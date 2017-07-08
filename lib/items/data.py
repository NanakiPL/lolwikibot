# -*- coding: utf-8 -*-

import json, re
from .. import api, SuperFloat, SuperFloats

from pprint import pprint

def getItems(version, locale = None):
    try:
        if getItems.v == version:
            return getItems.cache[locale or 'default']
    except (AttributeError, KeyError):
        pass
    
    try:
        return json.load(open('cache/items-%s-%s.json' % (str(version), locale or 'default')), parse_float = SuperFloat)
    except IOError:
        pass
    
    data = api.call('static_get_item_list', version = str(version), locale = locale, item_list_data = 'all')['data']
    if locale and re.match('^en', locale) == None:
        data_en = getItems(version)
        for key, item in data_en.items():
            if 'name' in item: data[key]['name_en'] = item['name']
            if 'plaintext' in item: data[key]['plaintext_en'] = item['plaintext']
            if 'description' in item: data[key]['description_en'] = item['description']
    
    for key, item in data.items():
        if item['id'] not in getItem.keys:
            getItem.keys[item['id']] = key
    
    data = SuperFloats(data)
    
    if not getItems.v or getItems.v < version:
        getItems.v = version
        getItems.cache = {}
    if getItems.v == version:
        getItems.cache[locale or 'default'] = data
        
    try:
        json.dump(data, open('cache/items-%s-%s.json' % (str(version), locale or 'default'), 'w'))
    except IOError:
        pass
    return data
getItems.v = None

def getItem(item, version, locale = None):
    data = getItems(version, locale)
    try:
        return data[item]
    except KeyError: pass
    try:
        return data[getItem.keys[item]]
    except KeyError: pass
    for k,d in data.items():
        if d['id'] == item:
            getItem.keys[d['id']] = k
            return d
    raise KeyError('No item \'%s\' in version %s' % (item, str(version)))
getItem.keys = {}

def itemUpdated(item, v1, v2, locale = None):
    if v1 == v2:
        return False
    elif v1 > v2:
        v1, v2 = v2, v1
    i1 = getItem(item, v1, locale)
    i2 = getItem(item, v2, locale)
    
    if ('name' in i1) != ('name' in i2): return 'name-xor'
    try:
        if i1['name'] != i2['name']: return 'name'
    except KeyError:
        pass
    for key in i2['stats'].keys():
        if i1['stats'][key] != i2['stats'][key]: return 'stats'
    return False