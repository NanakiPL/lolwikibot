# -*- coding: utf-8  -*-
from collections import OrderedDict

def dumps(obj, depth=0):
    if type(obj) is int or type(obj) is float:
        return '%g' % round(obj, 5)
    if type(obj) is str or type(obj) is unicode:
        return '\'%s\'' % obj.replace('\'', '\\\'')
    if type(obj) is bool:
        return 'true' if obj else 'false'
    if type(obj) is dict:
        obj = OrderedDict(sorted(obj.items()))
    if type(obj) is OrderedDict:
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
    
def ordered_dumps(obj, order):
    ord = []
    
    for a in order:
        try:
            ord.append((a, obj[a]))
        except KeyError:
            pass
    
    for a in sorted([x for x in obj.keys() if x not in order]):
        try:
            ord.append((a, obj[a]))
        except KeyError:
            pass
    
    return dumps(OrderedDict(ord))
    
def decomment(text):
    from re import sub, M
    text = sub('(?<!\-)--\[\[.*?\]\]', '', text, flags=M) # remove comment blocks
    text = sub('^\s*--.*?(\n|$)', '', text, flags=M) # remove comments
    return text
    
def commentify(text):
    import re
    # DPL-like escapes for double brackets
    text = text.replace(u'²[', u'[[')
    text = text.replace(u']²', u']]')
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if not re.match('\s*--', line) and not re.match('\s*$', line):
            lines[i] = '-- %s' % line
    return '\n'.join(lines).strip()