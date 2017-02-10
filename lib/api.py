# -*- coding: utf-8  -*-
from riotwatcher import RiotWatcher, LoLException, error_429, error_500, error_503
from time import sleep
from pywikibot import output, input
from requests.exceptions import HTTPError
from distutils.version import StrictVersion

keyFile = 'key.txt'
firstDataVersion = StrictVersion('3.7.1')

def _get():
    global keyFile, api
    try:
        return api
    except NameError:
        try:
            key = readKey()
        except (ValueError, IOError) as e:
            if type(e) is ValueError or e.errno == 2:
                output('Riot API key missing')
            else:
                output('Couldn\'t read %s' % keyFile)
            key = input('Input your key')
            try:
                setKey(key)
            except IOError:
                output('Couldn\'t save the key in a file. Continuing regardless')
        api = RiotWatcher(key)
    return api
    
def readKey():
    global keyFile
    f = open(keyFile)
    try:
        key = f.read().strip()
    finally:
        f.close()
    if key == '': raise ValueError
    return key
    
def setKey(key):
    import os
    global keyFile
    f = open(keyFile, 'w')
    try:
        f.write(key.strip() + '\n')
        os.chmod(f.name, 0o755)
    finally:
        f.close()
    
def call(method, *args, **kargs):
    m = getattr(_get(), method)
    
    noTries = 1
    while True:
        try:
            return m(*args, **kargs)
        except LoLException as e:
            if e.error not in [error_429, error_500, error_503]: raise
            delay = noTries * 5
            noTries += 1
            output('%s(): API error \'%s\'. Retrying in %d seconds' % (method, e.error, delay))
            sleep(delay)
        except HTTPError as e:
            if e.response.status_code not in [403]: raise
            delay = noTries * 5
            noTries += 1
            output('%s(): HTTP error %d. Retrying in %d seconds' % (method, e.response.status_code, delay))
            sleep(delay)

def realm(region = 'na'):
    try:
        return realm.cache[region]
    except KeyError:
        realm.cache[region] = call('static_get_realm', region = region)
        
    return realm.cache[region]
realm.cache = {}

def versions():
    try:
        return versions.cache
    except AttributeError:
        pass
    
    global firstDataVersion
    versions.cache = [StrictVersion(x) for x in call('static_get_versions') ]
    versions.cache = sorted([x for x in versions.cache if x >= firstDataVersion])
    return versions.cache

if __name__ == '__main__':
    try:
        output('Current key: \03{lightyellow}%s\03{default}' % readKey())
    except (ValueError, IOError):
        pass
    
    key = input('Input your key (empty to skip)').strip()
    if key != '':
        setKey(key)
    
    try:
        realm()
        output('\03{lightgreen}Good to go\03{default}')
    except:
        output('\03{lightred}API doesn\'t cooperate - check your key\03{default}')
        raise