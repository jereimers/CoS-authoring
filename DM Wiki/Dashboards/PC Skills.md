---
tags:
  - dashboard
  - dm-tool
publish:
---
```dataview
TABLE WITHOUT ID
  file.link as "PC",
  skill_proficiencies as "Skills"
FROM "Player Wiki/Player Characters"
WHERE type = "PC"
SORT file.name ASC
```
