# -*- coding: utf-8  -*-
from collections import OrderedDict

def dumps(obj, depth=0):
    if type(obj) is int or type(obj) is float:
        return '%g' % round(obj, 5)
    if type(obj) is str or type(obj) is unicode:
        return '\'%s\'' % obj.replace('\'', '\\\'')
    if type(obj) is bool:
        return 'true' if obj else 'false'
    if type(obj) is dict or type(obj) is OrderedDict:
        ind1 = '    ' * depth
        ind2 = '    ' * (depth+1)
        res = []
        for k, v in obj.items():
            try:
                k = k + 1
            except TypeError:
                pass
            res.append(u'[%s] = %s' % (dumps(k), dumps(v, depth+1)))
            
        return u'{\n%s%s\n%s}' % (ind2, (',\n' + ind2).join(res), ind1)
    if type(obj) is list:
        ind1 = '    ' * depth
        ind2 = '    ' * (depth+1)
        res = []
        for v in obj:
            res.append(u'%s' % (dumps(v, depth+1)))
            
        return u'{\n%s%s\n%s}' % (ind2, (',\n' + ind2).join(res), ind1)
    return 'nil'

if __name__ == '__main__':
    d = dumps({'array': [65, 23, 5], 'dict': {'mixed': {0: 43, 1: 54.33, 2: False, 4: None, 'string': 'value'}, 'array': [3, 6, 4], 'string': 'value'}})
    print(d)