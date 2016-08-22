# -*- coding: utf-8  -*-
import os, sys, re

def getConfig(file):
    global cfg
    cfg = {
        'usernames': {},
        'sysopnames': {},
        'disambiguation_comment': {},
        'family_files': {},
    }
    if os.path.exists(file):
        _filestatus = os.stat(file)
        _filemode = _filestatus[0]
        _fileuid = _filestatus[4]
        if sys.platform == 'win32' or _fileuid in [os.getuid(), 0]:
            if sys.platform == 'win32' or _filemode & 0o02 == 0:
                with open(file, 'rb') as f:
                    exec(compile(f.read(), file, 'exec'), cfg)
            else:
                print("WARNING: Skipped '%(fn)s': writeable by others."
                      % {'fn': file})
        else:
            print("WARNING: Skipped '%(fn)s': owned by someone else."
                  % {'fn': file})
        return True
    return False

def main():
    os.environ['PYWIKIBOT2_NO_USER_CONFIG'] = '1'
    import pywikibot
    from pywikibot import output, input, input_choice, Site
    from importlib import import_module
    from family import Family
    global cfg, family
    
    family = Family()
    
    if not getConfig('user-config2.py'): cfg = None
    
    output('\r\n  \03{yellow}+------------------------------+\03{default}')
    output('  \03{yellow}|  \03{lightyellow}Pywikibot config generator  \03{yellow}|\03{default}')
    output('  \03{yellow}+------------------------------+\03{default}\r\n')
    
    if not cfg:
        output('  Your user-config.py file is missing. Follow these steps to create it\r\n\r\n')
    
    output('\r\n> \03{lightyellow}Step 1\03{default}: Username')
    output('  Which account do you want to be used for bot edits\r\n')
    usernamePrompt = True
    if cfg:
        unames = sorted(list(set([x[1] for x in cfg['usernames'][family.name].items()])))
        if len(unames) == 1:
            output('Your current bot username is: %s' % unames[0])
            botname = unames[0]
            usernamePrompt = input_choice('Do you want to change it?', [('Yes', 'y'), ('No', 'n')], 'n', automatic_quit=False) == 'y'
        elif len(unames) > 1:
            output('Currently you use several different usernames: %s' % ', '.join(unames))
            output('Unfortunetly this script doesn\'t support complex config setups.')
            choice = input_choice('Do you want to discard your current config?', [('Yes', 'y'), ('No', 'n')], 'n', automatic_quit=False)
            if choice == 'n': raise pywikibot.bot.QuitKeyboardInterrupt
            else: cfg = None
    
    if usernamePrompt:
        botname = raw_input("\r\nPlease enter Wikia username of your bot: ")
    output('')
    
    
    output('\r\n> \03{lightyellow}Step 2\03{default}: Wikis')
    output('  Now you\'ll specify on which wikis do you want the bot to update data\r\n')
    langs = sorted(family.langs.keys())
    try:
        langs.insert(0, langs.pop(langs.index(u'en')))
    except ValueError:
        pass
    
    output('Checking user rights')
    
    wikis = []
    for lang in langs:
        wiki = {}
        wikis.append(wiki)
        
        wiki['url'] = family.langs[lang]
        wiki['site'] = site = Site(lang, family)
        for user in site.users(botname): break
        
        wiki['isBot'] = 'bot' in user['groups']
        wiki['isSysop'] = 'sysop' in user['groups']
        wiki['isGloBot'] = 'bot-global' in user['groups']
        
        wiki['botname'] = None
        wiki['sysopname'] = None
        
    
    output('Current flags your bot has on LoL wikis:')
    output('  \03{lightyellow}Lang   URL                                             Bot     Sysop\03{default}')
    for wiki in wikis:
        isBot = '\03{lightgreen}Yes   \03{default}' if wiki['isBot'] else ('\03{lightpurple}Global\03{default}' if wiki['isGloBot'] else '\03{lightred}No    \03{default}')
        isSysop = '\03{lightgreen}Yes\03{default}' if wiki['isSysop'] else '\03{lightred}No\03{default}'
        output('  \03{lightaqua}%(code)-5s\03{default}  http://%(url)-40s %(isBot)s  %(isSysop)s' % {
            'code': wiki['site'].code,
            'url': wiki['url'],
            'isBot': isBot,
            'isSysop': isSysop,
        })
    
    output('\r\nWhich of these should be editable?')
    output('(comma separated list of lang codes or empty for all that have a bot flag)')
    langs = input('Input')
    if langs == '':
        langs = None
    else:
        langs = re.split('\s*,\s*', langs.lower())
    
    for wiki in wikis:
        if not langs:
            if wiki['isBot'] or wiki['isGloBot']:
                wiki['botname'] = botname
        elif wiki['site'].code in langs:
            wiki['botname'] = botname
        if wiki['botname'] and wiki['isSysop']:
            wiki['sysopname'] = botname
    
    output('\r\n> \03{lightyellow}Step 2\03{default}: Sysop accounts')
    output('  There are some actions that might require an account with higher privileges, like protecting pages or editing ones that are protected.')
    output('  These actions will be skipped when there is no sysop account available.')
    output('  Also remember that these actions will show up in Recent Changes unless the account has a bot flag too.\r\n')
    
    #TODO
    
    output('> \03{lightyellow}Step 4\03{default}: Summary\r\n')
    output('  \03{lightyellow}Lang     Bot account             Sysop account\03{default}')
    for wiki in wikis:
        output('  \03{lightaqua}%(code)-5s\03{default}    %(botname)-20s    %(sysopname)s' % {
            'code': wiki['site'].code,
            'botname': wiki['botname'] or '',
            'sysopname': wiki['sysopname'] or '',
        })
    
if __name__ == '__main__':
    main()
    pass