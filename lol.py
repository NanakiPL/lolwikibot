# -*- coding: utf-8  -*-
import os

config_file = 'user-config.py'

def checkUserConfig():
    global config_file
    if not os.path.exists(config_file):
        import config
        config.main(True)
        return False
    return True
    
def main():
    global config_file
    if checkUserConfig():
        import pywikibot
        from bot import getBot
        
        try:
            getBot().run()
        except (pywikibot.bot.QuitKeyboardInterrupt, KeyboardInterrupt) as e:
            pywikibot.output('\r\n\03{lightaqua}Stopping open threads\03{default} - to force quit press Ctrl+C' + ' again' if type(e) is KeyboardInterrupt else '')
            try:
                pywikibot.stopme()
            except KeyboardInterrupt:
                pass
    else:
        from pywikibot import output
        if os.path.exists(config_file):
            output('\r\n\03{lightgreen}Config file is in place, but you have to run the script again\03{default}')
        else:
            output('\r\n\03{lightred}Config file creation failed - try again\03{default}')
        

if __name__ == '__main__':
    main()