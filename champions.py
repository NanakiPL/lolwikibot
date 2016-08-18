# -*- coding: utf-8  -*-
import pywikibot
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

def update(wikis, version, api):
    pywikibot.output('CHAMPIONS [%s] [%s]' % (version, ', '.join([x['lang'] for x in wikis])))
    champs = api.static_get_champion_list(version = str(version), champ_data = 'stats,tags,info')['data']
    
    universal = {}
    
    i = 1
    for key, champ in champs.items():
        universal[key] = s = {}
        s['stats'] = prepStats(champ['stats'])
        
        
        
        
        i+=1
        if i > 6: break
        
    
    pprint(universal)

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
    ], '6.16.2', getAPI())