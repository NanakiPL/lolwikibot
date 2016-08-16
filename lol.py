# -*- coding: utf-8  -*-

import pywikibot
from riotwatcher import RiotWatcher, LoLException
import re

# Global switches
saveAll = False
ignoreVC = False
workOn = False

def getAPI():
    f = open('key.txt', 'r')
    key = f.read()
    print(key)
    
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
            if site.has_mediawiki_message('custom-lolwikibot-language'):
                sites[lang]['locale'] = site.mediawiki_message('custom-lolwikibot-language').lower()
                if sites[lang]['locale'] == '': del sites[lang]['locale']
            else:
                pywikibot.output('\03{lightaqua}%s\03{default} doesn\'t have a language specified - assuming region default' % site)
            sites[lang]['api'] = lolapi.get(sites[lang]['region'])
        else:
            pywikibot.output('\03{lightaqua}%s\03{default} doesn\'t have a region specified - please, create page containting region code under \03{lightyellow}MediaWiki:Custom-lolwikibot-region\03{default}' % site)
            del sites[lang]
    
    pywikibot.output('Here is a list of language variants that your bot can work on.\r\n')
    pywikibot.output('\03{lightyellow}Wiki lang   Region   Locale\03{default}')
    for lang in codes:
        pywikibot.output('%(lang)-9s   %(region)-6s   %(locale)-5s' % sites[lang])
    
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
                raise pywikibot.bot.QuitKeyboardInterrupt
            list = re.split(u'[\s\.,;]+', list)
            for lang in list:
                if lang not in sites:
                    workOn = False
                    raise Exception(lang)
            break
        except pywikibot.bot.QuitKeyboardInterrupt: raise
        except Exception, lang:
            pywikibot.output('Invalid code specified (%s). Try again.' % lang)
    for i, lang in enumerate(list):
        list[i] = sites[lang]
    return list
        

def main():
    global saveAll, ignoreVC, workOn
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