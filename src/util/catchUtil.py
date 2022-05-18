

import logging


def catch_error(func):
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception as e:
            logging.exception(e)

    return wrapper