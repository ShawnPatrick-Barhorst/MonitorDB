import functools
import logging
import time

log = logging.getLogger(__name__)


def logged(fn):
    @functools.wraps(fn)
    def wrapper(conn, user_id, items):
        start = time.perf_counter()
        try:
            result = fn(conn, user_id, items)
        except Exception:
            log.exception("%s failed after %d items", fn.__name__, len(items))
            raise
        log.info(
            "%s: %d items in %.2fs -> %s",
            fn.__name__,
            len(items),
            time.perf_counter() - start,
            result,
        )
        return result

    return wrapper
