---
tags:
  - dashboard
  - dm-tool
  - npc-reference
publish: false
---

# NPC Directory

> **Comprehensive NPC reference organized by location, faction, and status**

---

## 🔍 Quick Filters

### All NPCs (Alphabetical)
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  region as "Region",
  current_location as "Location",
  factions as "Faction",
  status as "Status",
  first_appearance_session as "First Seen"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
SORT file.name ASC
```

---

## 📍 NPCs by Region

### Town of Vallaki
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  factions as "Faction",
  status as "Status",
  motivations as "Motivations",
  emotions as "Current Emotions"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND region = "Vallaki"
SORT file.name ASC
```

### Village of Barovia
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  factions as "Faction",
  status as "Status",
  home_base as "Home"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND region = "Barovia"
SORT file.name ASC
```

### Castle Ravenloft
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  factions as "Faction",
  status as "Status",
  cr as "CR"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND region = "Ravenloft"
SORT file.name ASC
```

### Krezk
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  factions as "Faction",
  status as "Status"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND region = "Krezk"
SORT file.name ASC
```

### Mount Ghakis
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  status as "Status",
  threat_level as "Threat"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND region = "Mount Ghakis"
SORT file.name ASC
```

### Wilderness
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  home_base as "Home Base",
  status as "Status"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND region = "Wilderness"
SORT current_location ASC, file.name ASC
```

---

## 🎭 NPCs by Faction

### Keepers of the Feather
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  region as "Region",
  current_location as "Location",
  status as "Status",
  motivations as "Motivations"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
  AND contains(factions, "Keepers of the Feather")
SORT file.name ASC
```

### Wachter Family
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  status as "Status",
  motivations as "Motivations"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
  AND (contains(factions, "Wachter") OR contains(file.name, "Wachter"))
SORT file.name ASC
```

### Vallakovich Family
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  status as "Status",
  motivations as "Motivations"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
  AND (contains(factions, "Vallakovich") OR contains(file.name, "Vallakovich"))
SORT file.name ASC
```

### All Factions (Summary)
```dataview
TABLE WITHOUT ID
  factions as "Faction",
  length(rows.file.link) as "NPC Count"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND factions != null
FLATTEN factions
GROUP BY factions
SORT factions ASC
```

---

## 💀 NPCs by Status

### Alive
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  region as "Region",
  current_location as "Location",
  factions as "Faction",
  first_appearance_session as "First Seen"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND status = "alive"
SORT file.name ASC
```

### Dead
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  region as "Region",
  current_location as "Last Known Location",
  factions as "Faction"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND status = "dead"
SORT file.name ASC
```

### Undead
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  region as "Region",
  current_location as "Location",
  cr as "CR"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND status = "undead"
SORT file.name ASC
```

### Unknown/Other Status
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  status as "Status",
  region as "Region",
  current_location as "Location"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
  AND status != "alive"
  AND status != "dead"
  AND status != "undead"
  AND status != null
SORT status ASC, file.name ASC
```

---

## 🎲 NPCs by Challenge Rating

### High Threat (CR 5+)
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  cr as "CR",
  region as "Region",
  current_location as "Location",
  status as "Status"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND cr >= 5
SORT cr DESC
```

### Medium Threat (CR 1-4)
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  cr as "CR",
  region as "Region",
  current_location as "Location",
  status as "Status"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND cr >= 1 AND cr < 5
SORT cr DESC
```

### Low Threat (CR < 1)
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  cr as "CR",
  region as "Region",
  current_location as "Location",
  status as "Status"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND cr < 1 AND cr != null
SORT cr DESC
```

---

## 📅 NPCs by First Appearance

### Recently Introduced (Last 3 Sessions)
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  first_appearance_session as "Session",
  region as "Region",
  current_location as "Location",
  factions as "Faction"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND first_appearance_session >= 10
SORT first_appearance_session DESC
```

### By Session
```dataview
TABLE WITHOUT ID
  first_appearance_session as "Session",
  length(rows.file.link) as "NPCs Introduced"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND first_appearance_session != null
GROUP BY first_appearance_session
SORT first_appearance_session DESC
```

---

## 🎭 Roleplay Quick Reference

### NPCs with Full Roleplay Properties
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  region as "Region",
  motivations as "Motivations",
  emotions as "Emotions",
  inspirations as "Character Inspirations"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
  AND motivations != null
  AND motivations != ""
  AND emotions != null
  AND emotions != ""
SORT file.name ASC
```

### NPCs with Resonance Defined
```dataview
LIST resonance
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
  AND resonance != null
  AND resonance != ""
SORT file.name ASC
```

### NPCs Missing Roleplay Properties (Need Backfill)
```dataview
LIST
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
  AND (motivations = null OR motivations = "")
SORT file.name ASC
```

---

## 📊 Statistics

**Total NPCs:**
```dataview
TABLE WITHOUT ID
  length(rows) as "Total NPC Count"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
```

**NPCs by Region:**
```dataview
TABLE WITHOUT ID
  region as "Region",
  length(rows) as "Count"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
GROUP BY region
SORT region ASC
```

**NPCs by Status:**
```dataview
TABLE WITHOUT ID
  status as "Status",
  length(rows) as "Count"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
GROUP BY status
SORT status ASC
```
