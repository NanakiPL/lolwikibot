# -*- coding: utf-8  -*-

from importlib import import_module
from lib import api
from distutils.version import StrictVersion
import re
        
def getWorkList(bot, type):
    res = {}
    wikis = bot.getWikiList()
    versions = api.versions()
    
    if bot.getOption('latest'):
        for wiki in wikis:
            v = wiki.realm['n'][type]
            if v not in res:
                res[v] = []
            res[v].append(wiki)
    else:
        for v in versions:
            v = str(v)
            if v not in res: res[v] = []
            for wiki in wikis:
                if wiki.needsUpdateTo(type, v):
                    res[v].append(wiki)
    return sorted([x for x in res.items() if len(x[1]) > 0], key = lambda x: StrictVersion(x[0]))
    
def run(bot):
    if len(bot.langs) == 0:
        pywikibot.output('Error: No valid languages to work on')
        bot.quit()
    if len(bot.types) == 0:
        pywikibot.output('Error: No valid types to work on')
        bot.quit()
    for type in bot.types:
        try:
            module = import_module('lib.%s' % type)
            if not hasattr(module, 'update') or not hasattr(module, 'datatype'):
                raise ImportError
        except ImportError:
            continue
        
        name = re.sub('^lib\.', '', module.__name__)
        pywikibot.output('\r\n\r\n\03{yellow}======  \03{lightyellow}%s  \03{yellow}%s\03{default}\r\n' % (name.upper(), '='*(46-len(name))))
        bot.printTable(module.datatype)
        pywikibot.output('\r\n\03{yellow}%s\03{default}' % ('='*56))
        
        for version, list in getWorkList(bot, module.datatype):
            pywikibot.output('\r\n  Version: \03{lightyellow}%-10s\03{default}  working on \03{lightyellow}%d\03{default} wiki%s  \03{lightaqua}%s\03{default}' % (version, len(list), ': ' if len(list) == 1 else 's:', '\03{default}, \03{lightaqua}'.join([x.lang for x in list])))
            try:
                module.update(list, version)
            except api.LoLException as e:
                pywikibot.output('API responded with: %s  - skipping this version' % e.error)
            for wiki in list:
                wiki.other['topVersion'] = str(version)
                wiki.saveVersion(module.datatype, version)
        
        versions = {}
        for wiki in bot.getWikiList():
            if 'topVersion' in wiki.other:
                v = wiki.other['topVersion']
                del wiki.other['topVersion']
                if v not in versions: versions[v] = []
                versions[v].append(wiki)
            
        for version, list in sorted(versions.items(), key = lambda x: StrictVersion(x[0])):
            if hasattr(module, 'topVersion'):
                module.topVersion(list, version)
    
def main():
    import config
    if config.check():
        global pywikibot
        import pywikibot
        from lib.bot import Bot
        
        try:
            Bot.availableOptions['latest'] = False
            bot = Bot()
            for arg in bot.args:
                if arg == '-latest': bot.options['latest'] = True
            
            run(bot)
        except (pywikibot.bot.QuitKeyboardInterrupt, KeyboardInterrupt):
            pywikibot.output('\r\n\03{lightyellow}Quitting\03{default}')
            try:
                pywikibot.stopme()
            except KeyboardInterrupt:
                pass
    
if __name__ == '__main__':
    main()