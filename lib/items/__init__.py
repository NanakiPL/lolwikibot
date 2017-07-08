# -*- coding: utf-8 -*-

datatype = 'item'

import items, lists

def update(wikis, version):
    items.update(wikis, version)
    
    lists.aliases(wikis, version)
    
def topVersion(wikis, version):
    lists.updatesList(wikis, version)