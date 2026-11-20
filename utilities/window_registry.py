import functools

_open = {}  # key -> Toplevel (or None while being built)


def single_instance(key):
    """Allow one live window per key; re-focus it instead of re-creating."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(parent=None, *a, **kw):
            if key in _open:
                w = _open[key]
                if w is not None and w.winfo_exists():
                    w.deiconify(); w.lift(); w.focus_force()
                return
            _open[key] = None
            try:
                return fn(parent, *a, **kw)
            finally:
                _open.pop(key, None)  # no dead refs after close
        return wrapper
    return deco


def track(key, window):
    _open[key] = window