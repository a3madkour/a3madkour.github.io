-- d2-blocks.lua — pandoc filter for D.2 multi-export Word backend.
-- Pass 1: numbering; Pass 2: styling.

local family_kinds = { theorem = true, lemma = true, corollary = true,
                       proposition = true, claim = true }
local own_counter_kinds = { definition = 0, remark = 0, example = 0,
                            note = 0, conjecture = 0, axiom = 0 }
local family_counter = 0

-- Map kind → display label (capitalized; same as the kind itself for D.2).
local label_of = {
  theorem = "Theorem", lemma = "Lemma", corollary = "Corollary",
  proposition = "Proposition", definition = "Definition", proof = "Proof",
  remark = "Remark", example = "Example", note = "Note",
  claim = "Claim", conjecture = "Conjecture", axiom = "Axiom",
}

local function header_style(kind)
  return label_of[kind] .. " Header"
end

local function body_style(kind)
  return label_of[kind] .. " Body"
end

local function header_text(kind, num, title)
  local label = label_of[kind]
  if kind == "proof" then return label .. "." end
  if title and title ~= "" then
    return label .. " " .. num .. ": " .. title
  end
  return label .. " " .. num .. "."
end

local function make_header_para(kind, num, title)
  local txt = header_text(kind, num, title)
  local span = pandoc.Span({ pandoc.Str(txt) },
                           pandoc.Attr("", {}, { { "custom-style", header_style(kind) } }))
  return pandoc.Para({ span })
end

local function wrap_body_style(kind, blocks)
  -- Apply the `<Kind> Body' custom-style to each Para in the block list.
  return pandoc.walk_block(pandoc.Div(blocks), {
    Para = function(p)
      local span = pandoc.Span(p.content,
                               pandoc.Attr("", {}, { { "custom-style", body_style(kind) } }))
      return pandoc.Para({ span })
    end,
  }).content
end

function Div(el)
  local kind = el.classes[1]
  if kind == nil or label_of[kind] == nil then return nil end

  local n
  if family_kinds[kind] then
    family_counter = family_counter + 1
    n = family_counter
  elseif own_counter_kinds[kind] ~= nil then
    own_counter_kinds[kind] = own_counter_kinds[kind] + 1
    n = own_counter_kinds[kind]
  elseif kind == "proof" then
    n = nil
  end
  el.attributes["d2-num"] = (n and tostring(n)) or ""

  -- Strip optional surrounding quotes that org #+attr_html passes through.
  local title = (el.attributes["data-title"] or ""):gsub('^"(.*)"$', "%1")
  -- Store the cleaned title so tests can grep for it as a bare JSON string value.
  if title ~= "" then el.attributes["d2-title"] = title end
  local header = make_header_para(kind, n, title)
  local body = wrap_body_style(kind, el.content)

  -- Proof: append ∎ to the last paragraph in body.
  if kind == "proof" and #body > 0 then
    local last = body[#body]
    if last.t == "Para" then
      table.insert(last.content, pandoc.Space())
      table.insert(last.content, pandoc.Str("∎"))
    end
  end

  el.content = { header }
  for _, b in ipairs(body) do table.insert(el.content, b) end
  return el
end
