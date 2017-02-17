# -*- coding: utf-8 -*-
"""
This family file was auto-generated by $Id$
Configuration parameters:
  url = http://nanaki.wikia.com
  name = lol

Please do not commit this to the Git repository!
"""

from pywikibot import family
from pywikibot.tools import deprecated


class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'lol'
        self.langs = {
            'en': 'nanaki.wikia.com',
            'pl': 'pl.leagueoflegends.wikia.com',
        }

    def scriptpath(self, code):
        return ''

    @deprecated('APISite.version()')
    def version(self, code):
        return u'1.19.24'
