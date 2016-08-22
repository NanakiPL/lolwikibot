# -*- coding: utf-8  -*-

def checkUserConfig():
    try:
        open('user-configs.py').close()
    except IOError as e:
        if e.errno == 2:
            import config
            return config.main()
        raise
        
    
def main():
    family = checkUserConfig()
    
    print('fam %s' % family)
    import pywikibot
    try:
        return
        from bot import Bot
        bot = Bot('lol')
        bot.run()
        
    except (pywikibot.bot.QuitKeyboardInterrupt, KeyboardInterrupt) as e:
        pywikibot.output('\r\n\03{lightaqua}Stopping open threads\03{default} - to force quit press Ctrl+C' + ' again' if type(e) is KeyboardInterrupt else '')
        try:
            pywikibot.stopme()
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    main()