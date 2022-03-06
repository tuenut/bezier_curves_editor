import json
import pygame

from typing import List, Tuple

from app.events import EventManager
from app.events.subscriptions import LMB, RMB
from bezier import BezierCurve, BezierCurvesBunch
from render import AppRender
from utils.types import ABCBaseApp


class BaseApp(ABCBaseApp):
    _curves: List[BezierCurvesBunch]

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
    def curves(self) -> List[BezierCurvesBunch]:
        if self._temp_curve:
            return [*self._curves, self._temp_curve]
        else:
            return [*self._curves]


class CurveCreatingMixin(BaseApp):
    def _add_curve(self, event: pygame.event.Event):
        """Command to eneter in 'Create curve mode'."""

        self.state["mode"] = self.MODE_CURVE_CREATING

        self.events.unsubscribe(self._mouse_LMB_event_id)
        self._mouse_LMB_event_id = self.events.subscribe(
            on_mouse_button=LMB,
            callback=self._add_point_to_temp_curve
        )
        self.events.unsubscribe(self._esc_event_id)
        self._esc_event_id = self.events.subscribe(
            on_key_down=pygame.K_ESCAPE,
            callback=self._interrupt_adding_curve,
        )

        self._temp_curve = BezierCurvesBunch()

    def _interrupt_adding_curve(self, event: pygame.event.Event):
        """Interrupt 'Create curve mode' and delete not finished curve."""

        del self._temp_curve
        self._temp_curve = None

        self._set_escape_default()
        self._set_mouse_default()

        self.state["mode"] = self.MODE_NORMAL

    def _add_point_to_temp_curve(self, event: pygame.event.Event):
        mouse_position = event.pos

        self._temp_curve.add_vertex(pygame.Vector2(mouse_position))

        if len(self._temp_curve.vertices) % 4 == 0 and not self._enter_event_id:
            self.state["mode"] = self.MODE_CURVE_COMPLETION

            self._enter_event_id = self.events.subscribe(
                on_key_down=pygame.K_RETURN,
                callback=self._complete_curve
            )

    def _complete_curve(self, event: pygame.event.Event):
        self._curves.append(self._temp_curve)
        self._temp_curve = None

        self._set_escape_default()
        self._set_mouse_default()

        self.events.unsubscribe(self._enter_event_id)
        self._enter_event_id = None

        self.state["mode"] = self.MODE_NORMAL


class CurveManipulatingMixin(BaseApp):
    def _select_point(self, event: pygame.event.Event):
        pos = pygame.Vector2(event.pos)

        for curve_bunch in self.curves:
            for point in curve_bunch.vertices:
                if abs(point.x - pos.x) < 5 and abs(point.y - pos.y) < 5:
                    self.state["selected_point"] = curve_bunch.select_point(point)
                    self.state["selected_curve"] = curve_bunch

                    self._set_events_for_moving_point()
                    return

    def _set_events_for_moving_point(self):
        self.events.unsubscribe(self._mouse_LMB_event_id)
        self._mouse_LMB_event_id = self.events.subscribe(
            on_mouse_button=LMB,
            callback=self._save_point_position,
        )
        self.events.unsubscribe(self._mouse_RMB_event_id)
        self._mouse_RMB_event_id = self.events.subscribe(
            on_mouse_button=RMB,
            callback=self._cancel_point_selection
        )
        self.events.unsubscribe(self._esc_event_id)
        self._esc_event_id = self.events.subscribe(
            on_key_down=pygame.K_ESCAPE,
            callback=self._cancel_point_selection
        )

    def _save_point_position(self, event: pygame.event.Event):
        self.state["selected_curve"].save_point_position()
        self.state["selected_curve"] = None
        self.state["selected_point"] = None

        self._set_mouse_default()
        self._set_escape_default()

    def _cancel_point_selection(self, event: pygame.event.Event):
        self.state["selected_curve"].cancel_point_selection()
        self.state["selected_curve"] = None
        self.state["selected_point"] = None

        self._set_mouse_default()
        self._set_escape_default()

    def _add_point_to_curve(self):
        raise NotImplementedError


class DataManagement(BaseApp):
    @property
    def data(self):
        data = {"curves": []}

        for curve in self._curves:
            curve_data = {
                "vertices": [(v.x, v.y) for v in curve.vertices]
            }
            data["curves"].append(curve_data)

        return data

    def save(self, event: pygame.event.Event):
        with open("trek.json", "w") as file:
            json.dump(self.data, file, indent=4)

    def open(self, event: pygame.event.Event):
        with open("trek.json", "r") as file:
            data = json.load(file)

        for curve in data["curves"]:
            raise NotImplementedError("Should be rewritten for BezierCurvesBunch")
            self._curves.append(BezierCurve(curve["vertices"]))


class App(CurveCreatingMixin, CurveManipulatingMixin, DataManagement):
    FPS = 100

    def __init__(self):
        self.events: EventManager = EventManager()
        self._curves = []

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

    def _exit(self, event: pygame.event.Event):
        self.state["running"] = False

    def __subscribe_events(self):
        self._set_escape_default()
        self._set_mouse_default()

        self.events.subscribe(
            on_event=pygame.QUIT,
            callback=self._exit
        )
        self.events.subscribe(
            on_key_down=pygame.K_q,
            callback=self._exit,
        )

        self.events.subscribe(
            on_key_down=pygame.K_a,
            callback=self._add_curve
        )
        self.events.subscribe(
            on_key_down=pygame.K_s,
            callback=self.save
        )
        self.events.subscribe(
            on_key_down=pygame.K_o,
            callback=self.open
        )

    def _set_mouse_default(self):
        self.events.unsubscribe(self._mouse_LMB_event_id)
        self._mouse_LMB_event_id = self.events.subscribe(
            on_mouse_button=LMB,
            callback=self._select_point,
        )

        self.events.unsubscribe(self._mouse_RMB_event_id)

    def _set_escape_default(self):
        self.events.unsubscribe(self._esc_event_id)
        self._esc_event_id = self.events.subscribe(
            on_key_down=pygame.K_ESCAPE,
            callback=self._exit,
        )

    def _do_nothing_callback(self, event: pygame.event.Event):
        pass