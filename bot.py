# -*- coding: utf-8  -*-
import pywikibot, re, api
from pywikibot import bot, config
from pywikibot.exceptions import UserBlocked, UserRightsError, NoPage, IsNotRedirectPage, LockedPage

from distutils.version import LooseVersion

class Bot(bot.Bot):
    family = None
    wikis = {}
    
    options = {
        'always': False,
    }
    
    def __init__(self, family):
        self.family = pywikibot.family.Family.load(family)
        config.family = family = self.family.name
        config.mylang = None
        
        langs = self.family.langs.keys()
        langs = sorted([x for x in config.usernames[family].keys() if x in langs])
        try:
            langs.insert(0, langs.pop(langs.index(u'en')))
        except ValueError:
            pass
        
        for lang in langs:
            self.wikis[lang] = wiki = pywikibot.Site(lang, family)
            wiki.__class__ = Wiki
            wiki.reInit()
            
            print('')
            print(lang)
            print(wiki)
            
            print(wiki.getVersion('champion'))
        print(self.wikis)

realms = {}

class Wiki(pywikibot.site.APISite):
    def reInit(self):
        self.region = None
        self.locale = None
        self.comments = {}
        self.versions = {}
        
        try:
            self.region = self.mediawiki_message('custom-lolwikibot-region').strip().lower()
            if self.region == '': raise ValueError
        except (ValueError, KeyError):
            pywikibot.output('Notice: \03{lightaqua}%s\03{default} doesn\'t have a region specified - assuming NA' % self)
            self.region = 'na'
        
        try:
            self.locale = self.mediawiki_message('custom-lolwikibot-locale').strip()
            if self.locale == '': raise ValueError
            match = re.match('([a-z]{2})[ _]([a-z]{2})', self.locale.lower())
            if not match: raise ValueError('malformed')
            self.locale = '%s_%s' % (match.group(1), match.group(2).upper())
        except (ValueError, KeyError):
            self.locale = api.realm(self.region)['l']
            pywikibot.output('Notice: \03{lightaqua}%s\03{default} doesn\'t have a locale specified - assuming region default: %s' % (self, self.locale))
    
    def getVersion(self, type):
        if type not in self.versions:
            try:
                match = re.search('^\s*return\s*\{\s*\'([0-9]+\.[0-9]+\.[0-9]+)\'\s*\}', pywikibot.Page(self, 'Module:Lolwikibot/%s' % type).get())
                self.versions[type] = LooseVersion(match.group(1))
            except NoPage, AttributeError:
                self.versions[type] = None
        return self.versions[type]
    
    def moduleComments(self, type = ''):
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
                if intro == None or outro == None:
                    i, o = self.moduleComments()
                    intro = i if intro == None else intro
                    outro = o if outro == None else outro
                self.comments[type] = (intro, outro)
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
        
        
bot = Bot('lol')
    
if __name__ == '__main__':
    pass