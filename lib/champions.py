# -*- coding: utf-8  -*-
import pywikibot, re, api, lua, sys
from bot import Bot, twtranslate, VersionConflict
bot = Bot()

# Other
from collections import OrderedDict
from distutils.version import StrictVersion

#
from pprint import pprint

# Properties
type = 'champion'

def prepStats(stats):
    res = {}
    
    for x in ['armor', 'attackdamage', 'crit', 'hp', 'hpregen', 'mp', 'mpregen', 'spellblock']:
        res[x] = {
            'base': round(stats[x], 5),
            'level': round(stats[x + 'perlevel'], 5)
        }
    res['attackrange'] = round(stats['attackrange'], 5)
    res['movespeed'] = round(stats['movespeed'], 5)
    res['attackspeed'] = {
        'offset': round(stats['attackspeedoffset'], 5),
        'level': round(stats['attackspeedperlevel'], 5)
    }
    res['attackspeed']['base'] = round(0.625 / (1 + stats['attackspeedoffset']), 5)
    
    return res
    
def prepInfo(info):
    return OrderedDict([
        ('attack', info['attack']),
        ('defense', info['defense']),
        ('magic', info['magic']),
        ('difficulty', info['difficulty'])
    ])
    
def prepSkins(skins):
    s = {}
    maxId = 0
    for skin in skins:
        num = skin['id'] % 1000
        if num > 0:
            maxId = max(maxId, num)
            s[num] = skin['name']
    res = [None] * maxId
    for x in range(0, maxId):
        res[x] = s[x+1] if x+1 in s else None
    return res

def universalData(version):
    version = str(version)
    if version in universalData.cache:
        return universalData.cache[version]
    res = {}
    
    champs = api.call('static_get_champion_list', version = str(version), champ_data = 'stats,tags,info,partype')['data']
    for key, champ in champs.items():
        res[key] = s = {}
        s['id'] = champ['id']
        s['key'] = key
        
        s['stats'] = prepStats(champ['stats'])
        s['info'] = prepInfo(champ['info'])
        s['tags'] = champ['tags']
        
        s['name'] = champ['name']
        s['title'] = champ['title']
        
        s['resource'] = champ['partype']
        
        s['update'] = version
    
    keys = sorted(universalData.cache.keys() + [version], key = lambda x: StrictVersion(x))
    for key in keys[:-2]:
        del universalData.cache[key]
    if version in keys[-2:]:
        universalData.cache[version] = res
    return res
universalData.cache = {}
    
def localeData(version, locales):
    universal = universalData(version)
    locales = list(set(locales))
    res = {}
    for locale in locales:
        res[locale] = {}
        addEn = re.match('^en', locale) == None
        
        champs = api.call('static_get_champion_list', champ_data = 'skins', version = str(version), locale = locale)['data']
        for key, champ in champs.items():
            res[locale][key] = {}
            res[locale][key]['id'] = champ['id']
            res[locale][key]['name'] = champ['name']
            res[locale][key]['title'] = champ['title']
            res[locale][key]['skins'] = prepSkins(champ['skins'])
            res[locale][key]['update'] = version
            if addEn:
                res[locale][key]['name_en'] = universal[key]['name']
                res[locale][key]['title_en'] = universal[key]['title']
    return res
    
def saveChamp(page, champ, locale):
    wiki = page.site
    version = re.match('^([0-9]+\.[0-9]+)\.[0-9]+$', champ['update'])
    
    data = {}
    data.update(champ)
    data.update(locale)
    
    summary = twtranslate(wiki, 'champions-%s-summary' % ('update' if page.exists() else 'create')) % {
        'full': version.group(0),
        'short': version.group(1)
    }
    
    try:
        wiki.saveData(page, data, summary = summary, order = [
            'id',
            'key',
            'name',
            'title',
            'name_en',
            'title_en',
        ])
    except VersionConflict as e:
        pywikibot.output('Version conflict: trying to save older version of data.' % e.old)
    
def saveList(wiki, page, data):
    wiki = page.site
    version = re.match('^([0-9]+\.[0-9]+)\.[0-9]+$', data['update'])
    
    summary = twtranslate(wiki, 'champions-%s-list-summary' % ('update' if page.exists() else 'create')) % {
        'full': version.group(0),
        'short': version.group(1)
    }
    
    try:
        wiki.saveData(page, data, summary = summary, order = ['list'])
    except VersionConflict as e:
        pywikibot.output('Version conflict: trying to save older version of data.' % e.old)
    
def updateChampions(wikis, locales, universal):
    for key, champ in sorted(universal.items(), key=lambda x: x[1]['name']):
        for wiki in wikis:
            page = wiki.subpageOf('Module:Champion', '%s' % key)
            
            saveChamp(page, champ, locales[wiki.locale][key])
    
def statLists(wikis, universal):
    pages = {}
    for key, champ in universal.items():
        for stat in champ['stats']:
            p = 'stats.%s' % stat
            if p not in pages: pages[p] = {'list':{},'update':champ['update']}
            pages[p]['list'][key] = {
                'id': champ['id'],
                'name': champ['name'],
                'stats': {
                    stat: champ['stats'][stat]
                }
            }
    for wiki in wikis:
        for key, data in sorted(pages.items()):
            page = wiki.subpageOf('Module:Champion', 'list/%s' % key)
            
            saveList(wiki, page, data)
    
def tagsList(wikis, universal):
    data = {}
    for key, champ in universal.items():
        data[key] = {
            'id': champ['id'],
            'name': champ['name'],
            'tags': champ['tags']
        }
    data = {'list': data, 'update': champ['update']}
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/tags')
        saveList(wiki, page, data)
    
def resourceList(wikis, universal):
    data = {}
    for key, champ in universal.items():
        data[key] = {
            'id': champ['id'],
            'name': champ['name'],
            'resource': champ['resource']
        }
    data = {'list': data, 'update': champ['update']}
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/resource')
        saveList(wiki, page, data)
    
def infoList(wikis, universal):
    data = {}
    for key, champ in universal.items():
        data[key] = {
            'id': champ['id'],
            'name': champ['name'],
            'info': champ['info']
        }
    data = {'list': data, 'update': champ['update']}
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/info')
        saveList(wiki, page, data)
    
def nameList(wikis, locales):
    res = {}
    for locale, data in locales.items():
        d = {}
        for key, champ in data.items():
            d[key] = {
                'id': champ['id'],
                'name': champ['name'],
                'name_en': champ['name_en'],
                'title': champ['title'],
                'title_en': champ['title_en'],
            }
        res[locale] = {'list': d, 'update': champ['update']}
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/name')
        pprint(res[wiki.locale])
        saveList(wiki, page, res[wiki.locale])
    
def updateLists(wikis, locales, universal):
    nameList(wikis, locales)
    tagsList(wikis, universal)
    resourceList(wikis, universal)
    infoList(wikis, universal)
    statLists(wikis, universal)
    
def update(wikis, version):
    universal = universalData(version)
    locales = localeData(version, [x.locale for x in wikis])
    
    updateChampions(wikis, locales, universal)
    updateLists(wikis, locales, universal)

# Last version only
def updateAliases(wikis, aliases):
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'keys')
        data = aliases[wiki.locale]
        summary = twtranslate(wiki, 'champions-%s-keys-summary' % ('update' if page.exists() else 'create'))
        wiki.saveData(page, data, summary = summary, comments = 'keys')
    
def prepAliases(locales):
    res = {}
    for locale, data in locales.items():
        res[locale] = d = {}
        
        for key, champ in sorted(data.items()):
            d[champ['id']] = key
            if champ['name'] != key:
                d[champ['name']] = key
            if 'name_en' in champ and champ['name_en'] != key:
                d[champ['name_en']] = key
        d = OrderedDict(sorted(d.items(), key = lambda x: x[1]))
    return res
    
def lastUpdateList(wikis, universal):
    global bot
    p = re.compile('([\{,]\s*\[\s*\'update\'\s*\]\s*=\s*\')([0-9]+\.[0-9]+\.[0-9]+)(\'\s*[,\}])')
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/updates')
        bot.current_page = page
        pywikibot.output('Getting versions from champion data modules')
        pywikibot.output('Press Ctrl+C anytime to skip this page')
        
        list = sorted(universal.items(), key=lambda x: x[1]['name'])
        size = len(list)
        i = 0
        
        try:
            res = {}
            for key, champ in list:
                i += 1
                champpage = wiki.subpageOf('Module:Champion', '%s' % key)
                try:
                    match = p.search(champpage.text)
                    ver = match.group(2)
                except AttributeError:
                    ver = None
                if ver:
                    res[key] = str(ver)
                
                sys.stdout.write('\r')
                sys.stdout.flush()
                sys.stdout.write('Progress: %3d / %3d' % (i, size))
                sys.stdout.flush()
            pywikibot.output('')
            wiki.saveData(page, res)
        except KeyboardInterrupt:
            pass
    
def topVersion(wikis, version):
    universal = universalData(version)
    locales = localeData(version, [x.locale for x in wikis])
    
    aliases = prepAliases(locales)
    updateAliases(wikis, aliases)
    #lastUpdateList(wikis, universal)