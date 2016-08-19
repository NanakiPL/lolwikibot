# -*- coding: utf-8  -*-
import pywikibot, re, api, lua
from collections import OrderedDict

# i18n
from pywikibot.i18n import twtranslate, set_messages_package
set_messages_package('i18n')

#
from pprint import pprint

# Global switches
saveAll = False

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

def universalData(version):
    version = str(version)
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
    return res
    
def localeData(version, locales, universal):
    res = {}
    for locale in locales:
        res[locale] = {}
        addEn = re.match('^en', locale) == None
        
        champs = api.call('static_get_champion_list', version = str(version), locale = locale)['data']
        for key, champ in champs.items():
            res[locale][key] = {}
            res[locale][key]['name'] = champ['name']
            res[locale][key]['title'] = champ['title']
            if addEn:
                res[locale][key]['name_en'] = universal[key]['name']
                res[locale][key]['title_en'] = universal[key]['title']
    return res
    
def ignores(text):
    text = re.sub('^\s*--.*?$', '', text, flags=re.M) # remove comments
    text = re.sub('(?<!\-)--\[\[.*?\]\]', '', text, flags=re.M) # remove comment blocks
    
    pattern = re.compile('^\s*\[\'update\'\]\s*=\s*\'([0-9]+(\.[0-9]+){1,2})\'\s*,?\s*$', re.M)
    
    try:
        version = pattern.search(text).group(1)
    except AttributeError:
        version = None
        
    text = pattern.sub('', text) # remove version info
    
    return text.strip(), version
def compare(old, new):
    
    old_ignored, v = ignores(old)
    new_ignored, _ = ignores(new)
    
    if old_ignored == new_ignored:
        return False, v
    
    pywikibot.showDiff(old, new)
    
    return True, v
    
def savePage(page, champ, locale, intro = None, outro = None):
    global saveAll
    pywikibot.output(u'  \03{aqua}%s\03{default}' % page)
    
    match = re.match('^([0-9]+\.[0-9]+)\.[0-9]+$', champ['update'])
    
    data = {}
    data.update(champ)
    data.update(locale)
    
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
        'update',
    ])
    
    new_text = (u'%s\n\nreturn %s\n\n%s' % (intro or '', data, outro or '')).strip()
    try:
        old_text = page.get()
        isNew = False
    except pywikibot.exceptions.NoPage:
        old_text = ''
        isNew = True
    
    changed, version = compare(old_text, new_text)
    if changed:
        summary = twtranslate(page.site, 'champions-%s-summary' % ('create' if isNew else 'update')) % {
            'full': match.group(0),
            'short': match.group(1)
        }
        pywikibot.output(u'\03{lightyellow}Summary:\03{default} %s' % summary)
        
        if saveAll == False:
            choice = pywikibot.input_choice(u'Do you want to accept these changes?', [('Yes', 'y'), ('No', 'n'), ('All', 'a')], 'n')
        else:
            choice = 'a'
        if choice == 'a': saveAll = True
        if choice == 'y' or choice == 'a':
            page.put(new_text, summary = summary)
        
    else:
        pywikibot.output(u'No changes were needed on %s' % page.title(asLink=True))
    pywikibot.output('')
    
def updateChampions(wikis, locales, universal):
    for key, champ in sorted(universal.items(), key=lambda x: x[1]['name']):
        pywikibot.output(u'\03{lightpurple}%s\03{default}' % champ['name'])
        for wiki in wikis:
            site = wiki['site']
            locale = wiki['locale']
            
            page = pywikibot.Page(wiki['site'], wiki['champModule'] % locales[locale][key]['name'])
            
            savePage(page, champ, locales[locale][key], intro = wiki['intro'], outro = wiki['outro'])
            
            
def update(wikis, version):
    
    for wiki in wikis:
        page = pywikibot.Page(wiki['site'], u'Champion', ns=828)
        try:
            page = page.getRedirectTarget()
        except pywikibot.exceptions.IsNotRedirectPage:
            pass
        wiki['champModule'] = u'%s/%%s/data' % page.title()
    
    universal = universalData(version)
    locales = localeData(version, [x['locale'] for x in wikis], universal)
    
    updateChampions(wikis, locales, universal)

    
# For testing purposes:
if __name__ == '__main__':
    from lol import getWikis
    pywikibot.config.simulate = saveAll = True
    update(getWikis().values(), '6.16.1')