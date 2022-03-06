from __future__ import annotations

import pygame

from typing import TypedDict, Union, Tuple, List, Optional, Callable

from abc import ABC, abstractmethod


class ABCBezierCurve(ABC):
    __curve_resolution: int
    __step_size: float
    __old_point_position: Union[pygame.Vector2, None] = None
    __selected_point: Union[pygame.Vector2, None] = None

    vertices: List[pygame.Vector2]
    vectors: List[pygame.Vector2]

    @property
    @abstractmethod
    def step_size(self) -> float:
        ...

    @abstractmethod
    def update(self):
        ...

    @abstractmethod
    def add_vertex(self, vector: Union[pygame.Vector2, Tuple[float, float]]):
        ...

    @abstractmethod
    def set_resolution(self, value):
        ...

    @abstractmethod
    def select_point(self, point) -> pygame.Vector2:
        ...

    @abstractmethod
    def save_point_position(self):
        ...

    @abstractmethod
    def cancel_point_selection(self):
        ...


class AppStateType(TypedDict):
    running: Union[bool, None]
    selected_point: Union[Union[Tuple[float, float], pygame.Vector2], None]
    selected_curve: Union[ABCBezierCurve, None]
    mode: Union[str, None]


class ABCEvenManager(ABC):
    @abstractmethod
    def subscribe(
            self,
            callback: Callable,
            on_key_down: Optional[int] = None,
            on_mouse_button: Optional[int] = None,
            kwargs: Optional[list] = None,
            as_args: bool = False
    ) -> str:
        ...

    @abstractmethod
    def unsubscribe(self, subscription_id: str):
        ...

    @abstractmethod
    def check_events(self):
        ...


class ABCBaseApp(ABC):
    events: ABCEvenManager
    state: AppStateType

    @property
    @abstractmethod
    def curves(self) -> List[ABCBezierCurve]:
        ...
