import logging
from typing import Optional, Dict

import pygame

from app.events.subscription import EventSubscription, Subscriptions
from utils.decorators import as_singleton


@as_singleton
class EventManager:
    logger = logging.getLogger(__name__)
    logger.level = logging.INFO

    def __init__(self):
        self.logger.debug("Init events manager.")

        self.__subscriptions = Subscriptions()
        self.__events = []

    def check_events(self):
        self.logger.debug("Start handling pygame events.")

        self.__events = pygame.event.get()
        for event in self.__events:
            self.logger.debug(f"Handle <{event}>")
            self.on_event(event)

        self.logger.debug("Clear events.")
        self.__events = []

        self.logger.debug("End of handling pygame events.")

    def on_event(self, event):
        event_subscribtions = self.__subscriptions.get(event.type, {})

        for subscription in list(event_subscribtions.values()):
            callback = subscription["callback"]
            subtype = subscription["subtype"]
            conditions = subscription["conditions"]

            if self.__check_conditions(event, conditions) \
                    and self.__check_event_subtype(event, subtype):
                kwargs = self.__get_kwargs(event, subscription["kwargs"])
                if subscription["as_args"]:
                    callback(*kwargs.values())
                else:
                    callback(**kwargs)

    def __check_conditions(self, event, conditions):
        if not conditions:
            return True

        try:
            return all([
                self.__check_condition(getattr(event, attr), value)
                for attr, value in conditions.items()
            ])
        except AttributeError:
            self.logger.debug(
                f"Check event <{event}> conditions for <{conditions}> not"
                " successful."
            )
            return False

    def __check_condition(self, event_value, expected_value):
        if isinstance(expected_value, (list, tuple)):
            return event_value in expected_value
        else:
            return event_value == expected_value

    def __check_event_subtype(self, event, subtype):
        if subtype is None:
            return True

        try:
            return event.subtype == subtype
        except AttributeError:
            self.logger.debug(f"Event <{event}> has no subtype of <{subtype}>")
            return False

    def __get_kwargs(self, event, kwargs):
        if kwargs is None:
            return {}

        try:
            return {arg_name: getattr(event, arg_name) for arg_name in kwargs}
        except AttributeError:
            self.logger.exception(
                f"Try get kwargs <{kwargs}> for callback, but event <{event}>"
                f" has no some attrs."
            )
            raise

    @classmethod
    def dispatch(cls, event_type, **kwargs):
        """Looks like method to manual dispatch event."""
        cls.logger.debug(f"Dispatch <{event_type}> with kwargs <{kwargs}>.")

        event = pygame.event.Event(event_type, kwargs)
        pygame.event.post(event)

    def subscribe(
            self,
            event_type,
            callback,
            subtype: Optional[int] = None,
            conditions: Optional[dict] = None,
            kwargs: Optional[list] = None,
            as_args: bool = False
    ) -> str:
        subscription = EventSubscription(
            callback, event_type, subtype, conditions, kwargs, as_args
        )

        try:
            self.__subscriptions.add(subscription)
        except KeyError:
            self.__subscriptions[event_type] = [subscription, ]

        return subscription.id

    def unsubscribe(self, subscription_id: str):
        event_type, index = list(map(int, subscription_id.split(".")))
        del self.__subscriptions[event_type][index]
