# -*- coding: utf-8  -*-

import pywikibot
from riotwatcher import RiotWatcher, LoLException
from distutils.version import LooseVersion
import re

# Global switches
saveAll = False
ignoreVC = False
workOn = False

class GeneralQuit(Exception): pass

def getAPI(key):
    if not key:
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
    return RiotWatcher(key)
    
def getSites():
    codes = sorted(pywikibot.config.usernames[pywikibot.config.family].keys())
    try:
        codes.insert(0, codes.pop(codes.index(u'en')))
    except ValueError:
        pass
    
    realms = {}
    sites = {}
    for lang in codes:
        sites[lang] = {}
        sites[lang]['site'] = site = pywikibot.Site(lang)
        sites[lang]['lang'] = site.lang
        
        try:
            sites[lang]['version'] = LooseVersion(re.match('([0-9]+\.[0-9]+\.[0-9]+)', site.expand_text('{{#invoke:lolwikibot|get|champions}}')).group(1))
        except AttributeError:
            sites[lang]['version'] = None
        
        if site.has_mediawiki_message('custom-lolwikibot-region'):
            sites[lang]['region'] = site.mediawiki_message('custom-lolwikibot-region').lower()
            if sites[lang]['region'] not in realms:
                realms[sites[lang]['region']] = api.static_get_realm(region = sites[lang]['region'])
            realm = realms[sites[lang]['region']]
            sites[lang]['update'] = LooseVersion(realm['v'])
            
            try:
                sites[lang]['locale'] = site.mediawiki_message('custom-lolwikibot-language').lower()
                if sites[lang]['locale'] == '': raise ValueError
            except (ValueError, KeyError):
                sites[lang]['locale'] = realms[sites[lang]['region']]['l']
                pywikibot.output('\03{lightaqua}%s\03{default} doesn\'t have a language specified - assuming region default: %s' % (site, realms[sites[lang]['region']]['l']))
        else:
            pywikibot.output('\03{lightaqua}%s\03{default} doesn\'t have a region specified - please, create page containting region code under \03{lightyellow}MediaWiki:Custom-lolwikibot-region\03{default}' % site)
            del sites[lang]
    
    pywikibot.output('\r\nHere is a list of language variants that your bot can work on:\r\n')
    pywikibot.output('\03{lightyellow}Language    Region    Locale    Version: wiki    current\03{default}')
    for lang in codes:
        pywikibot.output('%(lang)-8s    %(region)-6s    %(locale)-6s    %(color)s%(version)13s    %(update)-7s\03{default}' % {
            'lang': sites[lang]['lang'],
            'region': sites[lang]['region'],
            'locale': sites[lang]['locale'],
            'version': sites[lang]['version'],
            'update': sites[lang]['update'],
            'color': '\03{lightred}' if sites[lang]['version'] < sites[lang]['update'] else '\03{lightgreen}',
        })
    codes = [x for x in codes if sites[x]['version'] < sites[x]['update']]
    print(codes)
    
    global workOn
    pywikibot.output('\r\nWhich ones do you want to work on?')
    pywikibot.output('\03{gray}(List of lang codes or empty to quit)\03{default}')
    while True:
        try:
            if workOn == True:
                pywikibot.output('Langs: \03{lightaqua}all\03{default}')
                return sites
            elif workOn:
                list = workOn
                pywikibot.output('Langs: \03{lightaqua}%s\03{default}' % workOn)
            else:
                list = pywikibot.input('Langs').strip()
            if list == u'':
                raise GeneralQuit
            list = re.split(u'[\s\.,;]+', list)
            for lang in list:
                if lang not in sites:
                    workOn = False
                    raise ValueError(lang)
            break
        except (pywikibot.bot.QuitKeyboardInterrupt, GeneralQuit): raise GeneralQuit
        except ValueError, lang:
            pywikibot.output('Invalid code specified (%s). Try again.' % lang)
    for i, lang in enumerate(list):
        list[i] = sites[lang]
    return list


def main():
    global saveAll, ignoreVC, workOn, stepByStep
    apikey = None
    for arg in pywikibot.handleArgs():
        if   arg == '-force':                saveAll = True
        elif arg == '-all':                  workOn = True
        elif arg.startswith('-langs:'):      workOn = arg[7:]
        elif arg.startswith('-key:'):        apikey = arg[5:]
        elif arg.startswith('-since:'):      stepByStep = arg[7:]
    
    global api
    try:
        api = getAPI(apikey)
        sites = getSites()
        
        getChamps()
        champs = api.static_get_champion_list(version = LooseVersion('6.1.1'), champ_data = 'stats,tags,info')
        print(champs)
        
    except GeneralQuit:
        pass

if __name__ == '__main__':
    main()