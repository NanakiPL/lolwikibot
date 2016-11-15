# -*- coding: utf-8  -*-
import pywikibot, re, api, lua
from pywikibot import config, output
from pywikibot.bot import Bot
from pywikibot.exceptions import NoPage
from api import LoLException
from json import loads
from ordered_set import OrderedSet

# i18n
from pywikibot.i18n import twtranslate, set_messages_package
set_messages_package('i18n')

# Other
from distutils.version import StrictVersion


from collections import Mapping
def addMissing(f, t):
    changed = False
    for k, v in f.items():
        if k not in t:
            t[k] = v
        elif isinstance(t[k], Mapping) and isinstance(v, Mapping):
            changed = addMissing(v, t[k]) or changed
        else:
            changed = changed or t[k] != v
    if not changed:
        for k, v in t.items():
            if k not in f:
                return True
    return changed
    
def numKeys(data):
    if isinstance(data, dict):
        for k,v in data.items():
            try:
                n = int(k)
                data[n] = numKeys(v)
                del data[k]
            except ValueError:
                pass
    return data

class Bot(Bot):
    family = 'lol'
    
    availableOptions = {
        'always': False,
        'protect': False,
    }
    types = [
        'champions',
        'items',
        'masteries',
        'runes',
        'spells',
    ]
    _save_counter = 0
    langs = []
    
    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Bot,cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
        
    def __init__(self, langs = None):
        if(self.__initialized): return
        self.__initialized = True
        
        types = None
        
        self.options = {
            'always': False,
            'protect': False,
        }
        
        self.args = []
        for arg in pywikibot.handle_args():
            if   arg == '-always':                         self.options['always'] = True
            elif arg == '-protect':                        self.options['protect'] = True
            elif arg == '-dryrun':                         pywikibot.config.simulate = True
            elif arg.startswith('-langs:') and not langs:  langs = arg[7:].split(',')
            elif arg.startswith('-types:'):                types = arg[7:].split(',')
            elif arg.startswith('-key:'):                  api.setKey(arg[5:])
            else: self.args.append(arg)
            
        self.family = pywikibot.family.Family.load(self.__class__.family)
        config.family = self.family.name
        
        self.__class__.langs = self.family.langs.keys()
        self.__class__.langs = sorted([x for x in config.usernames[self.family.name].keys() if x in self.__class__.langs])
        try:
            self.__class__.langs.insert(0, self.__class__.langs.pop(self.__class__.langs.index(u'en')))
        except ValueError:
            pass
        if langs: self.langs = [x for x in langs if x in self.__class__.langs]
        
        self.wikis = {}
        for lang in self.langs:
            self.wikis[lang] = wiki = Wiki(lang, self.family)
            if wiki.logged_in():
                output('Logged in to \03{lightaqua}%s\03{default}' % wiki)
            else:
                wiki.login()
            
        if types: self.types = [x for x in types if x in self.__class_.types]
        
    @property
    def current_page(self):
        return self._current_page
        
    @current_page.setter
    def current_page(self, page):
        if page != self._current_page:
            self._current_page = page
            if len(self.langs) == 1:
                output(u'\r\n\r\n>>> \03{lightpurple}%s\03{default} <<<'
                       % (page.title()))
            else:
                output(u'\r\n\r\n>>> \03{lightaqua}%s\03{default} : \03{lightpurple}%s\03{default} <<<'
                       % (page.site.code, page.title()))
    
    def getWikiList(self, region = None, locale = None):
        res = []
        for lang in self.langs:
            wiki = self.wikis[lang]
            if region and wiki.region != region: continue
            if locale and wiki.locale != locale: continue
            res.append(wiki)
        return res
    
    def printTable(self, type):
        output('\03{lightyellow}  Wiki     Region    Locale        Old  New\03{default}')
        for wiki in self.getWikiList():
            old = wiki.getVersion(type)
            new = wiki.realm['n'][type]
            
            output('  \03{lightaqua}%(wiki)-5s\03{default}    %(region)-6s    %(locale)-6s    %(color)s%(old)7s  %(new)-7s\03{default}' % {
                'wiki':    wiki.lang,
                'region':  wiki.region,
                'locale':  wiki.locale,
                'old':     old,
                'new':     new,
                'color':   '\03{lightred}' if wiki.needsUpdateTo(type, new) else '\03{lightgreen}'
            })
    
    def userPut(self, *args, **kwargs):
        if self.getOption('protect'): kwargs['async'] = False
        return super(Bot, self).userPut(*args, **kwargs)
    
    def run(self): # override parent
        pass
    
class Wiki(pywikibot.site.APISite):
    __initialized = None
    versionModule = 'Module:Lolwikibot/%s'
    def __new__(cls, *args, **kwargs):
        wiki = pywikibot.Site(*args, **kwargs)
        if not isinstance(wiki, cls):
            wiki.__class__ = cls
        return wiki
    def __init__(self, *args, **kwargs):
        if self.__initialized: return
        self.__initialized = True
        
        self.region = None
        self.locale = None
        self.protectLevel = None
        self._realm = None
        self.comments = {}
        self.versions = {}
        self.other = {}
        
        try:
            self.region = self.mediawiki_message('custom-lolwikibot-region').strip().lower()
            if self.region == '': raise ValueError
        except (ValueError, KeyError):
            output('Notice: \03{lightaqua}%s\03{default} doesn\'t have a region specified - assuming NA' % self)
            self.region = 'na'
        
        try:
            self.locale = self.mediawiki_message('custom-lolwikibot-locale').strip()
            if self.locale == '': raise ValueError
            match = re.match('([a-z]{2})[ _]([a-z]{2})', self.locale.lower())
            if not match: raise ValueError('malformed')
            self.locale = '%s_%s' % (match.group(1), match.group(2).upper())
        except (ValueError, KeyError):
            self.locale = self.realm['l']
            output('Notice: \03{lightaqua}%s\03{default} doesn\'t have a locale specified - assuming region default: %s' % (self, self.locale))
        
        try:
            self.protectLevel = self.mediawiki_message('custom-lolwikibot-protect').strip().lower()
            if self.protectLevel == '': raise ValueError
        except (ValueError, KeyError):
            pass
    
    @property
    def realm(self):
        if not self._realm:
            self._realm = api.realm(self.region)
        return self._realm
    
    def needsUpdateTo(self, type, version):
        if not isinstance(version, StrictVersion):
            version = StrictVersion(version)
        old = self.getVersion(type)
        return not old or old < version
    
    def getVersion(self, type):
        if type not in self.versions:
            try:
                match = re.search(r'(?:^|\n)\s*return\s*\{\s*(\'|")([0-9]+\.[0-9]+\.[0-9]+)\1\s*\}', pywikibot.Page(self, self.versionModule % type).get())
                self.versions[type] = StrictVersion(match.group(2))
                
            except (NoPage, AttributeError):
                self.versions[type] = None
        return self.versions[type]
        
    def saveVersion(self, type, version):
        version = str(version)
        
        page = pywikibot.Page(self, self.versionModule % type)
        
        summary = twtranslate(self, 'lolwikibot-version-summary')
        
        if self.saveData(page, version, summary = summary, comments = 'version', fallback = False):
            self.versions[type] = version
        
    def fetchData(self, page, suppress = False):
        if page.namespace() != 828:
            raise ValueError('%s needs to be in Module namespace' % page.title(asLink = True))
        if not suppress: output('Fetching data from %s' % page.title(asLink = True))
        
        data = loads(self.expand_text('{{#invoke:lolwikibot|dumpModule|%s}}' % page.title(withNamespace = False), title = page.title()))
        if 'error' in data:
            raise LuaError(data['error'])
        
        return numKeys(data)
        
    def saveData(self, page, newdata, comments = '', fallback = True, **kwargs):
        if not isinstance(page, pywikibot.page.BasePage):
            page = pywikibot.Page(self, page)
        Bot().current_page = page
        
        if isinstance(newdata, (basestring, int, float)):
            newdata = [newdata]
        
        intro, outro = self.moduleComments(comments, fallback)
        
        if isinstance(newdata, list):
            res = self._saveList(page, newdata, intro = intro, outro = outro, **kwargs)
        else:
            res = self._saveDict(page, newdata, intro = intro, outro = outro, **kwargs)
        
        if Bot().getOption('protect') and page.exists():
            self.protectModule(page)
        
        return res
    
    def _saveList(self, page, newdata, intro = '', outro = '', order = None, summary = None):
        olddata = None
        oldtext = ''
        
        if page.exists():
            olddata = self.fetchData(page)
            oldtext = page.get()
            
            changed = olddata != newdata
            
            if not changed:
                summary = twtranslate(self, 'lolwikibot-commentsonly-summary')
        
        newtext = (u'%s\n\nreturn %s\n\n%s' % (intro, lua.dumps(newdata), outro)).strip()
        
        return Bot().userPut(page, oldtext, newtext, summary = summary)
    
    def _saveDict(self, page, newdata, intro = '', outro = '', order = None, summary = None):
        newver = newdata.get('update', None)
        oldver = None
        
        olddata = None
        oldtext = ''
        if page.exists():
            olddata = self.fetchData(page)
            oldtext = page.get()
            oldver = olddata.get('update', None)
            if oldver:
                output('Current version: \03{lightyellow}%s\03{default}' % oldver)
        
        keys = OrderedSet()
        added = OrderedSet()
        
        if order:
            for k in order:
                if k in newdata:
                    keys.add(k)
                elif olddata and k in olddata:
                    added.add(k)
        
        for k in sorted(newdata.keys()):
            keys.add(k)
        
        if olddata:
            for k in sorted(olddata.keys()):
                if k not in newdata:
                    added.add(k)
            
            if newver and oldver:
                if StrictVersion(oldver) > StrictVersion(newver): raise VersionConflict(oldver, newver)
                newdata['update'] = oldver
            
            changed = addMissing(olddata, newdata)
            
            if not changed:
                summary = twtranslate(self, 'lolwikibot-commentsonly-summary')
            elif newver:
                newdata['update'] = newver
            oldtext = page.get()
        
        dump = []
        for k in keys:
            dump += [(k, newdata[k])]
        dump += [None]
        dump += twtranslate(self, 'lolwikibot-division-line-comment').split('\n')
        dump += [None]
        for k in added:
            dump += [(k, newdata[k])]
        
        newtext = lua.ordered_dumps(dump)
        
        newtext = (u'%s\n\nreturn %s\n\n%s' % (intro, newtext, outro)).strip()
        
        return Bot().userPut(page, oldtext, newtext, summary = summary)
        
    def protectModule(self, page):
        if self.protectLevel and 'edit' in page.applicable_protections():
            current = page.protection()
            if 'edit' in current and current['edit'][0] == self.protectLevel and 'move' in current and current['move'][0] == self.protectLevel: return
            output(u'Protecting %s' % page.title(asLink=True))
            reason = twtranslate(self, 'lolwikibot-protect-summary')
            self.protect(page, {'edit':self.protectLevel,'move':self.protectLevel}, reason)
        
    def moduleComments(self, type = '', fallback = True):
        if type not in self.comments:
            from lua import commentify
            
            intro = None
            outro = None
            
            # Type-specific
            if type != '':
                try:
                    intro = self.mediawiki_message('custom-lolwikibot-module-intro-%s' % type).strip()
                    intro = commentify(intro)
                except KeyError:
                    intro = None
                try:
                    outro = self.mediawiki_message('custom-lolwikibot-module-outro-%s' % type).strip()
                    outro = commentify(outro)
                except KeyError:
                    outro = None
            
            # Default
            if fallback or type == '':
                if not intro:
                    try:
                        intro = self.mediawiki_message('custom-lolwikibot-module-intro').strip()
                        intro = commentify(intro)
                    except KeyError:
                        intro = ''
                if not outro:
                    try:
                        outro = self.mediawiki_message('custom-lolwikibot-module-outro').strip()
                        outro = commentify(outro)
                    except KeyError:
                        outro = ''
            self.comments[type] = (intro or '', outro or '')
        return self.comments[type]
        
    def subpageOf(self, page, subpage):
        if not isinstance(page, pywikibot.Page):
            page = pywikibot.Page(self, page)
        try:
            page = page.getRedirectTarget()
        except pywikibot.exceptions.IsNotRedirectPage:
            pass
        return pywikibot.Page(self, '%s/%s' % (page.title(), subpage))

class VersionConflict(Exception):
    def __init__(self, old, new):
        self.old = old
        if not isinstance(old, StrictVersion):
            self.old = StrictVersion(old)
        else:
            self.old = old
        if not isinstance(new, StrictVersion):
            self.new = StrictVersion(new)
        else:
            self.new = new
    def __str__(self):
        return '%s => %s' % (self.old, self.new)

class LuaError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value