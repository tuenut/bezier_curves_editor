from __future__ import annotations

import logging

from typing import Optional, Dict, List

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class Subscriptions:
    __store: Dict[int, Dict[str, EventSubscription]]
    __stored_indices: Dict[str, int]

    def __init__(self):
        self.__store = {}

    def add(self, subscription: EventSubscription):
        try:
            if subscription.id not in self.__store[subscription.event_type]:
                self.__store[subscription.event_type][subscription.id] = subscription
            else:
                raise
        except KeyError:
            self.__store[subscription.event_type] = {}


class EventSubscription:
    def __init__(self,
                 callback,
                 event_type,
                 subtype: Optional[int] = None,
                 conditions: Optional[dict] = None,
                 kwargs: Optional[list] = None,
                 as_args: bool = False):
        logger.debug(
            f"Subscribe callback <{callback}> on event_type <{event_type}>."
        )
        logger.debug(f"Conditions <{conditions}>.")
        logger.debug(f"Kwargs <{kwargs}>.")
        logger.debug(f"Subtype <{subtype}>")

        index = id(callback)

        self.event_type = event_type
        self.subtype = subtype
        self.callback = callback
        self.conditions = conditions if conditions else {}
        self.kwargs = kwargs if kwargs else []
        self.as_args = as_args

        self.__id = f"{str(event_type)}.{index}"

    @property
    def id(self):
        return self.__id
