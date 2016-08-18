# -*- coding: utf-8  -*-
import pywikibot, re
from collections import OrderedDict

#
from pprint import pprint

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
    
    return OrderedDict(res.items())
    
def prepInfo(info):
    return OrderedDict([
        ('attack', info['attack']),
        ('defense', info['defense']),
        ('magic', info['magic']),
        ('difficulty', info['difficulty'])
    ])

def update(wikis, version, api):
    champs = api.static_get_champion_list(version = str(version), champ_data = 'stats,tags,info')['data']
    
    for wiki in wikis:
        page = pywikibot.Page(wiki['site'], 'Champion', ns=828)
        try:
            page = page.getRedirectTarget()
        except pywikibot.exceptions.IsNotRedirectPage:
            pass
        wiki['champModule'] = '%s/%%s/data' % page.title()
    
    universal = {}
    en = {}
    
    i = 1
    for key, champ in champs.items():
        universal[key] = s = {}
        s['id'] = champ['id']
        s['key'] = key
        
        s['stats'] = prepStats(champ['stats'])
        s['info'] = prepInfo(champ['info'])
        s['tags'] = champ['tags']
        
        en[key] = {
            'name': champ['name'],
            'title': champ['title'],
        }
    
    locales = {}
    for locale in [x['locale'] for x in wikis]:
        locales[locale] = {}
        champs = api.static_get_champion_list(version = str(version), locale = locale)['data']
        
        addEn = re.match('^(en)', locale) == None
        for key, champ in champs.items():
            locales[locale][key] = {}
            locales[locale][key]['name'] = champ['name']
            locales[locale][key]['title'] = champ['title']
            if addEn:
                locales[locale][key]['name_en'] = en[key]['name']
                locales[locale][key]['title_en'] = en[key]['title']
    
    for key, champ in sorted(en.items(), key=lambda x: x[1]['name']):
        pywikibot.output('  \03{lightpurple}%s\03{default}' % (champ['name']))
        for wiki in wikis:
            site = wiki['site']
            locale = wiki['locale']
            
            page = pywikibot.Page(wiki['site'], wiki['champModule'] % locales[locale][key]['name'])
            
            pywikibot.output('    \03{aqua}%s\03{default}' % (page))

# For testing purposes:
if __name__ == '__main__':
    from lol import getAPI
    update([
        {
            'lang': u'en',
            'locale': u'pl_PL',
            'region': u'eune',
            'site': pywikibot.Site("en", "lol")
        }, {
            'lang': u'pl',
            'locale': u'en_US',
            'region': 'na',
            'site': pywikibot.Site("pl", "lol")
        }
    ], '6.10.1', getAPI())