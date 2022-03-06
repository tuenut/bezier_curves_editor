import pygame

from typing import List

from utils.types import AppStateType, ABCBezierCurve, ABCBezierCurvesBunch


gray = pygame.Color(100, 100, 100)
lightgray = pygame.Color(200, 200, 200)
red = pygame.Color(255, 0, 0)
green = pygame.Color(0, 255, 0)
blue = pygame.Color(0, 0, 255)


class AppRender:
    def __init__(self, state: AppStateType):
        self.screen = pygame.display.set_mode((1024, 768))
        self.font = pygame.font.SysFont('mono', 12, bold=True)
        self.app_state = state

    def update(self, curves_bunch: List[ABCBezierCurvesBunch], text):
        ### Draw stuff
        self.screen.fill(gray)

        ### Highlight selected point
        if self.app_state["selected_point"] is not None:
            selected = self.app_state["selected_point"]
            pygame.draw.circle(self.screen, green, (selected.x, selected.y), 10)

        for bunch in curves_bunch:
            self._draw(bunch)

        self.screen.blit(
            self.font.render(self.app_state["mode"], True, (255, 255, 255)),
            pygame.Vector2(10, 10)
        )

        self.screen.blit(
            self.font.render(str(self.app_state["selected_point"]), True, (255, 255, 255)),
            pygame.Vector2(10, 30)
        )
        if text:
            self.screen.blit(
                self.font.render(text, True, (255, 255, 255)),
                pygame.Vector2(10, 60)
            )

        ### Flip screen
        pygame.display.flip()

    def _draw(self, curve_bunch: ABCBezierCurvesBunch):
        for curve in curve_bunch.curves:
            self._draw_curve(curve)

    def _draw_curve(self, curve: ABCBezierCurve):
        ### Draw control points
        for p in curve.vertices:
            pygame.draw.circle(self.screen, blue, (int(p.x), int(p.y)), 4)

        if len(curve.vertices) == 4 and curve.points:
            ### Draw control "lines"
            pygame.draw.lines(self.screen, lightgray, False, curve.vertices)
            ### Draw bezier curve
            pygame.draw.lines(self.screen, red, False, curve.points, 2)
