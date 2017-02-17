local MODULE = 'Champion' -- Name of this page

local arguments = {
    ['1'] = 'name',
}

local function getKey(key)
    key = tonumber(key) or key
    
    local keys = mw.loadData('Module:' .. MODULE .. '/keys')
    new = keys[key]
    
    if new then
        return new
    end
    return key
end

local function handleKeyError(s, e)
    if s then return e end
    if e.type == 'invalid key' then
        return '<span class="error">'..mw.message.new('custom-lolwikibot-invalid-champion', e.key):plain()..'</span>'
    end
    error(e, 0)
end

local Champion = {}

function Champion.new(key)
    local new = getKey(key)
    mw.log('New champ: ' .. new .. ' ('.. key ..')')
    local obj = setmetatable({}, Champion)
    obj.key = new
    obj._data = setmetatable({}, {__index=function(self,key)
        mw.log(key)
        obj:fetch(key)
        return rawget(self, key)
    end})
    return obj
end



function Champion.__index(self, key)
    if Champion[key] then return Champion[key] end
    return self._data[key]
end

function Champion:p(...)
    local res = {}
    mw.log('a', #arg)
    for i,key in ipairs(arg) do
        key = arguments[key] or key
        res[i] = nil
        key = mw.text.trim(key or '', '%.%s')
        if key ~= '' then
            res[i] = self
            key = mw.text.split(key, '%s*%.%s*')
            for j,v in ipairs(key) do
                if type(res[i]) == 'table' then
                    res[i] = res[i][v]
                else
                    res[i] = nil
                end
            end
        end
    end
    mw.log('r', #res)
    return unpack(res)
end
local function flatten(data)
    local res = {}
    for k1,v1 in pairs(data) do
        if type(v1) == 'table' then
            if v1[1] then
                local l = {}
                for i,v in ipairs(v1) do
                    l[i] = v
                end
                res[k1] = table.concat(l, ';')
            else
                local subres = flatten(v1)
                for k2,v2 in pairs(subres) do
                    res[k1 .. '.' .. k2] = v2
                end
            end
        else
            res[k1] = v1
        end
    end
    return res
end
function Champion:flat(raw)
    raw = not not raw
    self:fetch()
    local res = flatten(self._data)
    if raw then return res end
    local res2 = {}
    
    for k,v in pairs(arguments) do
        if res[v] then
            res2[k] = res[v]
            res[v] = nil
        end
    end
    for k,v in pairs(res) do
        res2[k] = v
    end
    
    for k,v in pairs(res2) do mw.log(k) end
    return res2
end

function Champion:fetch(...)
    local s, e = pcall(function(self)
        local data = mw.loadData('Module:' .. MODULE .. '/' .. self.key)
        for k,v in pairs(data) do
            self._data[k] = v
        end
    end, self)
    if not s then
        error({type='invalid key', key = self.key})
    end
    return self
end


local champs, p = {}, {}
function p.get(key)
    if not champs[key] then
        old = key
        key = getKey(key)
        if not champs[key] then
            champs[key] = Champion.new(key)
        end
        if old ~= key then champs[old] = champs[key] end
    end
    return champs[key]
end

function p.param(frame)
    return handleKeyError(pcall(function(frame)
        champ = Champion.new(mw.text.trim(frame.args[1]))
        res = champ:p(frame.args[2])
        return res
    end, frame))
end
function p.params(frame)
    return handleKeyError(pcall(function(frame)
        champ = Champion.new(mw.text.trim(frame.args[1]))
        params = {}
        for i,v in ipairs(frame.args) do
            if i > 1 then
                table.insert(params, v)
            end
        end
        
        params = {champ:p(unpack(params))}
        
        if frame.args['expr'] then
            expr = mw.text.trim(frame.args['expr']) .. ' '
            for i,v in ipairs(params) do
                expr = mw.ustring.gsub(expr, '%%' .. i .. '([^0-9])', v .. '%1')
            end
            return mw.ext.ParserFunctions.expr(expr)
        end
        if frame.args['format'] then
            f = mw.text.trim(frame.args['format'])
            mw.log(f)
            f = mw.ustring.format(f, unpack(params))
            mw.log(f)
            return f
        end
        sep = frame.args['separator']
        if sep then
            mw.text.trim(sep)
            if sep == '' then
                sep = ' '
            end
        end
        return table.concat(params, sep or ', ')
    end, frame))
end
function p.template(frame)
    return handleKeyError(pcall(function(frame)
        champ = Champion.new(mw.text.trim(frame.args[1] or ''))
        tpl = mw.text.trim(frame.args[2] or '')
        
        local args = champ:flat()
        for k,v in pairs(frame.args) do
            if type(k) == 'string' then
                args[k] = v
            end
        end
        for k,v in pairs(frame:getParent().args) do
            if type(k) == 'string' then
                args[k] = v
            end
        end
        
        s, res = pcall(function(frame, title, args)
            return frame:expandTemplate{ title = title, args = args }
        end, frame, tpl, args)
        if s then
            return res
        else
            return '[[' .. mw.title.new(tpl, 'Template').prefixedText .. ']]'
        end
    end, frame))
end
function p.keys(frame)
    return handleKeyError(pcall(function(frame)
        local fn = require('Module:Filename')
        local champs = mw.loadData('Module:' .. MODULE .. '/list/name')['list']
        local aliases = {}
        local o = {}
        
        for k,v in pairs(champs) do
            table.insert(o, k)
            aliases[k] = {}
        end
        
        local keys = mw.loadData('Module:' .. MODULE .. '/keys')
        for k,v in pairs(keys) do
            if k ~= champs[v]['name'] and k ~= champs[v]['id'] then
                table.insert(aliases[v], '<code>' .. k .. '</code>')
            end
        end
        
        table.sort(o, function(a, b) return champs[a]['name']<champs[b]['name'] end)
        mw.log(table.concat(o, '\n'))
        
        local res = {}
        for i,k in ipairs(o) do
            local champ = champs[k]
            local row = {}
            table.insert(row, '| [[File:' .. fn.character{champ['name']} .. '|x26px|link=]]')
            table.insert(row, '| [[' .. champ['name'] .. ']]')
            table.insert(row, '| <code>' .. k .. '</code>')
            table.insert(row, '| ' .. champ['id'])
            table.insert(row, '| ' .. table.concat(aliases[k], ', '))
            table.insert(res, table.concat(row, '\n'))
        end
        
        return '|-\n' .. table.concat(res, '\n|-\n') .. '\n|-'
    end, frame))
end

return p