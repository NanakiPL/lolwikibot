# -*- coding: utf-8  -*-

from numbers import Number
from decimal import Decimal, InvalidOperation

from pprint import pprint #debug

class Difference(Exception):
    types = {
        'changed': u'Changed  (%s -> %s)',
        'len': u'Number of items changed from %d to %d',
        'mismatch': u'Type mismatch - %s and %s',
    }
    
    def __init__(self, type, oldval, newval, path):
        self.type = type
        self.oldval = oldval
        self.newval = newval
        self.path = path
        try:
            self.str = Difference.types[type]
        except (KeyError, TypeError):
            raise ValueError(u'Invalid type')
        
        pass
    
    def __str__(self):
        o = repr(self.oldval)
        n = repr(self.newval)
        if len(o) > 50:
            o = o[:40] + u'...' + o[-7:]
        if len(n) > 50:
            n = n[:40] + u'...' + n[-7:]
        s = self.str % tuple(filter(None, [o, n]))
        if len(self.path):
            return u'%s: %s' % (u'.'.join(map(unicode, self.path)), s)
        return s
        
    def __repr__(self):
        o = repr(self.oldval)
        n = repr(self.newval)
        
        if len(o) > 70:
            o = o[:60] + u'...' + o[-7:]
        if len(n) > 70:
            n = n[:60] + u'...' + n[-7:]
        
        return u'Difference(' + u', '.join([repr(self.type), o, n, u'\'' + u'.'.join(map(unicode, self.path))]) + u'\')'

def _raise(e):
    try:
        compare.stack += [e]
    except AttributeError:
        raise e

def _compareBasic(a, b):
    try:
        return Decimal(unicode(a)) != Decimal(unicode(b))
    except InvalidOperation:
        return a != b
        
def _compareDicts(old, new, path, keymap = None):
    keys = set()
    keys.update(old.keys())
    keys.update(new.keys())
    
    try:
        keys.intersection_update(map(lambda x: x[0] if isinstance(x, tuple) else x, keymap))
        subkeys = dict(filter(lambda x: isinstance(x, tuple), keymap))
    except TypeError:
        pass
    
    for k in sorted(keys):
        if (k in old) != (k in new):
            if (k in new):
                _raise(Difference('changed', None, new[k], path + [k]))
            else:
                _raise(Difference('changed', old[k], None, path + [k]))
        else:
            try:
                compare(old[k], new[k], path = path + [k], keymap = subkeys[k])
            except (UnboundLocalError, KeyError):
                compare(old[k], new[k], path = path + [k])
    
    return False

def _compareLists(old, new, path, keymap = None):
    if len(old) != len(new):
        _raise(Difference('len', len(old), len(new), path))
        basic = True
        for i in range(0, max(len(old), len(new))):
            if (i < len(old) and isinstance(old[i], (list, dict))) or (i < len(new) and isinstance(new[i], (list, dict))):
                basic = False
                break
        if basic:
            del compare.stack[-1:]
            _raise(Difference('changed', old, new, path))
        return True
    else:
        basic = True
        diff = 0
        for i in range(0, len(old)):
            if isinstance(old[i], (list, dict)) or isinstance(new[i], (list, dict)):
                basic = False
            diff += compare(old[i], new[i], path = path + [i], keymap = keymap)
        if diff and basic:
            del compare.stack[-diff:]
            _raise(Difference('changed', old, new, path))
        return diff
    return False
        
def compare(old, new, full = False, path = [], keymap = None):
    res = False
    if full: compare.stack = []
    if isinstance(old, (Number, basestring)) != isinstance(new, (Number, basestring)) or isinstance(old, list) != isinstance(new, list) or isinstance(old, dict) != isinstance(new, dict):
        _raise(Difference('mismatch', type(old), type(new), path))
        return True
    
    if isinstance(old, dict):
        res = res or _compareDicts(old, new, path, keymap = keymap)
    elif isinstance(old, list):
        res = res or _compareLists(old, new, path, keymap = keymap)
    else:
        if _compareBasic(old, new):
            res = True
            _raise(Difference('changed', old, new, path))
    
    if full:
        stack = compare.stack
        del compare.stack
        if len(stack):
            return stack
    return bool(res)
