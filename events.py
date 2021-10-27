import logging
from typing import Optional, Dict

import pygame

from utils.decorators import as_singleton


@as_singleton
class EventManager:
    logger = logging.getLogger(__name__)
    logger.level = logging.INFO

    __subscriptions: Dict[int, Dict[int, dict]]

    def __init__(self):
        self.logger.debug("Init events manager.")

        self.__subscriptions = {}
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

            if self.check_conditions(event, conditions) \
                    and self.check_event_subtype(event, subtype):
                kwargs = self.__get_kwargs(event, subscription["kwargs"])
                if subscription["as_args"]:
                    callback(*kwargs.values())
                else:
                    callback(**kwargs)

    @classmethod
    def check_conditions(cls, event, conditions):
        if not conditions:
            return True

        try:
            return all([
                cls.check_condition(getattr(event, attr), value)
                for attr, value in conditions.items()
            ])
        except AttributeError:
            cls.logger.debug(
                f"Check event <{event}> conditions for <{conditions}> not"
                " successful."
            )
            return False

    @classmethod
    def check_condition(cls, event_value, expected_value):
        if isinstance(expected_value, (list, tuple)):
            return event_value in expected_value
        else:
            return event_value == expected_value

    @classmethod
    def check_event_subtype(cls, event, subtype):
        if subtype is None:
            return True

        try:
            return event.subtype == subtype
        except AttributeError:
            cls.logger.debug(
                f"Event <{event}> is has no subtype of <{subtype}>"
            )
            return False

    @classmethod
    def __get_kwargs(cls, event, kwargs):
        if kwargs is None:
            return {}

        try:
            return {arg_name: getattr(event, arg_name) for arg_name in kwargs}
        except AttributeError:
            cls.logger.exception(
                f"Try get kwargs <{kwargs}> for callback, but event <{event}>"
                f" has no some attrs."
            )
            raise

    @classmethod
    def dispatch(cls, event_type, **kwargs):
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
        self.logger.debug(
            f"Subscribe callback <{callback}> on event_type <{event_type}>."
        )
        self.logger.debug(f"Conditions <{conditions}>.")
        self.logger.debug(f"Kwargs <{kwargs}>.")
        self.logger.debug(f"Subtype <{subtype}>")

        subscription = {
            "callback": callback,
            "subtype": subtype,
            "conditions": conditions,
            "kwargs": kwargs,
            "as_args": as_args
        }

        index = id(callback)
        try:
            if index in self.__subscriptions[event_type]:
                raise Exception("Event already registered.")

            self.__subscriptions[event_type][index] = subscription
        except KeyError:
            self.__subscriptions[event_type] = {index: subscription, }

        subscription_id = f"{str(event_type)}.{index}"

        return subscription_id

    def unsubscribe(self, subscription_id: str):
        event_type, index = list(map(int, subscription_id.split(".")))
        del self.__subscriptions[event_type][index]
