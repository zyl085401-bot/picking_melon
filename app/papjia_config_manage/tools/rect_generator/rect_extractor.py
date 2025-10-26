import cv2
import numpy as np
import json
import yaml


class RectExtractor:
    def __init__(self, json_path, image_path, rows, cols, row2col=False, pre_name=""):
        self.image_path = image_path
        self.rows = rows
        self.cols = cols
        self.row2col = row2col
        self.pre_name = pre_name
        self.rectangles = []
        self.image = cv2.imread(image_path)
        self.clone = self.image.copy()
        self.drawing = False
        self.current_rect = []
        self.json_path = json_path
        self.json_rects = self.load_json_rects()
        self.rects_with_name = {}

    def load_json_rects(self):
        with open(self.json_path, "r") as file:
            data = json.load(file)
        return [obj["bbox"] for obj in data["objects"]]

    def draw_rectangle(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.current_rect = [(x, y)]

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                img_copy = self.clone.copy()
                cv2.rectangle(img_copy, self.current_rect[0], (x, y), (0, 255, 0), 2)
                cv2.imshow("image", img_copy)

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.current_rect.append((x, y))
            x1, y1 = self.current_rect[0]
            x2, y2 = self.current_rect[1]
            self.rectangles.append([x1, y1, x2, y2])
            cv2.rectangle(self.clone, self.current_rect[0], self.current_rect[1], (0, 255, 0), 2)
            cv2.imshow("image", self.clone)

    def is_overlapping(self, rect1, rect2):
        x1, y1, x2, y2 = rect1
        x3, y3, x4, y4 = rect2
        return not (x1 > x4 or x3 > x2 or y1 > y4 or y3 > y2)

    def get_overlapping_rects(self):
        overlapping_rects = []
        for drawn_rect in self.rectangles:
            draw_rect_area = (drawn_rect[2] - drawn_rect[0]) * (drawn_rect[3] - drawn_rect[1])
            for json_rect in self.json_rects:
                if self.is_overlapping(json_rect, drawn_rect):
                    overlap_area = self.calculate_overlap_area(json_rect, drawn_rect)
                    if overlap_area / draw_rect_area > 0.5:
                        overlapping_rects.append(json_rect)
                        break
        return overlapping_rects

    def calculate_overlap_area(self, rect1, rect2):
        x1 = max(rect1[0], rect2[0])
        y1 = max(rect1[1], rect2[1])
        x2 = min(rect1[2], rect2[2])
        y2 = min(rect1[3], rect2[3])
        if x1 < x2 and y1 < y2:
            return (x2 - x1) * (y2 - y1)
        return 0

    def divide_image(self):
        overlapping_rects = self.get_overlapping_rects()
        if len(overlapping_rects) != 4:
            raise ValueError("Exactly 4 overlapping rectangles must be found.")

        # Assuming the centers are in order: top-left, top-right, bottom-right, bottom-left
        centers = [[(rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2] for rect in overlapping_rects]
        top_left, top_right, bottom_right, bottom_left = centers

        # Calculate the step sizes
        if self.row2col:
            step_y = (top_right[1] - top_left[1]) // (self.rows - 1)
            step_x = (bottom_left[0] - top_left[0]) // (self.cols - 1)
        else:
            step_x = (top_right[0] - top_left[0]) // (self.cols - 1)
            step_y = (bottom_left[1] - top_left[1]) // (self.rows - 1)

        points = []
        for i in range(self.rows):
            for j in range(self.cols):
                point_x = top_left[0] + j * step_x
                point_y = top_left[1] + i * step_y
                points.append((int(point_x), int(point_y)))

        return points

    def display_divided_points(self, points):
        for i, point in enumerate(points):
            row = int(i / self.cols) + 1
            col = int(i % self.cols) + 1
            if self.row2col:
                tmp = row
                row = col
                col = tmp
            name = f"{self.pre_name}_{row}_{col}"
            for rect in self.json_rects:
                if rect[0] <= point[0] <= rect[2] and rect[1] <= point[1] <= rect[3]:
                    center_x = int((rect[0] + rect[2]) // 2)
                    center_y = int((rect[1] + rect[3]) // 2)
                    print(f"{rect} -> {name}")
                    cv2.rectangle(
                        self.clone, (int(rect[0]), int(rect[1])), (int(rect[2]), int(rect[3])), (255, 0, 0), 2
                    )
                    cv2.circle(self.clone, (center_x, center_y), 5, (0, 0, 255), -1)
                    cv2.putText(
                        self.clone,
                        name,
                        (center_x, center_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 0, 0),
                        1,
                        cv2.LINE_AA,
                    )
                    self.rects_with_name[name] = rect
        cv2.imshow("Divided Points", self.clone)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def export_to_yaml(self, yaml_path):
        data = {
            "rect": [list(map(float, rect)) for rect in self.rects_with_name.values()],
            "target": [
                {
                    "name": name,
                    "status": "有_未使用",
                    "category": self.pre_name
                }
                for name in self.rects_with_name.keys()
            ]
        }
        with open(yaml_path, "w") as file:
            yaml.dump(data, file, allow_unicode=True)

    def run(self):
        cv2.namedWindow("image")
        cv2.setMouseCallback("image", self.draw_rectangle)
        while True:
            cv2.imshow("image", self.clone)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
        cv2.destroyAllWindows()
        return self.divide_image()


if __name__ == "__main__":
    json_path = "/home/yw/workspace/tmp/rect_images/rect_test_tube_001.json"
    image_path = "/home/yw/workspace/tmp/rect_images/rect_test_tube_001.jpg"  # Replace with your image path
    yaml_path = "/home/yw/workspace/tmp/rect_images/rect_test_tube_001.yaml"
    rows = 5  # Replace with the number of rows you want
    cols = 4  # Replace with the number of columns you want
    extractor = RectExtractor(json_path, image_path, rows, cols, row2col=True, pre_name="testtube")
    points = extractor.run()
    extractor.display_divided_points(points=points)
    extractor.export_to_yaml(yaml_path=yaml_path)
