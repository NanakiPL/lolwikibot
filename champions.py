# -*- coding: utf-8  -*-
import pywikibot, re, api, lua
from bot import bot, twtranslate
bot = bot()

# Other
from collections import OrderedDict

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
        if skin['num'] > 0:
            maxId = max(maxId, skin['num'])
            s[skin['num']] = skin['name']
    res = [None] * maxId
    for x in range(0, maxId):
        res[x] = s[x+1] if x+1 in s else None
    return res

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
    locales = list(set(locales))
    res = {}
    for locale in locales:
        res[locale] = {}
        addEn = re.match('^en', locale) == None
        
        champs = api.call('static_get_champion_list', champ_data = 'skins', version = str(version), locale = locale)['data']
        for key, champ in champs.items():
            res[locale][key] = {}
            res[locale][key]['name'] = champ['name']
            res[locale][key]['title'] = champ['title']
            res[locale][key]['skins'] = prepSkins(champ['skins'])
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
    
def savePage(wiki, page, champ, locale, intro = '', outro = ''):
    global bot
    
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
        'skins',
        'update',
    ])
    
    newtext = (u'%s\n\nreturn %s\n\n%s' % (intro, data, outro)).strip()
    
    print('SAVING: %s' % page)
    wiki.saveModule(page, newtext, summary = 'create' if page.exists() else 'update')
    
    return
    
    old_text = ''
    isNew = True
    try:
        old_text = page.get()
        isNew = False
    except pywikibot.exceptions.NoPage:
        pass
    
    
    
    changed, version = compare(old_text, newtext)
    if changed:
        match = re.match('^([0-9]+\.[0-9]+)\.[0-9]+$', champ['update'])
        summary = twtranslate(page.site, 'champions-%s-summary' % ()) % {
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
            page.put(newtext, summary = summary)
        
    else:
        pywikibot.output(u'No changes were needed on %s' % page.title(asLink=True))
    pywikibot.output('')
    
def updateChampions(wikis, locales, universal):
    for key, champ in sorted(universal.items(), key=lambda x: x[1]['name'])[11:13]:
        for wiki in wikis:
            page = pywikibot.Page(wiki, wiki.other['champModule'] % locales[wiki.locale][key]['name'])
            
            intro, outro = wiki.moduleComments('champion')
            
            savePage(wiki, page, champ, locales[wiki.locale][key], intro = intro, outro = outro)
            
            
def update(wikis, version):
    for wiki in wikis:
        page = pywikibot.Page(wiki, u'Module:Champion')
        try:
            page = page.getRedirectTarget()
        except pywikibot.exceptions.IsNotRedirectPage:
            pass
        wiki.other['champModule'] = u'%s/%%s/data' % page.title()
        wiki.saveVersion('champion', '1.1.1')
    
    universal = universalData(version)
    locales = localeData(version, [x.locale for x in wikis], universal)
    
    updateChampions(wikis, locales, universal)