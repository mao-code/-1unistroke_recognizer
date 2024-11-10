import math
from typing import List, Tuple
from templates import templates as raw_templates  # Renamed to avoid confusion

Point = Tuple[float, float]

class Recognizer:
    def __init__(self, templates: List[dict], num_samples: int = 64):
        self.num_samples = num_samples
        self.templates = []

        # process the templates
        for template in raw_templates:
            processed_points = self.process(template['points'])
            self.templates.append({
                'name': template['name'],
                'points': processed_points
            })
            # print(f"Template '{template['name']}' has {len(processed_points)} points after processing.")

    def recognize(self, points: List[Point]) -> Tuple[str, float, int]:
        processed = self.process(points)
        best_score = float('inf')
        best_template = None
        best_index = -1
        for index, template in enumerate(self.templates):
            d = self.path_distance(processed, template['points'])
            if d < best_score:
                best_score = d
                best_template = template['name']
                best_index = index
        # The score can be adjusted based on the maximum possible distance
        max_distance = 0.5 * math.sqrt(2 * (250 ** 2))  # Based on scale_to_square size
        score = 1 - (best_score / max_distance)
        return best_template, score, best_index

    def process(self, points: List[Point]) -> List[Point]:
        points = self.resample(points, self.num_samples)
        radians = self.indicative_angle(points)
        points = self.rotate_by(points, -radians)
        points = self.scale_to_square(points, 250)
        points = self.translate_to_origin(points)
        return points

    def resample(self, points: List[Point], n: int) -> List[Point]:
        I = self.path_length(points) / (n - 1)
        D = 0.0
        new_points = [points[0]]
        i = 1
        while i < len(points):
            d = self.distance(points[i - 1], points[i])
            if (D + d) >= I:
                t = (I - D) / d
                new_x = points[i - 1][0] + t * (points[i][0] - points[i - 1][0])
                new_y = points[i - 1][1] + t * (points[i][1] - points[i - 1][1])
                new_point = (new_x, new_y)
                new_points.append(new_point)
                points.insert(i, new_point)
                D = 0.0
            else:
                D += d
            i += 1
        if len(new_points) == n - 1:
            new_points.append(points[-1])
        return new_points

    def indicative_angle(self, points: List[Point]) -> float:
        c = self.centroid(points)
        return math.atan2(c[1] - points[0][1], c[0] - points[0][0])

    def rotate_by(self, points: List[Point], angle: float) -> List[Point]:
        c = self.centroid(points)
        cos = math.cos(angle)
        sin = math.sin(angle)
        new_points = []
        for p in points:
            qx = (p[0] - c[0]) * cos - (p[1] - c[1]) * sin + c[0]
            qy = (p[0] - c[0]) * sin + (p[1] - c[1]) * cos + c[1]
            new_points.append((qx, qy))
        return new_points

    def scale_to_square(self, points: List[Point], size: float) -> List[Point]:
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        width = max_x - min_x
        height = max_y - min_y
        # Prevent division by zero
        if width == 0:
            width = 1
        if height == 0:
            height = 1
        new_points = [((p[0] - min_x) * (size / width),
                       (p[1] - min_y) * (size / height)) for p in points]
        return new_points

    def translate_to_origin(self, points: List[Point]) -> List[Point]:
        c = self.centroid(points)
        new_points = [(p[0] - c[0], p[1] - c[1]) for p in points]
        return new_points

    def path_distance(self, a: List[Point], b: List[Point]) -> float:
        if len(a) != len(b):
            raise ValueError("Point lists must be of the same length")
        d = 0.0
        for p1, p2 in zip(a, b):
            d += self.distance(p1, p2)
        return d / len(a)

    def path_length(self, points: List[Point]) -> float:
        d = 0.0
        for i in range(1, len(points)):
            d += self.distance(points[i - 1], points[i])
        return d

    def centroid(self, points: List[Point]) -> Point:
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return (x, y)

    def distance(self, p1: Point, p2: Point) -> float:
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])
