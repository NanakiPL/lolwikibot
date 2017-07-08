# -*- coding: utf-8 -*-

import pywikibot, re

from data import getItems
from ..bot import Bot, twtranslate, LuaError
from items import prepStats
from datetime import datetime, timedelta

bot = Bot()

# Other
from distutils.version import StrictVersion

from pprint import pprint
    
def saveList(page, items, newver):
    wiki = page.site
    newver = StrictVersion(newver)
    
    data = {'list': items, 'update': str(newver)}
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
    
    if items == olddata['list']:
        data['update'] = olddata['update']
        summary = twtranslate(wiki, 'lolwikibot-commentsonly-summary')
    else:
        summary = twtranslate(wiki, 'items-%s-list-summary' % action) % {
            'full': str(newver),
            'short': re.match('^([0-9]+\.[0-9]+)\.[0-9]+$', str(newver)).group(1)
        }
    
    wiki.saveData(page, data, summary = summary, order = ['list'])
    
def statLists(wikis, version):
    data  = getItems(version)
    stats = {}
    
    for key, item in data.items():
        s = prepStats(item)
        for stat, v in s.items():
            if stat not in stats:
                stats[stat] = {}
            stats[stat][key] = {
                'id': item['id'],
                'name': item['name'],
                'stats': {
                    stat: v
                }
            }
    
    for stat, data in sorted(stats.items()):
        for wiki in wikis:
            page = wiki.subpageOf('Module:Item', 'list/%s' % stat)
            bot.current_page = page
            
            saveList(page, data, version)
    
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
        summary = twtranslate(wiki, 'items-%s-keys-summary' % action)
    
    wiki.saveData(page, keys, summary = summary, extra = sorted(extra))
    
def aliases(wikis, version):
    for wiki in wikis:
        page = wiki.subpageOf('Module:Item', 'keys')
        bot.current_page = page
        
        data = getItems(version, wiki.locale)
        keys = {}
        
        for key, item in data.items():
            try:
                keys[item['name']] = item['id']
                keys[item['name_en']] = item['id']
            except KeyError:
                pass
        saveAliases(page, keys)
    
def deltastr(td):
    s = str(td - timedelta(microseconds = td.microseconds))
    if td.seconds > 1:
        return s
    return '%s.%s' % (s, ('%d' % round(td.microseconds / 10000)).ljust(2, '0'))
    
def updatesList(wikis, version):
    items = getItems(version)
    keys = sorted(items.keys(), key = lambda x: items[x]['name'])
    count = len(keys)
    
    for wiki in wikis:
        page = wiki.subpageOf('Module:Item', 'list/updates')
        bot.current_page = page
        pywikibot.output('Getting versions from item data modules')
        pywikibot.output('Press Ctrl+C anytime to skip this page\n\r')
        try:
            start_time = datetime.now()
            i = 0
            
            data = {}
            
            for key in keys:
                i += 1
                itempage = wiki.subpageOf('Module:Item', '%s' % key)
                item = wiki.fetchData(itempage, suppress = True)
                
                data[key] = {
                    'id': item['id'],
                    'name': item['name'],
                    'update': item['update'],
                }
                
                if i == count:
                    pywikibot.output('Progress: %3d / %3d' % (i, count))
                elif i % 5 == 0:
                    pywikibot.output('Progress: %3d / %3d   Est. time left: %s' % (i, count, deltastr((datetime.now() - start_time) / i * (count - i))))
            saveList(page, data, version)
        except KeyboardInterrupt:
            pywikibot.output('\n\rSkipping this page')