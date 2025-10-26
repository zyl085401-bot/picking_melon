import json
import yaml


class GridPointGenerator:
    def __init__(self, config_file="/home/yw/workspace/papjia_config_manage/config/point_generate.yaml"):
        self.config_file = config_file
        self.pose_file = ""
        self.areas = {}
        self.vertices = {}
        self.all_poses = {}
        self.load_config(self.config_file)

    def load_config(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            self.pose_file = config.get("位姿文件", "")
            vertex_file = config.get("端点文件", "")
            with open(vertex_file, "r") as f:
                self.vertices = json.load(f)
            self.areas = config.get("区域", {})

    def generate_areas(self):
        for area_name, area_info in self.areas.items():
            rows = area_info.get("rows", 0)
            cols = area_info.get("cols", 0)
            keys = area_info.get("vertices", 0)
            vertex_poses = []
            frame_id = ""
            for key in keys:
                vertex = self.vertices
                for k in key:
                    vertex = vertex.get(k, {})
                pose = [float(coord) for coord in vertex["pose"]]
                vertex_poses.append(pose)
                frame_id = vertex["frame_id"]
            poses = self.generate_grid(rows, cols, vertex_poses)
            self.all_poses[area_name] = {}
            for i, pose in enumerate(poses):
                self.all_poses[area_name][f"{area_name}_{int(i / cols) + 1}_{int(i % cols) + 1}"] = {
                    "frame_id": frame_id,
                    "pose": pose,
                    "status": "无",
                }
        with open(self.pose_file, "w", encoding="utf-8") as f:
            json.dump(self.all_poses, f, ensure_ascii=False, indent=2)

    def generate_grid(self, rows: int, cols: int, points: list) -> list:
        """
        生成均匀分布的网格点
        :param rows: 行数（垂直方向分割数）
        :param cols: 列数（水平方向分割数）
        :param points: 四个顶点（顺时针）
        :return: 按行优先顺序排列的点列表
        """
        if len(points) != 4:
            raise ValueError("请先加载四个边界点")

        if rows < 1 or cols < 1:
            raise ValueError("行数和列数必须大于0")

        # 解包四个角点（顺时针顺序）
        top_left, top_right, bottom_right, bottom_left = points

        grid_points = []
        for row in range(rows):
            v = row / (rows - 1) if rows > 1 else 0

            # 计算左右边界点
            left = self._interpolate(top_left, bottom_left, v)
            right = self._interpolate(top_right, bottom_right, v)

            for col in range(cols):
                u = col / (cols - 1) if cols > 1 else 0
                # 水平插值
                point = self._interpolate(left, right, u)
                grid_points.append(point)

        self.grid = grid_points
        return grid_points

    def _interpolate(self, start: list, end: list, ratio: float) -> list:
        """线性插值函数"""
        return [start[i] + (end[i] - start[i]) * ratio for i in range(len(start))]


if __name__ == "__main__":
    # 使用示例
    generator = GridPointGenerator()
    generator.generate_areas()
    print("Finished")
