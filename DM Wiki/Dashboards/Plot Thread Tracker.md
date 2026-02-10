---
tags:
  - dashboard
  - dm-tool
  - plot-tracker
publish: false
---

# Plot Thread Tracker

> **Track active quests, storylines, and narrative threads across sessions**

---

## ⚡ Active Plot Threads

### Active Quests
```dataview
TABLE WITHOUT ID
  file.link as "Quest",
  giver as "Quest Giver",
  locations as "Location",
  NPCs_involved as "NPCs Involved"
FROM "Player Wiki/Quests"
WHERE status = "active"
SORT file.name ASC
```

### Planning/Upcoming Quests
```dataview
TABLE WITHOUT ID
  file.link as "Quest",
  giver as "Quest Giver",
  locations as "Location",
  status as "Status"
FROM "Player Wiki/Quests"
WHERE status = "planning"
SORT file.name ASC
```

---

## ✅ Completed Quests
```dataview
TABLE WITHOUT ID
  file.link as "Quest",
  giver as "Quest Giver",
  locations as "Location"
FROM "Player Wiki/Quests"
WHERE status = "complete" OR status = "completed"
SORT file.name ASC
```

---

## 📖 Recent Session Plot Developments

### Last 5 Sessions - New Threads
```dataview
TABLE WITHOUT ID
  file.link as "Session",
  play_date as "Date",
  plot_threads_introduced as "New Threads Introduced"
FROM "Player Wiki/Session Recaps"
WHERE plot_threads_introduced != null AND plot_threads_introduced != ""
SORT file.name DESC
LIMIT 5
```

### Last 5 Sessions - Advanced Threads
```dataview
TABLE WITHOUT ID
  file.link as "Session",
  play_date as "Date",
  plot_threads_advanced as "Threads Advanced"
FROM "Player Wiki/Session Recaps"
WHERE plot_threads_advanced != null AND plot_threads_advanced != ""
SORT file.name DESC
LIMIT 5
```

---

## 🎭 Quests by Quest Giver

```dataview
TABLE WITHOUT ID
  giver as "Quest Giver",
  file.link as "Quest",
  status as "Status",
  locations as "Location"
FROM "Player Wiki/Quests"
WHERE giver != null
SORT giver ASC, file.name ASC
```

---

## 📍 Quests by Location

### Vallaki Quests
```dataview
TABLE WITHOUT ID
  file.link as "Quest",
  giver as "Quest Giver",
  status as "Status",
  NPCs_involved as "NPCs Involved"
FROM "Player Wiki/Quests"
WHERE contains(locations, "Vallaki")
SORT status ASC, file.name ASC
```

### Barovia Quests
```dataview
TABLE WITHOUT ID
  file.link as "Quest",
  giver as "Quest Giver",
  status as "Status",
  NPCs_involved as "NPCs Involved"
FROM "Player Wiki/Quests"
WHERE contains(locations, "Barovia")
SORT status ASC, file.name ASC
```

### Other Locations
```dataview
TABLE WITHOUT ID
  file.link as "Quest",
  locations as "Location",
  giver as "Quest Giver",
  status as "Status"
FROM "Player Wiki/Quests"
WHERE !contains(locations, "Vallaki")
  AND !contains(locations, "Barovia")
  AND locations != null
SORT locations ASC, file.name ASC
```

---

## 🎯 Quest Status Overview

```dataview
TABLE WITHOUT ID
  status as "Status",
  length(rows) as "Quest Count"
FROM "Player Wiki/Quests"
GROUP BY status
SORT status ASC
```

---

## 🧵 All Quests (Full List)

```dataview
TABLE WITHOUT ID
  file.link as "Quest",
  status as "Status",
  giver as "Quest Giver",
  locations as "Location",
  NPCs_involved as "NPCs Involved",
  arcs as "Associated Arcs"
FROM "Player Wiki/Quests"
SORT status ASC, file.name ASC
```

---

## 🔍 Quest Gaps & TODOs

### Quests Missing Location Info
```dataview
LIST
FROM "Player Wiki/Quests"
WHERE (locations = null OR locations = "")
SORT file.name ASC
```

### Quests Missing Quest Giver
```dataview
LIST
FROM "Player Wiki/Quests"
WHERE giver = null OR giver = ""
SORT file.name ASC
```

### Quests Without Status
```dataview
LIST
FROM "Player Wiki/Quests"
WHERE status = null OR status = ""
SORT file.name ASC
```

### Quests Not Linked to Arcs
```dataview
LIST
FROM "Player Wiki/Quests"
WHERE arcs = null OR arcs = ""
SORT file.name ASC
```

---

## 📊 Quest Statistics

**Total Quests:**
```dataview
TABLE WITHOUT ID
  length(rows) as "Total Quest Count"
FROM "Player Wiki/Quests"
```

**Quests by Status:**
```dataview
TABLE WITHOUT ID
  status as "Status",
  length(rows) as "Count"
FROM "Player Wiki/Quests"
GROUP BY status
SORT length(rows) DESC
```

---

## 🗺️ Campaign Arc Progression

### Active Arcs (from Recent Sessions)
```dataview
TABLE WITHOUT ID
  arcs as "Arc",
  length(rows.file.link) as "Sessions"
FROM "Player Wiki/Session Recaps"
WHERE arcs
FLATTEN arcs as active_arc
GROUP BY active_arc
SORT length(rows.file.link) DESC
LIMIT 10
```

### Session-by-Session Arc Progression
```dataview
TABLE WITHOUT ID
  file.link as "Session",
  play_date as "Date",
  arcs as "Arcs"
FROM "Player Wiki/Session Recaps"
SORT file.name ASC
```
