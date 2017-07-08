# -*- coding: utf-8 -*-

import pywikibot, re

from data import *
from ..bot import Bot, twtranslate, LuaError

bot = Bot()

# Other
from distutils.version import StrictVersion

def missingStats(data):
    try:
        desc = data['description_en']
    except KeyError:
        desc = data['description']
    desc = re.search('(?is)<stats>(.*?)</stats>', desc).group(1)
    
    res = {}
    
    try:
        v = float(re.search(r'(?i)([-+]?\d+(?:\.\d+)?)\% Base Mana Regen(?:eration)?', desc).group(1)) / 100
        res['mpregen'] = {'base': v}
    except (AttributeError, ValueError):
        pass
    
    try:
        v = float(re.search(r'(?i)([-+]?\d+(?:\.\d+)?)\% Base Health Regen(?:eration)?', desc).group(1)) / 100
        res['hpregen'] = {'base': v}
    except (AttributeError, ValueError):
        pass
    
    try:
        v = float(re.search(r'(?i)([-+]?\d+(?:\.\d+)?)\% Base Energy Regen(?:eration)?', desc).group(1)) / 100
        res['energyregen'] = {'base': v}
    except (AttributeError, ValueError):
        pass
    
    return res
    
stats_map = {
    'ArmorMod': 'armor',
    'ArmorPenetrationMod': 'armorpen',
    'AttackSpeedMod': 'attackspeed',
    'BlockMod': 'block',
    'CooldownMod': 'cooldown',
    'CritChanceMod': 'critchance',
    'CritDamageMod': 'critdamage',
    'DodgeMod': 'dodge',
    'EXPBonus': 'exp',
    'EnergyMod': 'energy',
    'EnergyPoolMod': 'energy',
    'EnergyRegenMod': 'energyregen',
    'GoldPer10Mod': 'gold',
    'HPMod': 'hp',
    'HPPoolMod': 'hp',
    'HPRegenMod': 'hpregen',
    'LifeStealMod': 'lifesteal',
    'MPMod': 'mp',
    'MPPoolMod': 'mp',
    'MPRegenMod': 'mpregen',
    'MagicDamageMod': 'abilitypower',
    'MagicPenetrationMod': 'magicpen',
    'MovementSpeedMod': 'movespeed',
    'PhysicalDamageMod': 'attackdamage',
    'SpellBlockMod': 'spellblock',
    'SpellVampMod': 'spelvamp',
    'TimeDeadMod': 'timedead',
}
def prepStats(data):
    res = {}
    
    for old, new in stats_map.items():
        stat = {}
        
        try:
            stat['flat'] = data['stats']['Flat' + old]
        except KeyError: pass
        try:
            stat['percent'] = data['stats']['Percent' + old]
        except KeyError: pass
        try:
            stat['r_flat'] = data['stats']['rFlat' + old]
        except KeyError: pass
        try:
            stat['r_percent'] = data['stats']['rPercent' + old]
        except KeyError: pass
        try:
            stat['r_flat_level'] = data['stats']['rFlat' + old + 'PerLevel']
        except KeyError: pass
        try:
            stat['r_percent_level'] = data['stats']['rPercent' + old + 'PerLevel']
        except KeyError: pass
        
        if stat != {}:
            try:
                res[new].update(stat)
            except KeyError:
                res[new] = stat
    
    return res
    
def prepTags(data):
    try:
        return map(lambda x: x.lower(), data['tags'])
    except:
        return []
    
def prepEffects(data):
    res = []
    
    m = max(map(lambda x: int(x.group(1)), filter(None, map(lambda x: re.match(r'^Effect(\d+)Amount$', x), data['effect'].keys()))))
    
    for x in range(1, m+1):
        k = 'Effect%dAmount' % x
        try:
            try:
                res += [int(data['effect'][k])]
            except ValueError:
                res += [float(data['effect'][k])]
        except KeyError:
            res += [None]
    return res
    
def prepItem(key, version, locale):
    data = getItem(key, version, locale)
    item = {}
        
    for k in ['id', 'name', 'name_en', 'plaintext', 'from', 'into', 'hideFromAll', 'inStore', 'colloq', 'maps', 'specialRecipe', 'requiredChampion', 'group', 'consumeOnFull', 'consumed', 'stacks']:
        try:
            item[k] = data[k]
        except KeyError:
            pass
    
    try:
        item['depth'] = data['depth']
    except KeyError:
        item['depth'] = 1
        
    item['tags'] = prepTags(data)
    item['stats'] = prepStats(data)
    try:
        item['stats'].update(missingStats(data))
    except (AttributeError, KeyError):
        pass
    
    try:
        item['effect'] = prepEffects(data)
    except KeyError:
        pass
    
    return item
    
def saveItem(page, item, newver):
    wiki = page.site
    newver = StrictVersion(newver)
    
    data = {}
    try:
        olddata = wiki.fetchData(page)
        data.update(olddata)
        oldver = StrictVersion(olddata['update'])
        action = 'revert'
        if newver > oldver:
            action = 'update'
            changed = itemUpdated(item['id'], oldver, newver)
            if changed:
                pywikibot.output('Item updated since \03{lightyellow}%s\03{default} (%s)' % (oldver, changed))
                data['update'] = str(newver)
        elif newver < oldver:
            if bot.options['downgrade']:
                data['update'] = str(newver)
            else:
                pywikibot.output('Trying to save older data (\03{lightyellow}%s\03{default} -> \03{lightyellow}%s\03{default})' % (oldver, newver))
                pywikibot.output('Use the -downgrade parameter to enable saving')
                return
    except LuaError:
        data, olddata = {}, {}
        data['update'] = str(newver)
        action = 'create'
    
    extra = []
    for k in data.keys():
        if k not in item and k != 'update':
            extra.append(k)
    
    data.update(item)
    if data == olddata:
        summary = twtranslate(wiki, 'lolwikibot-commentsonly-summary')
    else:
        summary = twtranslate(wiki, 'items-%s-summary' % action) % {
            'full': str(newver),
            'short': re.match('^([0-9]+\.[0-9]+)\.[0-9]+$', str(newver)).group(1)
        }
    
    wiki.saveData(page, data, summary = summary, extra = sorted(extra), order = [
        'id',
        'name',
        'name_en',
        'plaintext',
    ])
    
def preload(version, locales):
    pywikibot.output('\n\r  Preloading \03{lightyellow}default locale\03{default} data')
    getItems(version)
    for locale in sorted(locales):
        pywikibot.output('  Preloading \03{lightyellow}%s\03{default} data' % str(locale))
        getItems(version, locale)
    
def update(wikis, version):
    preload(version, set(map(lambda x: x.locale, wikis)))
    items = sorted(getItems(version).keys())
    for key in items:
        for wiki in wikis:
            page = wiki.subpageOf('Module:Item', '%s' % key)
            bot.current_page = page
            
            item = prepItem(key, version, wiki.locale)
            saveItem(page, item, version)