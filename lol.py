# -*- coding: utf-8  -*-

import pywikibot
from riotwatcher import RiotWatcher, LoLException
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
    print('Key: %s' % key)
    return RiotWatcher(key)
    
def getSites():
    codes = sorted(pywikibot.config.usernames[pywikibot.config.family].keys())
    codes.insert(0, codes.pop(codes.index(u'en')))
    
    sites = {}
    for lang in codes:
        sites[lang] = {}
        sites[lang]['site'] = site = pywikibot.Site(lang)
        sites[lang]['lang'] = site.lang
        
        if site.has_mediawiki_message('custom-lolwikibot-region'):
            sites[lang]['region'] = site.mediawiki_message('custom-lolwikibot-region').lower()
            realm = api.static_get_realm(region = sites[lang]['region'])
            sites[lang]['version'] = realm['v']
            try:
                sites[lang]['locale'] = site.mediawiki_message('custom-lolwikibot-language').lower()
                if sites[lang]['locale'] == '': raise ValueError
            except (ValueError, KeyError):
                sites[lang]['locale'] = realm['l']
                pywikibot.output('\03{lightaqua}%s\03{default} doesn\'t have a language specified - assuming region default: %s' % (site, realm['l']))
            print(realm)
        else:
            pywikibot.output('\03{lightaqua}%s\03{default} doesn\'t have a region specified - please, create page containting region code under \03{lightyellow}MediaWiki:Custom-lolwikibot-region\03{default}' % site)
            del sites[lang]
    
    pywikibot.output('Here is a list of language variants that your bot can work on.\r\n')
    pywikibot.output('\03{lightyellow}Wiki lang   Region   Locale   Version\03{default}')
    for lang in codes:
        pywikibot.output('%(lang)-9s   %(region)-6s   %(locale)-6s   %(version)-7s' % sites[lang])
    
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
            if list == '':
                raise GeneralQuit
            list = re.split(u'[\s\.,;]+', list)
            for lang in list:
                if lang not in sites:
                    workOn = False
                    raise Exception(lang)
            break
        except pywikibot.bot.QuitKeyboardInterrupt: raise GeneralQuit
        except Exception, lang:
            pywikibot.output('Invalid code specified (%s). Try again.' % lang)
    for i, lang in enumerate(list):
        list[i] = sites[lang]
    return list
        

def main():
    global saveAll, ignoreVC, workOn
    apikey = None
    for arg in pywikibot.handleArgs():
        if   arg == '-force':                saveAll = True
        elif arg == '-ignorevc':             ignoreVC = True
        elif arg == '-all':                  workOn = True
        elif arg.startswith('-langs:'):      workOn = arg[7:]
        elif arg.startswith('-key:'):        apikey = arg[5:]
    
    global api
    api = getAPI(apikey)
    sites = getSites()
    return 0

if __name__ == '__main__':
    main()