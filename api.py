# -*- coding: utf-8  -*-
from riotwatcher import RiotWatcher, LoLException
from time import sleep
from pywikibot import output, input

keyFile = 'key.txt'

def _get():
    global keyFile, api
    try:
        return api
    except NameError:
        try:
            key = readKey()
        except (ValueError, IOError) as e:
            if type(e) is ValueError or e.errno == 2:
                pywikibot.output('Riot API key missing')
            else:
                pywikibot.output('Couldn\'t read %s' % keyFile)
            key = pywikibot.input('Input your key')
            try:
                satKey(key)
            except IOError:
                pywikibot.output('Couldn\'t save the key in a file. Continuing regardless')
        api = RiotWatcher(key)
    return api
    
def readKey():
    global keyFile
    f = open(keyFile)
    key = f.read().strip()
    if key == '': raise ValueError
    return key
    
def setKey(key):
    global keyFile
    f = open(keyFile, 'w')
    f.write(key.strip())
    
def call(method, *args, **kargs):
    m = getattr(_get(), method)
    
    noTries = 1
    while True:
        try:
            return m(*args, **kargs)
        except LoLException as e:
            delay = noTries * 5
            noTries += 1
            pywikibot.output('API not responding \'%s\'. Retrying in %d seconds' % (e.error, delay))
            sleep(delay)

if __name__ == '__main__':
    try:
        output('Current key: \03{lightyellow}%s\03{default}' % readKey())
    except (ValueError, IOError):
        pass
    
    key = input('Input your key (empty to skip)').strip()
    if key != '':
        setKey(key)
    
    try:
        call('static_get_realm')
        output('\03{lightgreen}Good to go\03{default}')
    except:
        output('\03{lightred}API doesn\'t cooperate - check your key\03{default}')
        raise