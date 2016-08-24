# -*- coding: utf-8  -*-
import pywikibot, re, api, lua
from bot import getBot, twtranslate
bot = getBot()

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
            'base': round(stats[x], 3),
            'level': round(stats[x + 'perlevel'], 3)
        }
    res['attackrange'] = round(stats['attackrange'], 3)
    res['movespeed'] = round(stats['movespeed'], 3)
    res['attackspeed'] = {
        'offset': round(stats['attackspeedoffset'], 3),
        'level': round(stats['attackspeedperlevel'], 3)
    }
    res['attackspeed']['base'] = round(0.625 / (1 + stats['attackspeedoffset']), 3)
    
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
    
    champs = api.call('static_get_champion_list', version = str(version), champ_data = 'stats,tags,info')['data']
    for key, champ in champs.items():
        res[key] = s = {}
        s['id'] = champ['id']
        s['key'] = key
        
        s['stats'] = prepStats(champ['stats'])
        s['info'] = prepInfo(champ['info'])
        s['tags'] = champ['tags']
        
        s['name'] = champ['name']
        s['title'] = champ['title']
        
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
    
    intro, outro = wiki.moduleComments('champion')
    
    data = lua.ordered_dumps(data, [
        'id',
        'key',
        'name',
        'title',
        'name_en',
        'title_en',
        'tags',
        'info',
        'stats',
        'skins',
    ])
    
    newtext = (u'%s\n\nreturn %s\n\n%s' % (intro, data, outro)).strip()
    
    summary = twtranslate(wiki, 'champions-%s-summary' % ('update' if page.exists() else 'create')) % {
        'full': version.group(0),
        'short': version.group(1)
    }
    wiki.saveModule(page, newtext, summary = summary)
    
def saveList(wiki, page, data):
    wiki = page.site
    version = re.match('^([0-9]+\.[0-9]+)\.[0-9]+$', data['update'])
    
    intro, outro = wiki.moduleComments('champion')
    
    data = lua.ordered_dumps(data, [
        'list'
    ])
    
    newtext = (u'%s\n\nreturn %s\n\n%s' % (intro, data, outro)).strip()
    
    summary = twtranslate(wiki, 'champions-%s-list-summary' % ('update' if page.exists() else 'create')) % {
        'full': version.group(0),
        'short': version.group(1)
    }
    wiki.saveModule(page, newtext, summary = summary)
    
def updateChampions(wikis, locales, universal):
    for key, champ in sorted(universal.items(), key=lambda x: x[1]['name']):
        for wiki in wikis:
            page = pywikibot.Page(wiki, wiki.other['champModule'] % key)
            
            saveChamp(page, champ, locales[wiki.locale][key])
    
def statLists(wikis, universal):
    pages = {}
    for key, champ in sorted(universal.items(), key=lambda x: x[1]['name']):
        for stat in champ['stats']:
            p = 'stats.%s' % stat
            if p not in pages: pages[p] = {'list':{},'update':champ['update']}
            pages[p]['list'][key] = {
                'id': champ['id'],
                'stats': {
                    stat: champ['stats'][stat]
                }
            }
    for wiki in wikis:
        tpl = wiki.other['champListModule']
        for key, data in sorted(pages.items()):
            page = pywikibot.Page(wiki, tpl % key)
            
            saveList(wiki, page, data)
    
def updateLists(wikis, locales, universal):
    statLists(wikis, universal)
    
def update(wikis, version):
    for wiki in wikis:
        page = pywikibot.Page(wiki, u'Module:Champion')
        try:
            page = page.getRedirectTarget()
        except pywikibot.exceptions.IsNotRedirectPage:
            pass
        wiki.other['champModule'] = u'%s/%%s/data' % page.title()
        wiki.other['champListModule'] = u'%s/list/%%s' % page.title()
    
    universal = universalData(version)
    locales = localeData(version, [x.locale for x in wikis])
    
    #updateChampions(wikis, locales, universal)
    #updateLists(wikis, locales, universal)
    
def updateAliases(wikis, aliases):
    for wiki in wikis:
        data = 
    
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
    
def topVersion(wikis, version):
    universal = universalData(version)
    locales = localeData(version, [x.locale for x in wikis])
    
    aliases = prepAliases(locales)
    updateAliases(wikis, aliases)