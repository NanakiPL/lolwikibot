# -*- coding: utf-8 -*-

datatype = 'champion'

import champs, lists

def update(wikis, version):
    champs.update(wikis, version)
    
    lists.nameList(wikis, version)
    lists.infoList(wikis, version)
    lists.resourceList(wikis, version)
    lists.tagsList(wikis, version)
    lists.statLists(wikis, version)
    lists.aliases(wikis, version)
    lists.skills(wikis, version)
    
def topVersion(wikis, version):
    lists.updatesList(wikis, version)