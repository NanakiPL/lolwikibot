# -*- coding: utf-8 -*-

import json, re
from .. import api

from pprint import pprint

def getChampions(version, locale = None):
    try:
        if getChampions.v == version:
            return getChampions.cache[locale or 'default']
    except (AttributeError, KeyError):
        pass
    
    try:
        return json.load(open('cache/champions-%s-%s.json' % (str(version), locale or 'default')))
    except IOError:
        pass
    
    data = api.call('static_get_champion_list', version = str(version), locale = locale, champ_data = 'stats,tags,info,partype,passive,spells,skins,lore,allytips,enemytips')['data']
    if locale and re.match('^en', locale) == None:
        data_en = getChampions(version)
        for key, champ in data_en.items():
            data[key]['name_en'] = champ['name']
            data[key]['title_en'] = champ['title']
            data[key]['passive']['name_en'] = champ['passive']['name']
            for i,v in enumerate(champ['spells']):
                data[key]['spells'][i]['name_en'] = v['name']
            for i,v in enumerate(champ['skins']):
                if v['name'] != 'default':
                    data[key]['skins'][i]['name_en'] = v['name']
    
    for key, champ in data.items():
        if champ['id'] not in getChampion.keys:
            getChampion.keys[champ['id']] = key
    
    if not getChampions.v or getChampions.v < version:
        getChampions.v = version
        getChampions.cache = {}
    if getChampions.v == version:
        getChampions.cache[locale or 'default'] = data
    try:
        json.dump(data, open('cache/champions-%s-%s.json' % (str(version), locale or 'default'), 'w'))
    except IOError:
        pass
    return data
getChampions.v = None

def getChampion(champ, version, locale = None):
    data = getChampions(version, locale)
    try:
        return data[champ]
    except KeyError: pass
    try:
        return data[getChampion.keys[champ]]
    except KeyError: pass
    for k,d in data.items():
        if d['id'] == champ:
            getChampion.keys[d['id']] = k
            return d
    raise KeyError('No champion \'%s\' in version %s' % (champ, str(version)))
getChampion.keys = {}

def championUpdated(champ, v1, v2, locale = None):
    if v1 == v2:
        return False
    elif v1 > v2:
        v1, v2 = v2, v1
    c1 = getChampion(champ, v1, locale)
    c2 = getChampion(champ, v2, locale)
    
    if c1['title'] != c2['title']: return 1
    for key in c2['stats'].keys():
        if c1['stats'][key] != c2['stats'][key]: return 2
        
    if len(c1['spells']) != len(c2['spells']): return 3
    for i, s2 in enumerate(c2['spells']):
        s1 = c1['spells'][i]
    
        if s1['cooldown'] != s2['cooldown']: return 4
        if s1['cost'] != s2['cost']: return 5
        if s1['costType'].lower() != s2['costType'].lower(): return 6
        if s1['range'] != s2['range']: return 7
        
        try:
            if s1['effect'] != s2['effect']: return 8
        except KeyError:
            if ('effect' in s1) != ('effect' in s2): return 9
        
        try:
            if len(s1['vars']) != len(s2['vars']): return 10
            for j, vv2 in enumerate(s2['vars']):
                vv1 = s1['vars'][j]
                try:
                    if vv1['coeff'] != vv2['coeff']: return 11
                except KeyError:
                    if ('coeff' in vv1) != ('coeff' in vv2): return 12
                try:
                    if vv1['link'] != vv2['link']: return 13
                except KeyError:
                    if ('link' in vv1) != ('link' in vv2): return 14
                try:
                    if vv1['ranksWith'] != vv2['ranksWith']: return 15
                except KeyError:
                    if ('ranksWith' in vv1) != ('ranksWith' in vv2): return 16
        except KeyError:
            if ('vars' in s1) != ('vars' in s2): return 17
    return False