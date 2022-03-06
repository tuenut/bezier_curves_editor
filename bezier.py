"""
The code from [[here | https://www.drdobbs.com/forward-difference-calculation-of-bezier/184403417?pgno=5]]
 is taken as a basis for working with bezier curves
"""

import pygame

from typing import Union, List, Tuple
from loguru import logger

from utils.types import ABCBezierCurve, ABCBezierCurvesBunch


class BezierCurvesBunch(ABCBezierCurvesBunch):
    """List abstraction of bunch of curves.

    To draw a few sequence curves, where the last point previous curve should
     be the first point of next curve. That class manages that.
    """

    def __init__(self):
        self.curves = [BezierCurve(), ]
        self.vertices = []

        logger.debug(f"Create new curves bunch <{self}>")

    def add_vertex(self, vector: Union[pygame.Vector2, Tuple[float, float]]):
        if len(self.vertices) == 0 or (len(self.vertices) - 4) % 3 != 0:
            curve = self.curves[-1]
        else:
            logger.debug(f"Add new curve in <{self}>.")

            curve = BezierCurve()
            self.curves.append(curve)

            previous_curve = self.curves[-2]

            curve.add_vertex(previous_curve.vertices[-1])

        curve.add_vertex(vector)
        self.vertices.append(vector)

    def cancel_point_selection(self):
        self.vertices = []

        for curve in self.curves:
            if self.__selected_point in curve.vertices:
                curve.cancel_point_selection()
            for vertex in curve.vertices:
                if vertex not in self.vertices:
                    self.vertices.append(vertex)

    def select_point(self, point) -> pygame.Vector2:
        index = self.vertices.index(point)
        self.__old_point_position = self.vertices[index]
        self.vertices[index] = pygame.Vector2(point)
        self.__selected_point = self.vertices[index]

        return self.vertices[index]

    def save_point_position(self):
        index = self.vertices.index(self.__selected_point)
        self.vertices[index] = pygame.Vector2(self.__selected_point)

        self.__selected_point = None
        self.__old_point_position = None

    def update(self):
        for curve in self.curves:
            curve.update()

    def __repr__(self):
        return f"<{self.__class__.__name__}> with {len(self.vertices)}"


class BezierCurve(ABCBezierCurve):
    __curve_resolution: int
    __step_size: float
    __old_point_position: Union[pygame.Vector2, None] = None
    __selected_point: Union[pygame.Vector2, None] = None

    def __init__(self, vertices: list = None, curve_resolution: int = 30):
        self.vertices = [pygame.Vector2(v) for v in vertices] if vertices else []
        self.points: List[pygame.Vector2] = []

        self._set_resolution(curve_resolution)

        self.__changed = True

        self.update()

    def update(self):
        if len(self.vertices) != 4:
            return

        if self.__changed:
            self.__recalculate()
            self.__changed = False
        elif self.__old_point_position:
            self.__selected_point.x, self.__selected_point.y = pygame.mouse.get_pos()
            self.__recalculate()

    def add_vertex(self, vertex: Union[pygame.Vector2, Tuple[float, float]]):
        if len(self.vertices) < 4:
            self.vertices.append(vertex)
            self.__changed = True

    def cancel_point_selection(self):
        index = self.vertices.index(self.__selected_point)
        self.vertices[index] = pygame.Vector2(self.__old_point_position)

        self.__selected_point = None
        self.__old_point_position = None

        self.__changed = True

    def __recalculate(self):
        self.points = []

        point, first_FD, second_FD, third_FD = self.__get_forward_differences()

        # Compute points at each step
        self.points.append(pygame.Vector2(point.x, point.y))

        for i in range(self.__curve_resolution):
            point.x += first_FD.x
            point.y += first_FD.y

            first_FD.x += second_FD.x
            first_FD.y += second_FD.y

            second_FD.x += third_FD.x
            second_FD.y += third_FD.y

            self.points.append(pygame.Vector2(point))

    def __get_polynomial_coefs(self):
        # Compute polynomial coefficients from Bezier points
        ax = -self.vertices[0].x + 3 * self.vertices[1].x + -3 * self.vertices[2].x + self.vertices[3].x
        ay = -self.vertices[0].y + 3 * self.vertices[1].y + -3 * self.vertices[2].y + self.vertices[3].y

        bx = 3 * self.vertices[0].x + -6 * self.vertices[1].x + 3 * self.vertices[2].x
        by = 3 * self.vertices[0].y + -6 * self.vertices[1].y + 3 * self.vertices[2].y

        cx = -3 * self.vertices[0].x + 3 * self.vertices[1].x
        cy = -3 * self.vertices[0].y + 3 * self.vertices[1].y

        dx = self.vertices[0].x
        dy = self.vertices[0].y

        return pygame.Vector2(ax, ay), pygame.Vector2(bx, by), \
               pygame.Vector2(cx, cy), pygame.Vector2(dx, dy)

    def __get_forward_differences(self):
        a, b, c, d = self.__get_polynomial_coefs()

        # Compute forward differences from Bezier points and "h"
        pointX = d.x
        pointY = d.y

        firstFDX = a.x * (self._step_size ** 3) + b.x * (self._step_size ** 2) + c.x * self._step_size
        firstFDY = a.y * (self._step_size ** 3) + b.y * (self._step_size ** 2) + c.y * self._step_size

        secondFDX = 6 * a.x * (self._step_size ** 3) + 2 * b.x * (self._step_size ** 2)
        secondFDY = 6 * a.y * (self._step_size ** 3) + 2 * b.y * (self._step_size ** 2)

        thirdFDX = 6 * a.x * (self._step_size ** 3)
        thirdFDY = 6 * a.y * (self._step_size ** 3)

        return pygame.Vector2(pointX, pointY), pygame.Vector2(firstFDX, firstFDY), \
               pygame.Vector2(secondFDX, secondFDY), pygame.Vector2(thirdFDX, thirdFDY)

    @property
    def _step_size(self):
        return self.__step_size

    def _set_resolution(self, value):
        self.__curve_resolution = value
        self.__step_size = 1.0 / self.__curve_resolution

        self.__changed = True

    def __repr__(self):
        return f"<{self.__class__.__name__}> {str(self.vertices)} at <{id(self)}>"
