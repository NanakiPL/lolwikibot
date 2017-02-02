# -*- coding: utf-8  -*-
import os, sys, re
os.environ['PYWIKIBOT2_NO_USER_CONFIG'] = '1'

import pywikibot, os
from pywikibot import output, input, input_choice, Site
from importlib import import_module
from lib.family import Family
from lib import api

config_file = 'user-config.py'

def saveConfig(wikis):
    global family
    res = """# -*- coding: utf-8  -*-
from __future__ import unicode_literals

family = '%(family)s'
usernames[family] = {}
sysopnames[family] = {}
disambiguation_comment[family] = {}
family_files = { family: 'lib/family.py' }

# Keep above as is. Usernames and config follows.""" % {'family': family.name}
    
    for wiki in wikis:
        code = wiki['site'].code
        res += '\r\n\r\n\r\n#  %s  http://%s/\r\n' % (code, wiki['url'])
        res += '\r\n%susernames[family][\'%s\'] = \'%s\'' % ('' if wiki['usebot'] else '# ', code, botname)
        res += '\r\n%ssysopnames[family][\'%s\'] = \'%s\'' % ('' if wiki['sysopname'] else '# ', code, wiki['sysopname'] or botname)
    
    import codecs
    
    f = codecs.open(config_file, 'w', 'utf-8')
    f.write(res)
    os.chmod(f.name, 0o755)
    

def getConfig():
    global cfg, config_file
    cfg = {
        'usernames': {},
        'sysopnames': {},
        'disambiguation_comment': {},
        'family_files': {},
    }
    if os.path.exists(config_file):
        status = os.stat(config_file)
        if sys.platform == 'win32' or status[4] in [os.getuid(), 0]:
            if sys.platform == 'win32' or status[0] & 0o02 == 0:
                with open(config_file, 'rb') as f:
                    exec(compile(f.read(), config_file, 'exec'), cfg)
            else:
                print("WARNING: Skipped '%(fn)s': writeable by others."
                      % {'fn': config_file})
        else:
            print("WARNING: Skipped '%(fn)s': owned by someone else."
                  % {'fn': config_file})
        return True
    return False

def check(create = False):
    global config_file
    if not os.path.exists(config_file):
        if create:
            main(True)
            from pywikibot import output
            if os.path.exists(config_file):
                output('\r\n\03{lightgreen}Config file saved. Run the script again for changes to take effect\03{default}')
            else:
                output('\r\n\03{lightred}Config file creation failed - try again\03{default}')
        return False
    return True

def stepUsername(i):
    global cfg, family, botname
    output('\r\n> \03{lightyellow}Step %d\03{default}: Username' % i)
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
    
def stepWikis(i):
    global family, botname, wikis
    output('\r\n> \03{lightyellow}Step %d\03{default}: Wikis' % i)
    output('  Now you can specify wikis where you want the bot to update the data\r\n')
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
        
        wiki['usebot'] = False
        wiki['sysopname'] = None
    
    output('Current flags your bot has on LoL wikis:')
    output('  \03{lightyellow}Lang   URL                                             Bot     Sysop\03{default}')
    for wiki in wikis:
        isBot = '\03{lightgreen}Yes   \03{default}' if wiki['isBot'] else ('\03{lightpurple}Global\03{default}' if wiki['isGloBot'] else '\03{lightred}No    \03{default}')
        isSysop = '\03{lightgreen}Yes\03{default}' if wiki['isSysop'] else '\03{lightred}No\03{default}'
        output('  \03{lightaqua}%(code)-5s  http://%(url)-40s\03{default} %(isBot)s  %(isSysop)s' % {
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
                wiki['usebot'] = True
        elif wiki['site'].code in langs:
            wiki['usebot'] = True
            
def stepSysop(i):
    global family, botname, wikis
    output('\r\n> \03{lightyellow}Step %d\03{default}: Sysop accounts' % i)
    output('  Some actions like protecting pages may require a sysop account.')
    output('  These actions will be skipped when there is no sysop account available.\r\n')
    
    for wiki in wikis:
        if not wiki['usebot']: continue
        output('\r\n\03{lightaqua}%s  http://%s\03{default}' % (wiki['site'].code, wiki['url']))
        answers = []
        default = None
        
        try:
            sysop = cfg['sysopnames'][family.name][wiki['site'].code].strip()
            if sysop != '':
                output('Currently in config: %s' % sysop)
                answers.append(('Keep current', 'k'))
                default = 'k'
        except (TypeError, KeyError):
            pass
        
        if wiki['isSysop']:
            output('Your bot \03{lightgreen}has sysop rights\03{default} here')
            answers.append(('Use bot', 'b'))
            default = default or 'b'
            
        if len(answers):
            answers.append(('Use another', 'a'))
        else:
            answers.append(('Specify', 's'))
        answers.append(('Don\'t use any', 'd'))
            
        choice = input_choice('\r\nWhat do you want to do?', answers, default or 'd', automatic_quit = False)
        if choice == 'k':
            wiki['sysopname'] = sysop
        elif choice == 'b':
            wiki['sysopname'] = botname
        elif choice == 'a' or choice == 's':
            wiki['sysopname'] = input('Sysop username for \03{lightaqua}%s\03{default}' % wiki['site'].code)
    
def stepSummary(i, force):
    output('\r\n> \03{lightyellow}Step %d\03{default}: Summary\r\n' % i)
    output('  \03{lightyellow}Lang     Bot account             Sysop account\03{default}')
    for wiki in wikis:
        output('  \03{lightaqua}%(code)-5s\03{default}    %(botname)-20s    %(sysopname)s' % {
            'code': wiki['site'].code,
            'botname': botname if wiki['usebot'] else '',
            'sysopname': wiki['sysopname'] or '',
        })
            
    output('')
    if force or input_choice('Do you want to save new config?', [('Yes', 'y'), ('No', 'n')], 'y', automatic_quit = False) == 'y':
        saveConfig(wikis)
            
def stepAPI(i):
    output('\r\n> \03{lightyellow}Step %d\03{default}: Riot API key' % i)
    output('  You need a key to use Riot\'s API. You can get it here:')
    output('  https://developer.riotgames.com/\r\n')
    
    try:
        key = api.readKey()
        output('  \03{lightyellow}Current key:\03{default} %s\r\n' % key)
        if input_choice('Do you want to change the key?', [('Yes', 'y'), ('No', 'n')], 'n', automatic_quit = False) == 'n':
            return
    except (ValueError, IOError) as e:
        pass
    
    key = input('Key')
    
    try:
        api.setKey(key)
    except IOError:
        output('Couldn\'t save the key in a file. Make sure you have permission to write \'%s\'' % api.keyFile)
    
def main(force = False):
    global cfg, family, botname
    
    family = Family()
    
    if not getConfig(): cfg = None
    
    output('\r\n\03{yellow}+------------------------------+\03{default}')
    output('\03{yellow}|  \03{lightyellow}Pywikibot config generator  \03{yellow}|\03{default}')
    output('\03{yellow}+------------------------------+\03{default}\r\n')
    
    if not cfg:
        output('Your user-config.py file is missing. Follow these steps to create it\r\n\r\n')
    
    stepUsername(1)
    stepWikis(2)
    stepSysop(3)
    stepSummary(4, force)
    stepAPI(5)
    
if __name__ == '__main__':
    main()