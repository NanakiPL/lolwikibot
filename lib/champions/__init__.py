# -*- coding: utf-8 -*-

datatype = 'champion'

import champs, lists

def update(wikis, version):
    champs.update(wikis, version)
    lists.update(wikis, version)
    
def topVersion(wikis, version):
    lists.updatesList(wikis, version)