#!/bin/bash

# 智能克隆脚本工作流程：
# 1. 读取 repos_config.json 配置文件
# 2. 按分组处理仓库：
#    - 检查仓库是否已克隆
#    - 检查分支是否正确，如不正确则自动切换
#    - 检查远程更新，有更新则自动 pull
#    - 检查本地修改状态
# 3. 显示每个仓库的状态：
#    ✗ 未克隆：仓库尚未克隆
#    ⚠ 分支不符：当前分支与配置不一致
#    ✓ 已切换到正确分支：分支切换成功
#    ✗ 切换分支失败：无法切换到目标分支
#    正在更新...：检测到远程更新，正在拉取
#    ✓ 更新成功：远程更新拉取成功
#    ✗ 更新失败：远程更新拉取失败
#    ⚠ 本地修改：存在未提交的改动
#    ✓ 已同步：仓库状态完全同步
# 4. 最后生成统计报告，显示成功/失败数量

export TERM=xterm-256color
tput init

# 初始化配置
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
current_dir="$(dirname "$script_dir")"
config_file="${script_dir}/repos_config.json"
SECONDS=0 # 计时器

# 初始化统计数组
declare -A stats=(
    [groups]=0
    [total]=0
    [success]=0
    [failed]=0
)

declare -A group_repos_count=()
declare -A group_success=()
declare -A group_failed=()

# 颜色定义
COLOR_RESET="\033[0m"
COLOR_BLUE="\033[34m"
COLOR_GREEN="\033[32m"
COLOR_RED="\033[31m"
COLOR_CYAN="\033[36m"
COLOR_YELLOW="\033[33m"
COLOR_PURPLE="\033[35m"

# 获取仓库状态
get_repo_status() {
    local group=$1
    local repo=$2
    local target_dir="${current_dir}/${group}/${repo}"
    local branch=$(jq -r ".${group}.${repo}.branch" $config_file)

    if [ ! -d "$target_dir" ]; then
        echo -e "${COLOR_RED}✗ 未克隆${COLOR_RESET}"
        return
    fi

    local current_branch=$(git -C "$target_dir" rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ "$current_branch" != "$branch" ]; then
        echo -e "${COLOR_YELLOW}⚠ 分支不符${COLOR_RESET}"
        # 尝试切换到正确的分支
        if git -C "$target_dir" checkout $branch 2>/dev/null; then
            echo -e "${COLOR_GREEN}✓ 已切换到 ${branch} 分支${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}✗ 切换分支失败${COLOR_RESET}"
            return
        fi
    fi

    # 检查远程更新
    git -C "$target_dir" fetch origin $branch >/dev/null 2>&1
    local local_commit=$(git -C "$target_dir" rev-parse HEAD 2>/dev/null)
    local remote_commit=$(git -C "$target_dir" rev-parse origin/$branch 2>/dev/null)
    
    if [ "$local_commit" != "$remote_commit" ]; then
        echo -e "${COLOR_YELLOW}正在更新...${COLOR_RESET}"
        if git -C "$target_dir" pull origin $branch >/dev/null 2>&1; then
            echo -e "${COLOR_GREEN}✓ 更新成功${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}✗ 更新失败${COLOR_RESET}"
            return
        fi
    fi

    if git -C "$target_dir" status --porcelain | grep -q "^ M"; then
        echo -e "${COLOR_YELLOW}⚠ 本地修改${COLOR_RESET}"
    else
        echo -e "${COLOR_GREEN}✓ 已同步${COLOR_RESET}"
    fi
}

# 克隆仓库函数
clone_repo() {
    local group=$1
    local repo=$2
    local branch=$3
    local url=$4
    local target_dir="${current_dir}/${group}/${repo}"
    
    ((stats[total]++))
    repo_branch="${repo}@${branch}"
    printf "[%02d] %-30s" ${stats[total]} "$repo_branch"
    
    # 检查目录是否存在
    if [ -d "$target_dir" ]; then
        status_output=$(get_repo_status $group $repo)
        printf " | 状态: %b\n" "$status_output"
        ((stats[success]++))
        ((group_success[$group]++))
        return 0
    fi

    # 显示克隆进度
    printf " | 克隆中 "
    for i in {1..3}; do
        echo -n "▶"
        sleep 0.1
    done

    # 执行克隆操作
    if git clone -b $branch --no-single-branch $url $target_dir; then
        echo -e "${COLOR_GREEN}✓${COLOR_RESET}"
        ((stats[success]++))
        ((group_success[$group]++))
    else
        echo -e "${COLOR_RED}✗${COLOR_RESET}"
        ((stats[failed]++))
        ((group_failed[$group]++))
    fi
}

# 处理分组
process_group() {
    local group=$1
    ((stats[groups]++))
    
    echo -e "\n${COLOR_PURPLE}» 处理分组: ${COLOR_CYAN}${group}${COLOR_RESET}"
    mkdir -p "${current_dir}/${group}"

    # 获取仓库列表
    local group_repos=($(jq -r ".${group} | keys_unsorted[]" $config_file))
    group_repos_count[$group]=${#group_repos[@]}
    group_success[$group]=0
    group_failed[$group]=0

    # 遍历仓库
    for repo in "${group_repos[@]}"; do
        local branch=$(jq -r ".${group}.${repo}.branch" $config_file)
        local url=$(jq -r ".${group}.${repo}.url" $config_file)
        clone_repo $group $repo $branch $url
    done
}

# 打印最终报告
print_summary() {
    echo -e "\n${COLOR_CYAN}智能克隆作业报告${COLOR_RESET}"
    echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
    
    # 分组详情
    for group in "${groups[@]}"; do
        echo -e "┃ ${COLOR_BLUE}${group}${COLOR_RESET}"
        echo "┃├────────────────────┬────────────┐"
        
        while read repo; do
            status=$(get_repo_status $group $repo)
            printf "┃│%-20s | %-12b |\n" " ${repo}" "$status"
        done < <(jq -r ".${group}|keys_unsorted[]" $config_file)
        
        echo "└┼────────────────────┴────────────┤"
    done
    
    # 统计信息
    echo -e "┏━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━┓"
    echo -e "┃ 总仓库: ${stats[total]} 成功: ${COLOR_GREEN}${stats[success]}${COLOR_RESET} 失败: ${COLOR_RED}${stats[failed]}${COLOR_RESET}"
    echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
    echo -e "耗时: ${SECONDS} 秒"
}

display_width() {
    local str=$1
    local clean_str=$(echo "$str" | sed -r "s/\x1B\[[0-9;]*[mK]//g")
    local width=$(echo "$clean_str" | awk '{len=0; for(i=1;i<=length($0);i++){c=substr($0,i,1); len+=c~/[\x00-\x7F]/?1:2} print len}')
    echo $width
}

# 打印工作流程说明
print_workflow() {
    echo -e "\n${COLOR_CYAN}智能克隆脚本工作流程${COLOR_RESET}"
    echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
    echo "┃ 1. 读取 repos_config.json 配置文件                  ┃"
    echo "┃ 2. 按分组处理仓库：                                ┃"
    echo "┃    - 检查仓库是否已克隆                           ┃"
    echo "┃    - 检查分支是否正确，如不正确则自动切换        ┃"
    echo "┃    - 检查远程更新，有更新则自动 pull             ┃"
    echo "┃    - 检查本地修改状态                            ┃"
    echo "┃ 3. 可能的状态说明：                               ┃"
    echo -e "┃    ${COLOR_RED}✗ 未克隆${COLOR_RESET} - 仓库尚未克隆                        ┃"
    echo -e "┃    ${COLOR_YELLOW}⚠ 分支不符${COLOR_RESET} - 当前分支与配置不一致            ┃"
    echo -e "┃    ${COLOR_GREEN}✓ 已切换到正确分支${COLOR_RESET} - 分支切换成功             ┃"
    echo -e "┃    ${COLOR_RED}✗ 切换分支失败${COLOR_RESET} - 无法切换到目标分支            ┃"
    echo -e "┃    ${COLOR_YELLOW}正在更新...${COLOR_RESET} - 检测到远程更新，正在拉取       ┃"
    echo -e "┃    ${COLOR_GREEN}✓ 更新成功${COLOR_RESET} - 远程更新拉取成功                 ┃"
    echo -e "┃    ${COLOR_RED}✗ 更新失败${COLOR_RESET} - 远程更新拉取失败                  ┃"
    echo -e "┃    ${COLOR_YELLOW}⚠ 本地修改${COLOR_RESET} - 存在未提交的改动                ┃"
    echo -e "┃    ${COLOR_GREEN}✓ 已同步${COLOR_RESET} - 仓库状态完全同步                   ┃"
    echo "┃ 4. 最后生成统计报告，显示成功/失败数量           ┃"
    echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
    echo
}

# 主流程
groups=($(jq -r 'keys_unsorted[]' $config_file))

print_workflow
echo "开始执行仓库克隆作业..."
for group in "${groups[@]}"; do
    process_group $group
done

print_summary

# 错误提示
if [ ${stats[failed]} -gt 0 ]; then
    echo -e "\n${COLOR_RED}警告: 存在克隆失败项${COLOR_RESET}"
fi
