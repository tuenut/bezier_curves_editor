import logging
from typing import Callable, Any, Union, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventSubscription:
    callback: Callable[[Any], None]
    event_type: int
    subtype: Union[int, None]
    conditions: Dict[str, Any]
    kwargs: List[str]
    as_args: bool

    def __init__(self,
                 callback: Callable,
                 event_type: int,
                 subtype: Optional[int] = None,
                 conditions: Optional[Dict[str, Any]] = None,
                 kwargs: Optional[List[str]] = None,
                 as_args: bool = False):
        logger.debug(
            f"Subscribe callback <{callback}> on event_type <{event_type}>."
        )
        logger.debug(f"Conditions <{conditions}>.")
        logger.debug(f"Kwargs <{kwargs}>.")
        logger.debug(f"Subtype <{subtype}>")

        index = id(callback)

        self.callback = callback
        self.event_type = event_type

        self.subtype = subtype
        self.conditions = conditions if conditions else {}
        self.kwargs = kwargs if kwargs else []
        self.as_args = as_args

        self.__id = f"{str(event_type)}.{index}"

    def __repr__(self):
        return f"EventSubscription(callback={self.callback}, " \
               f"event_type={self.event_type}, id={self.id})"

    @property
    def id(self):
        return self.__id

    def check_subtype(self, event):
        try:
            return event.subtype == self.subtype
        except AttributeError:
            logger.debug(f"Event <{event}> has no subtype of <{self.subtype}>")
            return False

    def check_conditions(self, event):
        if not self.conditions:
            return True

        try:
            return all([
                self.__check_condition(getattr(event, attr), value)
                for attr, value in self.conditions.items()
            ])
        except AttributeError:
            # May be fail try to check some non-existent event attribute.
            logger.debug(
                f"Check event <{event}> conditions for <{self.conditions}> not"
                " successful."
            )
            return False

    @staticmethod
    def __check_condition(event_value, expected_value):
        if isinstance(expected_value, (list, tuple)):
            return event_value in expected_value
        else:
            return event_value == expected_value
