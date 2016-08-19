# -*- coding: utf-8  -*-
from riotwatcher import RiotWatcher, LoLException
from time import sleep

def _get():
    global api, apikey
    try:
        api = RiotWatcher(apikey)
    except NameError:
        pass
    try:
        return api
    except NameError:
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
        api = RiotWatcher(key)
    return api
    
def setKey(key):
    pass
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