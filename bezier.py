"""
The code from [[here | https://www.drdobbs.com/forward-difference-calculation-of-bezier/184403417?pgno=5]]
 is taken as a basis for working with bezier curves
"""

from typing import Union, List, Tuple

import pygame

from utils.types import ABCBezierCurve


class BezierCurve(ABCBezierCurve):
    __curve_resolution: int
    __step_size: float
    __old_point_position: Union[pygame.Vector2, None] = None
    __selected_point: Union[pygame.Vector2, None] = None

    def __init__(self, vertices: list = None, curve_resolution: int = 30):
        self.vertices = vertices if vertices else []
        self.vectors: List[pygame.Vector2] = []

        self.set_resolution(curve_resolution)

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

    def add_vertex(self, vector: Union[pygame.Vector2, Tuple[float, float]]):
        if len(self.vertices) < 4:
            self.vertices.append(vector)
            self.__changed = True

    def __recalculate(self):
        self.vectors = []

        point, first_FD, second_FD, third_FD = self.__get_forward_differences()

        # Compute points at each step
        self.vectors.append(pygame.Vector2(point.x, point.y))

        for i in range(self.__curve_resolution):
            point.x += first_FD.x
            point.y += first_FD.y

            first_FD.x += second_FD.x
            first_FD.y += second_FD.y

            second_FD.x += third_FD.x
            second_FD.y += third_FD.y

            self.vectors.append(pygame.Vector2(point))

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

        firstFDX = a.x * (self.step_size ** 3) + b.x * (self.step_size ** 2) + c.x * self.step_size
        firstFDY = a.y * (self.step_size ** 3) + b.y * (self.step_size ** 2) + c.y * self.step_size

        secondFDX = 6 * a.x * (self.step_size ** 3) + 2 * b.x * (self.step_size ** 2)
        secondFDY = 6 * a.y * (self.step_size ** 3) + 2 * b.y * (self.step_size ** 2)

        thirdFDX = 6 * a.x * (self.step_size ** 3)
        thirdFDY = 6 * a.y * (self.step_size ** 3)

        return pygame.Vector2(pointX, pointY), pygame.Vector2(firstFDX, firstFDY), \
               pygame.Vector2(secondFDX, secondFDY), pygame.Vector2(thirdFDX, thirdFDY)

    @property
    def step_size(self):
        return self.__step_size

    def set_resolution(self, value):
        self.__curve_resolution = value
        self.__step_size = 1.0 / self.__curve_resolution

        self.__changed = True

    def select_point(self, point):
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

    def cancel_point_selection(self):
        index = self.vertices.index(self.__selected_point)
        self.vertices[index] = pygame.Vector2(self.__old_point_position)

        self.__selected_point = None
        self.__old_point_position = None

        self.__changed = True
