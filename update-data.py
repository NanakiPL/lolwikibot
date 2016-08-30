# -*- coding: utf-8  -*-

from importlib import import_module
from lib.api import LoLException
from distutils.version import StrictVersion
    
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
            if not hasattr(module, 'update') or not hasattr(module, 'type'):
                raise ImportError
        except ImportError:
            continue
        
        pywikibot.output('\r\n\r\n\03{yellow}======  \03{lightyellow}%s  \03{yellow}%s\03{default}\r\n' % (module.__name__.upper(), '='*(50-len(module.__name__))))
        bot.printTable(module.type)
        pywikibot.output('\r\n\03{yellow}%s\03{default}' % ('='*(60)))
        
        for version, list in bot.getWorkList(module.type):
            pywikibot.output('\r\n  Version: \03{lightyellow}%-10s\03{default}  working on \03{lightyellow}%d\03{default} wiki%s  \03{lightaqua}%s\03{default}' % (version, len(list), ': ' if len(list) == 1 else 's:', '\03{default}, \03{lightaqua}'.join([x.lang for x in list])))
            try:
                module.update(list, version)
            except LoLException as e:
                pywikibot.output('API responded with: %s  - skipping this version' % e.error)
            for wiki in list:
                wiki.other['topVersion'] = str(version)
        
        pywikibot.output('\r\n  Saving info about latest version')
        versions = {}
        for wiki in bot.getWikiList():
            v = wiki.other['topVersion']
            if v not in versions: versions[v] = []
            versions[v].append(wiki)
            
        for version, list in sorted(versions.items(), key = lambda x: StrictVersion(x[0])):
            if hasattr(module, 'topVersion'):
                module.topVersion(list, version)
            for wiki in list:
                wiki.saveVersion(type, version)
    
def main():
    import config
    if config.check():
        global pywikibot
        import pywikibot
        from lib.bot import Bot
        
        try:
            run(Bot())
        except (pywikibot.bot.QuitKeyboardInterrupt, KeyboardInterrupt):
            pywikibot.output('\r\n\03{lightyellow}Quitting\03{default}')
            try:
                pywikibot.stopme()
            except KeyboardInterrupt:
                pass
    
if __name__ == '__main__':
    main()