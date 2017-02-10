# -*- coding: utf-8 -*-

import pywikibot, re

from data import getChampions
from ..bot import Bot, twtranslate, LuaError

bot = Bot()

# Other
from distutils.version import StrictVersion

from pprint import pprint
    
def saveList(page, champs, newver):
    wiki = page.site
    
    data = {'list': champs, 'update': str(newver)}
    try:
        olddata = wiki.fetchData(page)
        oldver = StrictVersion(olddata['update'])
        action = 'revert'
        if newver > oldver:
            action = 'update'
        elif newver < oldver and not bot.options['downgrade']:
            pywikibot.output('Trying to save older data (\03{lightyellow}%s\03{default} -> \03{lightyellow}%s\03{default})' % (oldver, newver))
            pywikibot.output('Use the -downgrade parameter to enable saving')
            return
    except LuaError:
        olddata = {'list': {}}
        action = 'create'
    
    if champs == olddata['list']:
        data['update'] = olddata['update']
        summary = twtranslate(wiki, 'lolwikibot-commentsonly-summary')
    else:
        summary = twtranslate(wiki, 'champions-%s-list-summary' % action) % {
            'full': str(newver),
            'short': re.match('^([0-9]+\.[0-9]+)\.[0-9]+$', str(newver)).group(1)
        }
    
    wiki.saveData(page, data, summary = summary, order = ['list'])
    
def statLists(wikis, version):
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
    
def tagsList(wikis, version):
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/tags')
        bot.current_page = page
        
        data  = getChampions(version, wiki.locale)
        champs = {}
        
        for key, champ in data.items():
            champs[key] = {
                'id': champ['id'],
                'name': champ['name'],
                'tags': champ['tags']
            }
        saveList(page, champs, version)
    
def resourceList(wikis, version):
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/resource')
        bot.current_page = page
        
        data  = getChampions(version, wiki.locale)
        champs = {}
        
        for key, champ in data.items():
            champs[key] = {
                'id': champ['id'],
                'name': champ['name'],
                'resource': champ['partype']
            }
            try:
                champs[key]['resource_en'] = champ['partype_en']
            except KeyError:
                pass
        saveList(page, champs, version)
    
def infoList(wikis, version):
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/info')
        bot.current_page = page
        
        data  = getChampions(version, wiki.locale)
        champs = {}
        
        for key, champ in data.items():
            champs[key] = {
                'id': champ['id'],
                'name': champ['name'],
                'info': champ['info']
            }
        saveList(page, champs, version)
    
def nameList(wikis, version):
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/name')
        bot.current_page = page
        
        data  = getChampions(version, wiki.locale)
        champs = {}
        
        for key, champ in data.items():
            champs[key] = {
                'id': champ['id'],
                'name': champ['name'],
                'title': champ['title']
            }
            try:
                champs[key]['name_en'] = champ['name_en']
                champs[key]['title_en'] = champ['title_en']
            except KeyError:
                pass
        saveList(page, champs, version)
    
def update(wikis, version):
    nameList(wikis, version)
    infoList(wikis, version)
    resourceList(wikis, version)
    tagsList(wikis, version)
    statLists(wikis, version)