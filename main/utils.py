import functools


def profile(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        import datetime
        now = datetime.datetime.now
        start = now()
        try:
            res = func(*a, **kw)
            return res
        except:
            raise
        finally:
            diff = now() - start
            print('func {}.{} took {} secs {} μs'.format(str(a[0].__class__), func.__name__, diff.seconds,
                                                         diff.microseconds))

    return wrapper


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
