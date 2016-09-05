# -*- coding: utf-8  -*-
from collections import OrderedDict
import re

def dumps(obj, depth=0):
    if isinstance(obj, (int, float)):
        return '%g' % round(obj, 5)
    if isinstance(obj, basestring):
        return '\'%s\'' % obj.replace('\'', '\\\'')
    if isinstance(obj, bool):
        return 'true' if obj else 'false'
    if isinstance(obj, dict) and not isinstance(obj, OrderedDict):
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
    
def ordered_dumps(obj):
    res = []
    for i in range(len(obj)):
        line = ''
        if isinstance(obj[i], tuple):
            line += u'    [%s] = %s' % (dumps(obj[i][0]), dumps(obj[i][1], 1))
        else:
            line += u'    -- %s' % obj[i] or ''
        res.append(line)
            
    res = u'{\n%s\n}' % ((',\n').join(res))
    res = re.sub(ur'(^|\n)    -- ,(\n|$)', ur'\1\2', res)
    res = re.sub(ur'(-- .*?),(\n|$)', ur'\1\2', res)
    
    return res
    
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