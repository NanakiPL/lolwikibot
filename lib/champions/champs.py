# -*- coding: utf-8 -*-

import pywikibot, re

from data import *
from ..bot import Bot, twtranslate, LuaError

bot = Bot()

# Other
from distutils.version import StrictVersion

def prepStats(data):
    res = {}
    
    for x in ['armor', 'attackdamage', 'crit', 'hp', 'hpregen', 'mp', 'mpregen', 'spellblock']:
        res[x] = {
            'base': round(data['stats'][x], 5),
            'level': round(data['stats'][x + 'perlevel'], 5)
        }
    res['attackrange'] = round(data['stats']['attackrange'], 5)
    res['movespeed'] = round(data['stats']['movespeed'], 5)
    res['attackspeed'] = {
        'offset': round(data['stats']['attackspeedoffset'], 5),
        'level': round(data['stats']['attackspeedperlevel'], 5)
    }
    res['attackspeed']['base'] = round(0.625 / (1 + data['stats']['attackspeedoffset']), 5)
    
    return res
    
def prepSkins(data):
    skins = {}
    maxId = 0
    for skin in data['skins']:
        num = skin['num']
        maxId = max(maxId, num)
        skins[num] = skin
    
    res = {
        'skins': [None] * maxId,
        'skins_en': [None] * maxId,
        'skins_chromas': []
    }
    for x in range(0, maxId+1):
        try:
            s = skins[x]
            try:
                if s['chromas']:
                    res['skins_chromas'] += [x]
            except KeyError:
                pass
            if x == 0: continue
            
            res['skins'][x-1] = s['name']
            try:
                res['skins_en'][x-1] = s['name_en']
            except KeyError:
                pass
        except KeyError:
            res['skins'][x-1] = ''
            res['skins_en'][x-1] = ''
    
    if not any(res['skins_en']):
        del res['skins_en']
    if len(res['skins_chromas']) == 0:
        del res['skins_chromas']
    
    return res
    
def prepSkills(data):
    res = {}
    
    return res

def prepChamp(key, version, locale):
    data = getChampion(key, version, locale)
    champ = {}
    
    champ['id'] = data['id']
    champ['key'] = data['key']
    champ['name'] = data['name']
    champ['title'] = data['title']
    champ['resource'] = data['partype']
    champ['tags'] = data['tags']
    champ['info'] = data['info']
    
    try:
        champ['name_en'] = data['name_en']
        champ['title_en'] = data['title_en']
        champ['resource_en'] = data['partype_en']
    except KeyError:
        pass
    
    champ['stats'] = prepStats(data)
    
    champ.update(prepSkins(data))
    
    return champ
    
def saveChamp(page, champ, newver):
    wiki = page.site
    newver = StrictVersion(newver)
    
    data = {}
    try:
        olddata = wiki.fetchData(page)
        data.update(olddata)
        oldver = StrictVersion(olddata['update'])
        action = 'revert'
        if newver > oldver:
            action = 'update'
            changed = championUpdated(champ['key'], oldver, newver)
            if changed:
                pywikibot.output('Champion updated since \03{lightyellow}%s\03{default} (%s)' % (oldver, changed))
                data['update'] = str(newver)
        elif newver < oldver:
            if bot.options['downgrade']:
                data['update'] = str(newver)
            else:
                pywikibot.output('Trying to save older data (\03{lightyellow}%s\03{default} -> \03{lightyellow}%s\03{default})' % (oldver, newver))
                pywikibot.output('Use the -downgrade parameter to enable saving')
                return
    except LuaError:
        data, olddata = {}, {}
        data['update'] = str(newver)
        action = 'create'
    
    extra = []
    for k in data.keys():
        if k not in champ and k != 'update':
            extra.append(k)
    
    data.update(champ)
    if data == olddata:
        summary = twtranslate(wiki, 'lolwikibot-commentsonly-summary')
    else:
        summary = twtranslate(wiki, 'champions-%s-summary' % action) % {
            'full': str(newver),
            'short': re.match('^([0-9]+\.[0-9]+)\.[0-9]+$', str(newver)).group(1)
        }
    
    wiki.saveData(page, data, summary = summary, extra = sorted(extra), order = [
        'id',
        'key',
        'name',
        'title',
        'name_en',
        'title_en',
    ])
    
def preload(version, locales):
    pywikibot.output('\n\r  Preloading \03{lightyellow}default locale\03{default} data')
    getChampions(version)
    for locale in sorted(locales):
        pywikibot.output('  Preloading \03{lightyellow}%s\03{default} data' % str(locale))
        getChampions(version, locale)
    
def update(wikis, version):
    preload(version, set(map(lambda x: x.locale, wikis)))
    champs = sorted(getChampions(version).keys())
    for key in champs:
        for wiki in wikis:
            page = wiki.subpageOf('Module:Champion', '%s' % key)
            bot.current_page = page
            
            champ = prepChamp(key, version, wiki.locale)
            saveChamp(page, champ, version)