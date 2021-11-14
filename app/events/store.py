from __future__ import annotations

from collections import defaultdict

import logging

from typing import Dict

from app.events.subscriptions import EventSubscription

logger = logging.getLogger(__name__)


class SubscriptionsStore:
    __store: Dict[int, Dict[str, EventSubscription]]
    __stored_indices: Dict[str, int]  # {subscription.id: event.type}

    def __init__(self):
        self.__store = defaultdict(dict)
        self.__stored_indices = {}

    def add(self, subscription: EventSubscription) -> None:
        if subscription.id in self.__stored_indices:
            raise KeyError(f"Subscription <{subscription}> already exists.")

        self.__store[subscription.event_type][subscription.id] = subscription
        self.__stored_indices[subscription.id] = subscription.event_type

    def remove(self, subscription_id: str) -> bool:
        if subscription_id not in self.__stored_indices:
            return False

        event_type = self.__stored_indices[subscription_id]

        del self.__store[event_type][subscription_id]
        del self.__stored_indices[subscription_id]

        return True

    def __getitem__(self, event_type):
        return list(self.__store[event_type].values())
