"""Monkey-patch chumpy + numpy for Python 3.11+ / numpy 1.24+ compatibility.

1. inspect.getargspec() removed in Python 3.11 — alias to getfullargspec
2. numpy.bool/int/float/complex/object/str removed in numpy 1.24 — add back as builtin aliases
3. 'unicode' doesn't exist in Python 3 — alias to str
"""
import inspect
import numpy as np

# Fix 1: inspect.getargspec → getfullargspec
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

# Fix 2: Restore removed numpy aliases for chumpy
_aliases = {
    'bool': bool,
    'int': int,
    'float': float,
    'complex': complex,
    'object': object,
    'str': str,
    'unicode': str,  # Python 3 has no 'unicode' type, alias to str
}
for name, val in _aliases.items():
    if not hasattr(np, name):
        setattr(np, name, val)
