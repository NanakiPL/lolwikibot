-- This module is used by the lolwikibot to read data on this wiki.
 
local lolwikibot = {}
 
function lolwikibot.version(frame)
    local key = mw.text.trim(mw.ustring.lower(frame.args[1] or ''))
    s, res = pcall(function()
        return mw.loadData('Modulelolwikibot' .. key)[1]
    end)
    if s then
        if mw.text.trim(frame.args[2] or '') ~= '' then
            return (mw.ustring.gsub(res, '^([0-9]+.[0-9]+).[0-9]+$', '%1'))
        end
        return res
    end
    return ''
end
 
local json = require('DevJson')
function lolwikibot.dumpModule(frame)
    name = frame.args[1]
    s, data = pcall(function()
        return mw.loadData('Module'..name)
    end)
    if not s then
        data = {['error'] = data}
    end
    return json.encode(data)
end
 
return lolwikibot