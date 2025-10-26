def swap_quotes(input_str):
    # 使用占位符替换单引号
    temp_str = input_str.replace("'", "$PH")
    # 将双引号转换为单引号
    temp_str = temp_str.replace('"', "'")
    # 将占位符替换回双引号
    result_str = temp_str.replace("$PH", '"')
    return result_str

def add_escape_character(input_str):
    result_str = input_str.replace("{", "\\{").replace("}", "\\}")
    return result_str