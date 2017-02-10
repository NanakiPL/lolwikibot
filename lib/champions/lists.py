# -*- coding: utf-8 -*-


            
            
    
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
    
def update(wikis, version):
    nameList(wikis)
    tagsList(wikis)
    resourceList(wikis)
    infoList(wikis)
    statLists(wikis)