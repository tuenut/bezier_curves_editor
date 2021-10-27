from functools import wraps


def as_singleton(cls):
    instance = None

    @wraps(cls)
    def wrapper(*args, **kwargs):
        nonlocal instance

        if instance is None:
            instance = cls(*args, **kwargs)

        return instance

    return wrapper