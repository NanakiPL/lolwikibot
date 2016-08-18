# -*- coding: utf-8  -*-

import pywikibot
import re

from riotwatcher import RiotWatcher, LoLException
from distutils.version import LooseVersion
from collections import OrderedDict

class GeneralQuit(Exception): pass

def getAPI():
    global api, apikey
    try:
        api = RiotWatcher(apikey)
    except NameError:
        pass
    try:
        return api
    except NameError:
        try:
            f = open('key.txt')
            key = f.read().strip()
            if key == '': raise ValueError()
        except (ValueError, IOError) as e:
            if type(e) is ValueError or e.errno == 2:
                pywikibot.output('Riot API key missing')
            else:
                pywikibot.output('Couldn\'t read key.txt')
            key = pywikibot.input('Input your key')
            try:
                f = open('key.txt', 'w')
                f.write(key)
            except IOError:
                pywikibot.output('Couldn\'t save the key in a file. Continuing regardless')
        api = RiotWatcher(key)
    return api
    
def getRealm(region = 'na'):
    region = str(region).lower()
    try:
        getRealm.realms
    except AttributeError:
        getRealm.realms = {}
    try:
        return getRealm.realms[region]
    except KeyError:
        getRealm.realms[region] = getAPI().static_get_realm(region = region)
    return getRealm.realms[region]
    
def getWikis(langs = None):
    codes = sorted(pywikibot.config.usernames[pywikibot.config.family].keys())
    try:
        codes.insert(0, codes.pop(codes.index(u'en')))
    except ValueError:
        pass
    try:
        codes = validateList(codes, langs)
    except KeyError as e:
        pywikibot.output('\r\nError:  No wiki in \'%s\' language. Valid langs: %s' % (e.args[0], ', '.join(e.args[1])))
        raise GeneralQuit
    
    wikis = OrderedDict()
    for lang in codes:
        wikis[lang] = wiki = {}
        
        wiki['site'] = site = pywikibot.Site(lang)
        wiki['lang'] = lang
        
        try:
            wiki['region'] = site.mediawiki_message('custom-lolwikibot-region').strip().lower()
            if wiki['region'] == '': raise ValueError
        except (ValueError, KeyError):
            pywikibot.output('Notice: \03{lightaqua}%s\03{default} doesn\'t have a region specified - assuming NA' % site)
            wiki['region'] = 'na'
        
        try:
            wiki['locale'] = site.mediawiki_message('custom-lolwikibot-locale').strip()
            if wiki['locale'] == '': raise ValueError
        except (ValueError, KeyError):
            wiki['locale'] = getRealm(wiki['region'])['l']
            pywikibot.output('Notice: \03{lightaqua}%s\03{default} doesn\'t have a locale specified - assuming region default: %s' % (site, wiki['locale']))
    return wikis

def validateList(values, input = None):
    try:
        values = values.keys()
    except AttributeError:
        pass
    
    if input == None: return values
    input = str(input).strip().lower()
    if input == 'all': return values
    input = re.split('\s*,\s*', input)
    
    res = []
    for val in input:
        if val in values:
            res.append(val)
        else:
            raise KeyError(val, values)
    return res
    
def lolVersion(text):
    try:
        return LooseVersion(re.match('^([0-9]+(\.[0-9]+){1,2})$', str(text).strip()).group(1))
    except AttributeError:
        raise ValueError('Bad version format')
    
def fliterWikis(wikis, key):
    global versions
    
    res = {}
    if versions:
        for v in versions:
            res[str(v)] = []
    
    pywikibot.output('\03{lightyellow}Wiki          Region    Locale            Old  New\03{default}')
    for lang, wiki in wikis.items():
        realm = getRealm(wiki['region'])
        new = LooseVersion(realm['n'][key])
        if str(new) not in res: res[str(new)] = []
        try:
            old = wiki['site'].expand_text('{{#invoke:lolwikibot|version|%s}}' % key)
            old = lolVersion(old)
        except ValueError:
            old = None
            old = lolVersion('6.5.1')
        
        if versions:
            skip = False
            for v in versions:
                if (not old or old < v) and new >= v:
                    res[str(v)].append(wiki)
        else:
            global forceUpdate
            skip = not forceUpdate and old >= new
            if not skip:
                res[str(new)].append(wiki)
        pywikibot.output('%(wiki)-10s    %(region)-6s    %(locale)-6s        %(color)s%(old)7s  %(new)-7s\03{default}  %(action)s' % {
            'wiki':    str(wiki['site']),
            'region':  wiki['region'],
            'locale':  wiki['locale'],
            'old':     old,
            'new':     new,
            'color':   '\03{lightred}' if not old or old < new else '\03{lightgreen}',
            'action':  'SKIP' if skip else '',
        })
    return OrderedDict(sorted(res.items(), key=lambda x: LooseVersion(x[0])))
    
def updateType(type, wikis):
    pywikibot.output('\r\n\03{yellow}=====  %-10s   ============================================================\03{default}\r\n' % type.upper())
    
    wikisPerVersion = fliterWikis(wikis, 'champion')
    
    import importlib
    module = importlib.import_module(type)
    
    for version, list in wikisPerVersion.items():
        if len(list) == 0: continue
        pywikibot.output('\r\nVersion: \03{lightyellow}%-10s\03{default}      working on \03{lightaqua}%d %s %s' % (version, len(list), 'wiki\03{default}: ' if len(list) == 1 else 'wikis\03{default}:', ', '.join([x['lang'] for x in list])))
        module.update(list, version, getAPI())
    print(version)
    # TODO: Update current version on wikis (mind region versions)
    

supported_types = [
    'champions'
]

# Global switches
saveAll = False
forceUpdate = False
workOn = False
versions = None

def main():
    global saveAll, forceUpdate, apikey, versions
    
    langs = None
    types = None
    sinceVersion = None
    for arg in pywikibot.handleArgs():
        if   arg == '-always':               saveAll = True
        if   arg == '-force':                forceUpdate = True
        elif arg.startswith('-langs:'):      langs = arg[7:]
        elif arg.startswith('-key:'):        apikey = arg[5:]
        elif arg.startswith('-since:'):      sinceVersion = lolVersion(arg[7:])
        elif arg.startswith('-types:'):      types = arg[7:]
    try:
        # Validate -types:
        try:
            types = validateList(supported_types, types)
        except KeyError as e:
            pywikibot.output('\r\nError:  Type \'%s\' not supported. Valid types: %s' % (e.args[0], ', '.join(e.args[1])))
            raise GeneralQuit
        
        # Validate -since:
        if sinceVersion:
            versions = [LooseVersion(x) for x in getAPI().static_get_versions()]
            versions = [x for x in versions if x >= sinceVersion]
            
        wikis = getWikis(langs)
        for t in types:
            updateType(t, wikis)
        
    except (GeneralQuit, pywikibot.bot.QuitKeyboardInterrupt, KeyboardInterrupt) as e:
        pywikibot.output('\r\n\03{lightaqua}Stopping open threads\03{default} - to force quit press Ctrl+C' + ' again' if type(e) is KeyboardInterrupt else '')
        try:
            pywikibot.stopme()
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    main()