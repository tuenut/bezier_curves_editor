import json
from typing import List, Tuple

import pygame

from app.events import EventManager
from bezier import BezierCurve
from render import AppRender
from utils.types import ABCBaseApp


class BaseApp(ABCBaseApp):
    _curves: List[BezierCurve]

    _mouse_LMB_event_id = None
    _mouse_RMB_event_id = None
    _esc_event_id = None
    _enter_event_id = None
    _temp_curve = None

    MODE_CURVE_CREATING = "creating_curve"
    MODE_CURVE_COMPLETION = "curve_completion"

    MODE_NORMAL = "normal"

    MODE_TEXTS = {
        MODE_CURVE_COMPLETION: "Press ENTER to save curve",
        MODE_NORMAL: "Press A to add new curve, or LMB to select point for moving"
    }

    @property
    def curves(self) -> List[BezierCurve]:
        if self._temp_curve:
            return [*self._curves, self._temp_curve]
        else:
            return [*self._curves]


class CurveCreatingMixin(BaseApp):
    def _add_curve(self):
        self.state["mode"] = self.MODE_CURVE_CREATING

        self.events.unsubscribe(self._mouse_LMB_event_id)
        self._mouse_LMB_event_id = self.events.subscribe(
            event_type=pygame.MOUSEBUTTONDOWN,
            conditions={"button": 1},
            callback=self._add_point_to_temp_curve,
            kwargs=["pos"],
            as_args=True
        )
        self.events.unsubscribe(self._esc_event_id)
        self._esc_event_id = self.events.subscribe(
            event_type=pygame.KEYDOWN,
            conditions={"key": pygame.K_ESCAPE},
            callback=self._interrupt_adding_curve,
        )

        self._temp_curve = BezierCurve()

    def _interrupt_adding_curve(self):
        del self._temp_curve
        self._temp_curve = None

        self._set_escape_default()
        self._set_mouse_default()

        self.state["mode"] = self.MODE_NORMAL

    def _add_point_to_temp_curve(self, mouse_position: Tuple[float, float]):
        self._temp_curve.add_vertex(pygame.Vector2(mouse_position))

        if len(self._temp_curve.vertices) == 4 and not self._enter_event_id:
            self.state["mode"] = self.MODE_CURVE_COMPLETION

            self._enter_event_id = self.events.subscribe(
                event_type=pygame.KEYDOWN,
                conditions={"key": pygame.K_RETURN},
                callback=self._complete_curve
            )

    def _complete_curve(self):
        self._curves.append(self._temp_curve)
        self._temp_curve = None

        self._set_escape_default()
        self._set_mouse_default()

        self.events.unsubscribe(self._enter_event_id)
        self._enter_event_id = None

        self.state["mode"] = self.MODE_NORMAL


class CurveManipulatingMixin(BaseApp):
    def _select_point(self, pos):
        pos = pygame.Vector2(pos)

        for curve in self.curves:
            for point in curve.vertices:
                if abs(point.x - pos.x) < 5 and abs(point.y - pos.y) < 5:
                    self.state["selected_point"] = curve.select_point(point)
                    self.state["selected_curve"] = curve

                    self._set_events_for_moving_point()
                    return

    def _set_events_for_moving_point(self):
        self.events.unsubscribe(self._mouse_LMB_event_id)
        self._mouse_LMB_event_id = self.events.subscribe(
            event_type=pygame.MOUSEBUTTONDOWN,
            conditions={"button": 1},
            callback=self._save_point_position,
        )
        self.events.unsubscribe(self._mouse_RMB_event_id)
        self._mouse_RMB_event_id = self.events.subscribe(
            event_type=pygame.MOUSEBUTTONDOWN,
            conditions={"button": 3},
            callback=self._cancel_point_selection
        )
        self.events.unsubscribe(self._esc_event_id)
        self._esc_event_id = self.events.subscribe(
            event_type=pygame.KEYDOWN,
            conditions={"key": pygame.K_ESCAPE},
            callback=self._cancel_point_selection
        )

    def _save_point_position(self):
        self.state["selected_curve"].save_point_position()
        self.state["selected_curve"] = None
        self.state["selected_point"] = None

        self._set_mouse_default()

    def _cancel_point_selection(self):
        self.state["selected_curve"].cancel_point_selection()
        self.state["selected_curve"] = None
        self.state["selected_point"] = None

        self._set_mouse_default()

    def _add_point_to_curve(self):
        raise NotImplementedError


class DataManagement(BaseApp):
    @property
    def data(self):
        data = {"curves": []}

        for curve in self._curves:
            curve_data = {
                "points": [(v.x, v.y) for v in curve.vectors],
                "vertices": [(v.x, v.y) for v in curve.vertices]
            }
            data["curves"].append(curve_data)

        return data

    def save(self):
        with open("trek.json", "w") as file:
            json.dump(self.data, file, indent=4)

    def open(self):
        with open("trek.json", "r") as file:
            data = json.load(file)

        for curve in data["curves"]:
            self._curves.append(BezierCurve(curve["vertices"]))


class App(CurveCreatingMixin, CurveManipulatingMixin, DataManagement):
    FPS = 100

    def __init__(self):
        self.events: EventManager = EventManager()
        self._curves: List[BezierCurve] = []

        self.state = {
            "running": None,
            "selected_point": None,
            "selected_curve": None,
            "mode": None
        }

        pygame.init()
        self.clock = pygame.time.Clock()

        self.render = AppRender(self.state)

        self.__subscribe_events()

    @property
    def help_text(self):
        try:
            return self.MODE_TEXTS[self.state["mode"]]
        except KeyError:
            return ""

    def run(self):
        self.state["running"] = True
        self.state["mode"] = self.MODE_NORMAL

        while self.state["running"]:
            self.events.handle_events()
            self.__update_stuff()
            self.__render_stuff()
            self.clock.tick(self.FPS)

    def __update_stuff(self):
        for curve in self.curves:
            curve.update()

        if self._temp_curve:
            self._temp_curve.update()

    def __render_stuff(self):
        self.render.update(self.curves, self.help_text)

    def _exit(self):
        self.state["running"] = False

    def __subscribe_events(self):
        self._set_escape_default()
        self._set_mouse_default()

        self.events.subscribe(
            event_type=pygame.QUIT,
            callback=self._exit
        )
        self.events.subscribe(
            event_type=pygame.KEYDOWN,
            callback=self._exit,
            conditions={"key": pygame.K_q}
        )

        self.events.subscribe(
            event_type=pygame.KEYDOWN,
            conditions={"key": pygame.K_a},
            callback=self._add_curve
        )
        self.events.subscribe(
            event_type=pygame.KEYDOWN,
            conditions={"key": pygame.K_s},
            callback=self.save
        )
        self.events.subscribe(
            event_type=pygame.KEYDOWN,
            conditions={"key": pygame.K_o},
            callback=self.open
        )

    def _set_mouse_default(self):
        if self._mouse_LMB_event_id:
            self.events.unsubscribe(self._mouse_LMB_event_id)

        self._mouse_LMB_event_id = self.events.subscribe(
            event_type=pygame.MOUSEBUTTONDOWN,
            conditions={"button": 1},
            callback=self._select_point,
            kwargs=["pos"],
            as_args=True
        )

        if self._mouse_RMB_event_id:
            self.events.unsubscribe(self._mouse_RMB_event_id)

        self._mouse_RMB_event_id = self.events.subscribe(
            event_type=pygame.MOUSEBUTTONDOWN,
            conditions={"button": 3},
            callback=self._do_nothing_callback,
        )

    def _set_escape_default(self):
        if self._esc_event_id:
            self.events.unsubscribe(self._esc_event_id)

        self._esc_event_id = self.events.subscribe(
            event_type=pygame.KEYDOWN,
            callback=self._exit,
            conditions={"key": pygame.K_ESCAPE}
        )

    def _do_nothing_callback(self):
        pass