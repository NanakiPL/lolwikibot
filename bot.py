# -*- coding: utf-8  -*-
import pywikibot, re, api, lua
from pywikibot import config, output
from pywikibot.bot import Bot
from pywikibot.exceptions import NoPage
from api import LoLException

# i18n
from pywikibot.i18n import twtranslate, set_messages_package
set_messages_package('i18n')

# Other
from distutils.version import StrictVersion
from importlib import import_module

class Bot(Bot):
    family = 'lol'
    
    availableOptions = {
        'always': False,
        'last': False,
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
            'last': False,
        }
        
        self.args = []
        for arg in pywikibot.handle_args():
            if   arg == '-always':                         self.setOptions(always = True)
            elif arg == '-last':                           self.setOptions(last = True)
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
            
        if types: self.types = [x for x in types if x in self.__class_.types]
        
    @property
    def current_page(self):
        return self._current_page
        
    @current_page.setter
    def current_page(self, page):
        if page != self._current_page:
            self._current_page = page
            if len(self.langs) == 1:
                output(u'\n\n>>> \03{lightpurple}%s\03{default} <<<'
                       % (page.title()))
            else:
                output(u'\n\n>>> \03{lightaqua}%s\03{default} : \03{lightpurple}%s\03{default} <<<'
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
            
            output('  \03{lightaqua}%(wiki)-5s\03{default}    %(region)-6s    %(locale)-6s    %(color)s%(old)7s  %(new)-7s\03{default}  %(action)s' % {
                'wiki':    wiki.lang,
                'region':  wiki.region,
                'locale':  wiki.locale,
                'old':     old,
                'new':     new,
                'color':   '\03{lightred}' if wiki.needsUpdateTo(type, new) else '\03{lightgreen}',
                'action':  '' if wiki.needsUpdateTo(type, new) else 'SKIP'
            })
        
    def getWorkList(self, type):
        res = {}
        wikis = self.getWikiList()
        versions = api.versions()
        
        if self.getOption('last'):
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
    
    def run(self):
        if len(self.langs) == 0:
            output('Error: No valid languages to work on')
            self.quit()
        if len(self.types) == 0:
            output('Error: No valid types to work on')
            self.quit()
        for type in self.types:
            try:
                module = import_module(type)
                if not hasattr(module, 'update') or not hasattr(module, 'type'):
                    raise ImportError
            except ImportError:
                continue
            
            output('\r\n\r\n\03{yellow}======  \03{lightyellow}%s  \03{yellow}%s\03{default}\r\n' % (module.__name__.upper(), '='*(50-len(module.__name__))))
            self.printTable(module.type)
            output('\r\n\03{yellow}%s\03{default}' % ('='*(60)))
            
            for version, list in self.getWorkList(module.type):
                output('\r\n  Version: \03{lightyellow}%-10s\03{default}  working on \03{lightyellow}%d\03{default} wiki%s  \03{lightaqua}%s\03{default}' % (version, len(list), ': ' if len(list) == 1 else 's:', '\03{default}, \03{lightaqua}'.join([x.lang for x in list])))
                try:
                    module.update(list, version)
                except LoLException as e:
                    output('API responded with: %s  - skipping this version' % e.error)
                for wiki in list:
                    wiki.other['topVersion'] = str(version)
            
            output('\r\n  Saving info about latest version')
            versions = {}
            for wiki in self.getWikiList():
                v = wiki.other['topVersion']
                if v not in versions: versions[v] = []
                versions[v].append(wiki)
                
            for version, list in sorted(versions.items(), key = lambda x: StrictVersion(x[0])):
                if hasattr(module, 'topVersion'):
                    module.topVersion(list, version)
                for wiki in list:
                    wiki.saveVersion(type, version)

class Wiki(pywikibot.site.APISite):
    versionModule = 'Module:Lolwikibot/%s'
    def __init__(self, *args, **kwargs):
        super(Wiki, self).__init__(*args, **kwargs)
        
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
                match = re.search('^\s*return\s*\{\s*\'([0-9]+\.[0-9]+\.[0-9]+)\'\s*\}', pywikibot.Page(self, self.versionModule % type).get())
                self.versions[type] = StrictVersion(match.group(1))
            except (NoPage, AttributeError):
                self.versions[type] = None
        return self.versions[type]
    
    def saveVersion(self, type, version):
        version = str(version)
        
        page = pywikibot.Page(self, self.versionModule % type)
        
        summary = twtranslate(self, 'lolwikibot-version-summary')
        
        if self.saveData(page, version, summary = summary, fallback = False):
            self.versions[type] = version
        
        if page.exists():
            self.protectModule(page)
    
    def compareModules(self, oldtext, newtext):
        if oldtext == newtext:
            return False # Nothing changed - don't do anything
            
        newtext_i = lua.decomment(newtext).strip()
        oldtext_i = lua.decomment(oldtext).strip()
        
        if oldtext_i == newtext_i:
            return newtext # Only comments changed - update with different summary
        
        p = re.compile('([\{,]\s*\[\s*\'update\'\s*\]\s*=\s*\')([0-9]+\.[0-9]+\.[0-9]+)(\'\s*[,\}])')
        match = p.search(oldtext_i)
        if match:
            oldtext_i = p.sub(ur'\1\3', oldtext_i)
            newtext_i = p.sub(ur'\1\3', newtext_i)
            
            if oldtext_i == newtext_i:
                newnewtext = p.sub(lambda x: '%s%s%s' % (x.group(1), match.group(2), x.group(3)), newtext)
                if oldtext == newnewtext:
                    return False # Version changed. Data and comments same - don't do anything
                return newnewtext # Version and coments changed - update only comments with different summary and keep old version
        return True # Data different - update with regular summary
    
    def saveData(self, page, data, comments = '', order = None, summary = None, fallback = True):
        if not isinstance(page, pywikibot.page.BasePage):
            page = pywikibot.Page(self, page)
        Bot().current_page = page
        
        if isinstance(data, (basestring, int, float)):
            data = [data]
        
        if order:
            newtext = lua.ordered_dumps(data, order)
        else:
            newtext = lua.dumps(data)
        
        intro, outro = self.moduleComments(comments, fallback)
        newtext = (u'%s\n\nreturn %s\n\n%s' % (intro, newtext, outro)).strip()
        
        oldtext = ''
        skip = False
        success = False
        try:
            oldtext = page.get()
            if not isinstance(data, list) and 'update' in data:
                newver = StrictVersion(data['update'])
                p = re.compile('[\{,]\s*\[\s*\'update\'\s*\]\s*=\s*\'([0-9]+\.[0-9]+\.[0-9]+)\'\s*[,\}]')
                match = p.search(lua.decomment(oldtext))
                if match:
                    oldver = StrictVersion(match.group(1))
                    if oldver > newver: raise VersionConflict(oldver, newver)
            res = self.compareModules(oldtext, newtext)
            if res and res != True:
                success = Bot().userPut(page, oldtext, res, summary = twtranslate(self, 'lolwikibot-commentsonly-summary'))
                skip = True
            elif res == False:
                output(u'No changes were needed on %s' % page.title(asLink=True))
                success = None
                skip = True
        except NoPage:
            pass
        if not skip:
            success = Bot().userPut(page, oldtext, newtext, summary = summary)
        
        if page.exists():
            self.protectModule(page)
        
        return success
    
    def protectModule(self, page):
        if self.protectLevel and 'edit' in page.applicable_protections():
            current = page.protection()
            if 'edit' in current and current['edit'][0] == self.protectLevel and 'move' in current and current['move'][0] == self.protectLevel: return
            reason = twtranslate(self, 'lolwikibot-protect-summary')
            print(reason)
            self.protect(page, {'edit':self.protectLevel,'move':self.protectLevel}, reason)
            
            raise Exception('boink')
        
    def moduleComments(self, type = '', fallback = True):
        if type not in self.comments:
            from lua import commentify
            
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
                if fallback and (intro == None or outro == None):
                    i, o = self.moduleComments()
                    intro = i if intro == None else intro
                    outro = o if outro == None else outro
                self.comments[type] = (intro or '', outro or '')
                return self.comments[type]
            
            # Default
            try:
                intro = self.mediawiki_message('custom-lolwikibot-module-intro').strip()
                intro = commentify(intro)
            except KeyError:
                intro = ''
            try:
                outro = self.mediawiki_message('custom-lolwikibot-module-outro').strip()
                outro = commentify(outro)
            except KeyError:
                outro = ''
            self.comments[''] = (intro, outro)
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