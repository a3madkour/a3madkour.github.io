-- d2-blocks.lua — pandoc filter for D.2 multi-export Word backend.
-- Pass 1: numbering. Walks Div nodes in document order; attaches `d2-num`
-- attribute per AMS counter convention.

local family_kinds = { theorem = true, lemma = true, corollary = true,
                       proposition = true, claim = true }
local own_counter_kinds = { definition = 0, remark = 0, example = 0,
                            note = 0, conjecture = 0, axiom = 0 }
local family_counter = 0

function Div(el)
  local kind = el.classes[1]
  if kind == nil then return nil end
  local n
  if family_kinds[kind] then
    family_counter = family_counter + 1
    n = family_counter
  elseif own_counter_kinds[kind] ~= nil then
    own_counter_kinds[kind] = own_counter_kinds[kind] + 1
    n = own_counter_kinds[kind]
  elseif kind == "proof" then
    n = nil
  else
    return nil  -- not a D.1 kind; pass through untouched
  end
  el.attributes["d2-num"] = (n and tostring(n)) or ""
  return el
end
