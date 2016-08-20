# -*- coding: utf-8  -*-

import pywikibot, re, api

from distutils.version import LooseVersion
from collections import OrderedDict

# i18n
from pywikibot.i18n import twtranslate, set_messages_package
set_messages_package('i18n')

# Supported types
supported_types = [
    'champions'
]

# Global switches
saveAll = False
forceUpdate = False

class GeneralQuit(Exception): pass
    
def getRealm(region = 'na'):
    region = str(region).lower()
    try:
        getRealm.realms
    except AttributeError:
        getRealm.realms = {}
    try:
        return getRealm.realms[region]
    except KeyError:
        getRealm.realms[region] = api.call('static_get_realm', region = region)
    return getRealm.realms[region]
    
def getWikis(langs = None):
    from lua import commentify
    
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
        wiki['version'] = {}
        
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
        
        try:
            wiki['intro'] = site.mediawiki_message('custom-lolwikibot-module-intro').strip()
            if wiki['intro'] == '': raise ValueError
            wiki['intro'] = commentify(wiki['intro'])
        except (ValueError, KeyError):
            wiki['intro'] = None
            
        try:
            wiki['outro'] = site.mediawiki_message('custom-lolwikibot-module-outro').strip()
            if wiki['outro'] == '': raise ValueError
            wiki['outro'] = commentify(wiki['outro'])
        except (ValueError, KeyError):
            wiki['outro'] = None
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
    
versions = None
def fliterWikis(wikis, key):
    global versions
    
    res = {}
    if versions:
        for v in versions:
            res[str(v)] = []
    
    pywikibot.output('  \03{lightyellow}Wiki          Region    Locale            Old  New\03{default}')
    for lang, wiki in wikis.items():
        realm = getRealm(wiki['region'])
        new = LooseVersion(realm['n'][key])
        if str(new) not in res: res[str(new)] = []
        try:
            old = wiki['site'].expand_text('{{#invoke:lolwikibot|version|%s}}' % key)
            old = lolVersion(old)
        except ValueError:
            old = None
        
        if versions:
            skip = False
            for v in versions:
                if (not old or old < v) and new >= v:
                    res[str(v)].append(wiki)
        else:
            global forceUpdate
            skip = not forceUpdate and old and old >= new
            if not skip:
                res[str(new)].append(wiki)
        pywikibot.output('  %(wiki)-10s    %(region)-6s    %(locale)-6s        %(color)s%(old)7s  %(new)-7s\03{default}  %(action)s' % {
            'wiki':    str(wiki['site']),
            'region':  wiki['region'],
            'locale':  wiki['locale'],
            'old':     old,
            'new':     new,
            'color':   '\03{lightred}' if not old or old < new else '\03{lightgreen}',
            'action':  'SKIP' if skip else '',
        })
    return OrderedDict(sorted(res.items(), key=lambda x: LooseVersion(x[0])))
    
def saveVersion(site, type, version):
    global saveAll
    page = pywikibot.Page(site, u'lolwikibot/%s' % type, ns=828)
    pywikibot.output(u'\n\n>>> \03{lightpurple}%s\03{default} <<<' % page)
    
    try:
        old_text = page.get()
    except pywikibot.exceptions.NoPage:
        old_text = ''
        
    new_text = 'return {\'%s\'}' % version
    
    if new_text != old_text:
        pywikibot.showDiff(old_text, new_text)
        summary = twtranslate(site, 'lolwikibot-version-summary')
        pywikibot.output(u'\03{lightyellow}Summary:\03{default} %s' % summary)
        
        if saveAll == False:
            choice = pywikibot.input_choice(u'Do you want to accept these changes?', [('Yes', 'y'), ('No', 'n'), ('All', 'a')], 'n')
        else:
            choice = 'a'
        if choice == 'a': saveAll = True
        if choice == 'y' or choice == 'a':
            page.put(new_text, summary = summary)
    
    
    
def updateType(type, wikis):
    pywikibot.output('\r\n\03{yellow}=====  %-10s   ============================================================\03{default}\r\n' % type.upper())
    
    from importlib import import_module
    module = import_module(type)
    
    wikisPerVersion = fliterWikis(wikis, module.type)
    
    global saveAll
    module.saveAll = saveAll
    
    for version, list in wikisPerVersion.items():
        if len(list) == 0: continue
        pywikibot.output('\r\n  Version: \03{lightyellow}%-10s\03{default}      working on \03{lightaqua}%d %s %s' % (version, len(list), 'wiki\03{default}: ' if len(list) == 1 else 'wikis\03{default}:', ', '.join([x['lang'] for x in list])))
        module.update(list, version)
        for wiki in list:
            wiki['version'][module.type] = version
    saveAll = module.saveAll
    
    for lang, wiki in wikis.items():
        try:
            saveVersion(wiki['site'], module.type, wiki['version'][module.type])
        except KeyError:
            pass

def main():
    global saveAll, forceUpdate, versions
    
    langs = None
    types = None
    sinceVersion = None
    for arg in pywikibot.handle_args():
        if   arg == '-always':               saveAll = True
        if   arg == '-dryrun':               pywikibot.config.simulate = True
        if   arg == '-force':                forceUpdate = True
        elif arg.startswith('-langs:'):      langs = arg[7:]
        elif arg.startswith('-key:'):        api.setKey(arg[5:])
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
            versions = [x for x in [LooseVersion(x) for x in api.call('static_get_versions')] if x >= sinceVersion]
            
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