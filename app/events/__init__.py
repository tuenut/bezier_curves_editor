import logging
import pygame

from typing import Callable, Optional, List

from app.events.store import SubscriptionsStore
from app.events.subscriptions import EventSubscription
from utils.decorators import as_singleton


logger = logging.getLogger(__name__)


@as_singleton
class EventManager:
    def __init__(self):
        logger.debug("Init events manager.")

        self.__store = SubscriptionsStore()
        self.__events = []

    def subscribe(
            self,
            callback: Callable,
            on_key_down: Optional[int] = None,
            on_mouse_button: Optional[int] = None,
            on_event: Optional[int] = None
    ) -> str:
        """Subscribe some callback to event

        :param on_key_down: Subscribe on key pressed on keyboard.
        :param on_mouse_button: Subscribe on mouse button click.
        :param on_event: Subscribe on specific event.
        :param callback: Callback method to handle event.
            Method interface should be:
             `callback(event: pygame.event.Event) -> None`
        :return: Subscription id. Can be used to unsubscribe.
        :rtype str
        """
        if on_key_down and on_mouse_button:
            raise Exception("Can't subscribe on two events simultaneously.")

        conditions = None

        if on_key_down:
            event_type = pygame.KEYDOWN
            conditions = {"key": on_key_down}
        elif on_mouse_button:
            event_type = pygame.MOUSEBUTTONDOWN
            conditions = {"button": on_mouse_button}
        elif on_event:
            event_type = on_event
        else:
            raise Exception("One of `on_key_down` or `on_mouse_button` should be passed. ")

        subscription = EventSubscription(
            callback=callback,
            event_type=event_type,
            conditions=conditions
        )
        self.__store.add(subscription)

        return subscription.id

    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe handler by `subscription_id`"""

        self.__store.remove(subscription_id)

    @classmethod
    def dispatch(cls, event_type, **kwargs):
        """Looks like method to manual dispatch event.

        TODO: looks like not enough useful method, may be should be removed.
        """

        logger.debug(
            f"Manual dispatching <{event_type}> with kwargs <{kwargs}>."
        )

        event = pygame.event.Event(event_type, kwargs)
        pygame.event.post(event)

    def handle_events(self):
        """Used to check and handle events in mainloop."""

        logger.debug("Start handling pygame events.")

        self.__events = pygame.event.get()
        for event in self.__events:
            logger.debug(f"Handle <{event}>")
            self._handle_event(event)

        logger.debug("Clear events.")
        self.__events = []

        logger.debug("End of handling pygame events.")

    def _handle_event(self, event):
        for subscription in self.__store[event.type]:
            if subscription.subtype and not subscription.check_subtype(event):
                continue

            if not subscription.check_conditions(event):
                continue

            subscription.callback(event)
