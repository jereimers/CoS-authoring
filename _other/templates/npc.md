---
# CORE ID
npc: true                 # handy boolean for Dataview filters
name: "NPC Name"
aliases:
  - "Alias One"
  - "Alias Two"
pronouns: "he/him"        # or she/her, they/them, etc.
race: "Human"
class: "Wizard"
age: 18
gender: "male"
creature_type: "humanoid" # or undead, fiend, etc.

# WORLD + STORY CONTEXT
origin: "[[Location or Region]]"
home_base: "[[Primary Location]]"
current_location: "[[Where They Are Now]]"
factions:
  - "[[Faction or Family A]]"
  - "[[Faction or Group B]]"
arc:
  - "[[Arc X - Title]]"
  - "[[Arc Y - Other Arc]]"
first_appearance_session: 7
first_appearance_date: "3 Neyavr 735"   # or whatever Barovian calendar
status: "alive"          # alive | dead | undead | missing | unknown
role_in_story: "Major NPC"   # minor, major, villain, quest-giver, etc.

# MECHANICAL STUFF
statblock_source: "CoS p. 231"       # or "Homebrew"
cr: 5
spellcasting:
  class: "wizard"
  level: 5
  spellbook_contains:
    - "sending"
    - "fear"
  spellbook_missing:
    - "remove curse"

# ROLEPLAYING HANDLE
resonance: >
  One- or two-sentence reminder of how the NPC should feel to the players.
emotions:
  - "curious"
  - "frustrated"
  - "anxious"
motivations:
  - "Primary driving goal"
  - "Secondary goal or fear"
inspirations:
  - "Name (Source)"
  - "Name (Source)"
vocal_notes: >
  Short description of voice, cadence, physical tics.

signature_lines:
  - "Favorite line or catchphrase."
  - "Another line you might improv from."

# RELATIONSHIPS
relationships:
  - name: "[[Other NPC 1]]"
    relation: "father"
    attitude: "strained"
    notes: "Brief description of dynamic."
  - name: "[[Other NPC 2]]"
    relation: "friend"
    attitude: "deeply loyal"
    notes: "Brief description of dynamic."

# KNOWLEDGE & CLUES
knowledge_topics:
  - topic: "[[Arabelle]]"
    category: "quest hook"
    summary: >
      One-line summary of what this NPC can tell the PCs about this topic.
  - topic: "[[Amber Temple]]"
    category: "lore"
    summary: >
      One-line summary of what they know or think they know.

# VISUALS / ASSETS
portrait: "IMG-somefile.png"     # filename in your images dir
portrait_credit: "Artist name / source"
handouts:
  - "[[Letter from Victor]]"
  - "Victor's Notes.png"

# TAGS
tags:
  - "npc"
  - "cos"
  - "vallaki"
---
