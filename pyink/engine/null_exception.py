class NullException(Exception):
    pass


def throw_null_exception(name: str):
    raise NullException(f"{name} is null or undefined")
