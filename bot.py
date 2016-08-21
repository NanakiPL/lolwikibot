# -*- coding: utf-8  -*-
import pywikibot, re, api, lua
from pywikibot import config, output
from pywikibot.bot import Bot
from pywikibot.exceptions import UserBlocked, UserRightsError, NoPage, IsNotRedirectPage, LockedPage

# i18n
from pywikibot.i18n import twtranslate, set_messages_package
set_messages_package('i18n')

# Other
from distutils.version import StrictVersion
from importlib import import_module

def getTypeModule(type):
    return import_module(type)

class Bot(Bot):
    family = None
    wikis = {}
    
    options = {
        'always': False,
    }
    types = [
        'champions',
        'items',
        'masteries',
        'runes',
        'spells',
    ]
    _save_counter = 0
    
    def __init__(self, family):
        global bot
        bot = self
        
        langs = None
        types = None
        self.sinceVersion = None
        
        for arg in pywikibot.handle_args():
            if   arg == '-always':               self.setOptions(always = True)
            elif arg == '-dryrun':               pywikibot.config.simulate = True
            elif arg.startswith('-langs:'):      langs = arg[7:].split(',')
            elif arg.startswith('-key:'):        api.setKey(arg[5:])
            elif arg.startswith('-since:'):      self.sinceVersion = StrictVersion(arg[7:])
            elif arg.startswith('-types:'):      types = arg[7:].split(',')
        
        self.family = pywikibot.family.Family.load(family)
        config.family = family = self.family.name
        config.mylang = None
        
        self.langs = self.family.langs.keys()
        self.langs = sorted([x for x in config.usernames[family].keys() if x in self.langs])
        try:
            self.langs.insert(0, self.langs.pop(self.langs.index(u'en')))
        except ValueError:
            pass
        if langs: self.langs = [x for x in langs if x in self.langs]
        
        for lang in self.langs:
            self.wikis[lang] = wiki = pywikibot.Site(lang, family)
            wiki.__class__ = Wiki
            wiki.reInit()
            
        if types: self.types = sorted([x for x in types if x in Bot.types])
        types = []
        for type in self.types:
            try:
                m = getTypeModule(type)
                if hasattr(m, 'update') and hasattr(m, 'type'):
                    types.append(m)
            except ImportError:
                pass
        self.types = types
    
    def printTable(self, type):
        output('\03{lightyellow}  Wiki    Region    Locale        Old  New\03{default}')
        for lang in self.langs:
            wiki = self.wikis[lang]
            
            old = wiki.getVersion(type)
            new = wiki.getRealm()['n'][type]
            
            output('  \03{lightaqua}%(wiki)-4s\03{default}    %(region)-6s    %(locale)-6s    %(color)s%(old)7s  %(new)-7s\03{default}  %(action)s' % {
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
        if self.sinceVersion:
            versions = [x for x in api.call('static_get_versions') if StrictVersion(x) >= self.sinceVersion]
            for v in versions:
                if v not in res: res[v] = []
                for lang in self.langs:
                    wiki = self.wikis[lang]
                    if wiki.needsUpdateTo(type, v):
                        res[v].append(wiki)
        else:
            for lang in self.langs:
                wiki = self.wikis[lang]
                v = wiki.getRealm()['n'][type]
                if v not in res: res[v] = []
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
            print(type)
            output('\r\n\r\n\03{yellow}======  \03{lightyellow}%s  \03{yellow}%s\03{default}\r\n' % (type.__name__.upper(), '='*(43-len(type.__name__))))
            self.printTable(type.type)
            output('\r\n\03{yellow}%s\03{default}' % ('='*(53)))
            for version, list in self.getWorkList(type.type):
                pywikibot.output('\r\n  Version: \03{lightyellow}%-10s\03{default}  working on \03{lightyellow}%d\03{default} wiki%s  \03{lightaqua}%s\03{default}' % (version, len(list), ': ' if len(list) == 1 else 's:', '\03{default}, \03{lightaqua}'.join([x.lang for x in list])))
                type.update(list, version)
        
    @property
    def current_page(self):
        return self._current_page
    @current_page.setter
    def current_page(self, page):
        if page != self._current_page:
            self._current_page = page
            output(u'\n\n>>> \03{lightaqua}%s\03{default} : \03{lightpurple}%s\03{default} <<<'
                       % (page.site.lang, page.title()))
    
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
            
            
    def saveModule(self, page, newtext, **kwargs):
        self.current_page = page
        
        oldtext = ''
        try:
            oldtext = page.get()
            res = self.compareModules(oldtext, newtext)
            if res and res != True:
                return bot.userPut(page, oldtext, res, summary = twtranslate(self, 'lolwikibot-commentsonly-summary'))
            elif res == False:
                return output(u'No changes were needed on s%s' % page.title(asLink=True))
        except NoPage:
            pass
        bot.userPut(page, oldtext, newtext, summary = kwargs['summary'])
        
        #TODO: need to return if the save was made
        #TODO: checking and applying protection from MediaWiki:custom-lolwikibot-protect

realms = {}

class Wiki(pywikibot.site.APISite):
    versionModule = 'Module:Lolwikibot/%s'
    def reInit(self):
        self.region = None
        self.locale = None
        self.comments = {}
        self.versions = {}
        
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
            self.locale = self.getRealm()['l']
            output('Notice: \03{lightaqua}%s\03{default} doesn\'t have a locale specified - assuming region default: %s' % (self, self.locale))
    
    def getRealm(self):
        return api.realm(self.region)
    
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
        version = StrictVersion(str(version))
        intro, outro = self.moduleComments('version', False)
        
        page = pywikibot.Page(self, self.versionModule % type)
        newtext = ('%s\n\nreturn {\'%s\'}\n\n%s' % (intro, version, outro)).strip()
        oldtext = page.text
        
        summary = twtranslate(self, 'lolwikibot-version-summary')
        
        if bot.saveModule(page, newtext, summary = summary):
            self.versions[type] = version
        
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
        
        
Bot('lol')
    
if __name__ == '__main__':
    bot.run()
    pass