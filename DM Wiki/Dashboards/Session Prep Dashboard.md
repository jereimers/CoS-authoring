---
tags:
  - dashboard
  - dm-tool
publish: false
---

# Session Prep Dashboard

> **Quick reference for session planning and live play**

---

## 📅 Current Session

```dataview
TABLE WITHOUT ID
  file.link as "Session",
  play_date as "Played",
  barovian_dates as "In-Game Date",
  locations as "Locations",
  arcs as "Arcs"
FROM "Player Wiki/Session Recaps" OR "DM Wiki/Sessions"
WHERE type = "session" OR contains(file.folder, "Session")
SORT file.name DESC
LIMIT 1
```

### Next Session Planning

```dataview
TABLE WITHOUT ID
  file.link as "Session Notes",
  file.mtime as "Last Modified"
FROM "DM Wiki/Sessions/Notes"
SORT file.mtime DESC
LIMIT 3
```

---

## 🎭 Active Story Arcs

**Recent Sessions' Arcs:**
```dataview
TABLE WITHOUT ID
  file.link as "Session",
  arcs as "Arcs Active"
FROM "Player Wiki/Session Recaps"
WHERE arcs
SORT file.name DESC
LIMIT 5
```

---

## 👥 NPCs by Region

### NPCs in Vallaki
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  factions as "Faction",
  motivations as "Motivations"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND region = "Vallaki"
SORT file.name ASC
```

### NPCs in Barovia (Village)
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  factions as "Faction",
  status as "Status"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND region = "Barovia"
SORT file.name ASC
```

### NPCs in Castle Ravenloft
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  current_location as "Location",
  status as "Status",
  cr as "CR"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC" AND region = "Ravenloft"
SORT file.name ASC
```

### Recently Introduced NPCs
```dataview
TABLE WITHOUT ID
  file.link as "NPC",
  first_appearance_session as "Session",
  region as "Region",
  current_location as "Location",
  status as "Status"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
  AND first_appearance_session >= 8
SORT first_appearance_session DESC
```

---

## ⚔️ Active Quests

```dataview
TABLE WITHOUT ID
  file.link as "Quest",
  giver as "Quest Giver",
  locations as "Location",
  NPCs_involved as "NPCs Involved",
  status as "Status"
FROM "Player Wiki/Quests"
WHERE status = "active" OR status = "planning"
SORT file.name ASC
```

---

## 📍 Key Locations

### Areas the Party Has Visited
```dataview
TABLE WITHOUT ID
  file.link as "Location",
  first_appearance_session as "First Visit",
  notable_npcs as "Notable NPCs",
  threat_level as "Threat Level"
FROM "DM Wiki/Entities/Areas"
WHERE type = "Area" AND first_appearance_session != null
SORT first_appearance_session DESC
LIMIT 10
```

---

## 🧵 Recent Plot Threads

### From Last 3 Sessions
```dataview
TABLE WITHOUT ID
  file.link as "Session",
  plot_threads_introduced as "New Threads",
  plot_threads_advanced as "Advanced Threads"
FROM "Player Wiki/Session Recaps"
WHERE plot_threads_introduced OR plot_threads_advanced
SORT file.name DESC
LIMIT 3
```

---

## 📖 Recent Session Recaps

```dataview
TABLE WITHOUT ID
  file.link as "Session",
  play_date as "Date Played",
  barovian_dates as "Barovian Date",
  combat as "Combat?",
  NPCs_met as "NPCs Met"
FROM "Player Wiki/Session Recaps"
SORT file.name DESC
LIMIT 5
```

---

## 🎲 Quick Reference

### NPCs by Status
```dataview
TABLE WITHOUT ID
  status as "Status",
  length(rows) as "Count"
FROM "DM Wiki/Entities/NPCs"
WHERE type = "NPC"
GROUP BY status
SORT status ASC
```

### Factions in Play
```dataview
LIST
FROM "DM Wiki/Entities/Factions"
WHERE type = "Faction"
SORT file.name ASC
```

---

## 📝 Notes & Reminders

<!-- Add session-specific notes here -->

- [ ] Review last session's recap
- [ ] Prepare NPC voices/mannerisms
- [ ] Review active quest details
- [ ] Check plot thread connections
