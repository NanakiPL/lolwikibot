# -*- coding: utf-8 -*-

import pywikibot, re

from data import getChampions
from ..bot import Bot, twtranslate, LuaError
from champs import prepStats
from datetime import datetime, timedelta

bot = Bot()

# Other
from distutils.version import StrictVersion

from pprint import pprint
    
def saveList(page, champs, newver):
    wiki = page.site
    newver = StrictVersion(newver)
    
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
    data  = getChampions(version)
    stats = {}
    
    for key, champ in data.items():
        s = prepStats(champ)
        for stat, v in s.items():
            if stat not in stats:
                stats[stat] = {}
            stats[stat][key] = {
                'id': champ['id'],
                'name': champ['name'],
                'stats': {
                    stat: v
                }
            }
    
    for stat, data in sorted(stats.items()):
        for wiki in wikis:
            page = wiki.subpageOf('Module:Champion', 'list/%s' % stat)
            bot.current_page = page
            
            saveList(page, data, version)
    
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
    
def saveAliases(page, keys):
    wiki = page.site
    
    try:
        oldkeys = wiki.fetchData(page)
        action = 'update'
    except LuaError:
        oldkeys = {}
        action = 'create'
    
    extra = []
    for key in oldkeys:
        if key not in keys:
            extra += [key]
    
    keyset = set(keys.values())
    
    keys = dict(oldkeys.items() + keys.items())
    
    for key in keyset:
        try:
            del keys[key]
        except KeyError:
            pass
    
    if keys == oldkeys:
        summary = twtranslate(wiki, 'lolwikibot-commentsonly-summary')
    else:
        summary = twtranslate(wiki, 'champions-%s-keys-summary' % action)
    
    wiki.saveData(page, keys, summary = summary, extra = extra)
    
def aliases(wikis, version):
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'keys')
        bot.current_page = page
        
        data = getChampions(version, wiki.locale)
        keys = {}
        
        for key, champ in data.items():
            keys[champ['id']] = key
            if champ['name'] != key:
                keys[champ['name']] = key
            try:
                if champ['name_en'] != key:
                    keys[champ['name_en']] = key
            except KeyError:
                pass
        saveAliases(page, keys)
    
def saveSkills(page, skills):
    wiki = page.site
    
    try:
        oldkeys = wiki.fetchData(page)
        action = 'update'
    except LuaError:
        oldkeys = {}
        action = 'create'
    
    extra = []
    for key in oldkeys:
        if key not in skills:
            extra += [key]
    
    skills = dict(oldkeys.items() + skills.items())
    
    if skills == oldkeys:
        summary = twtranslate(wiki, 'lolwikibot-commentsonly-summary')
    else:
        summary = twtranslate(wiki, 'champions-%s-skills-summary' % action)
    
    wiki.saveData(page, skills, summary = summary, extra = extra)
    
def skills(wikis, version):
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'skills')
        bot.current_page = page
        
        data = getChampions(version, wiki.locale)
        skills = {}
        
        for champ in data.values():
            s = set()
            
            s.add(champ['passive']['name'])
            s.update(re.split('\s*/\s*', champ['passive']['name']))
            
            for spell in champ['spells']:
                s.add(spell['name'])
                s.update(re.split('\s*/\s*', spell['name']))
                
            for skill in s:
                try:
                    skills[skill].add(champ['name'])
                except KeyError:
                    skills[skill] = set([champ['name']])
        
        for key in skills:
            if len(skills[key]) == 1:
                skills[key] = next(iter(skills[key]))
            else:
                skills[key] = sorted(skills[key])
        saveSkills(page, skills)
        
def deltastr(td):
    s = str(td - timedelta(microseconds = td.microseconds))
    if td.seconds > 1:
        return s
    return '%s.%s' % (s, ('%d' % round(td.microseconds / 10000)).ljust(2, '0'))
    
def updatesList(wikis, version):
    champs = getChampions(version)
    keys = sorted(champs.keys(), key = lambda x: champs[x]['name'])
    count = len(keys)
    
    from time import sleep
    from random import random
    
    for wiki in wikis:
        page = wiki.subpageOf('Module:Champion', 'list/updates')
        bot.current_page = page
        pywikibot.output('Getting versions from champion data modules')
        pywikibot.output('Press Ctrl+C anytime to skip this page\n\r')
        try:
            start_time = datetime.now()
            i = 0
            
            data = {}
            
            for key in keys:
                i += 1
                champpage = wiki.subpageOf('Module:Champion', '%s' % key)
                champ = wiki.fetchData(champpage, suppress = True)
                
                data[key] = {
                    'id': champ['id'],
                    'name': champ['name'],
                    'update': champ['update'],
                }
                
                if i == count:
                    pywikibot.output('Progress: %3d / %3d' % (i, count))
                elif i % 5 == 0:
                    pywikibot.output('Progress: %3d / %3d   Est. time left: %s' % (i, count, deltastr((datetime.now() - start_time) / i * (count - i))))
            saveList(page, data, version)
        except KeyboardInterrupt:
            pywikibot.output('\n\rSkipping this page')