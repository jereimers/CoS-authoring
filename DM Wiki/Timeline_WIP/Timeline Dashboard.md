---
type: dashboard
tags:
  - dashboard/timeline
---

# Barovian Timeline Dashboard

> [!info]
> This dashboard shows all in-game days, ordered chronologically, and for each day
> pulls in linked scenes / sessions via Dataview.

## 📅 Full Timeline of Days

```dataviewjs
TABLE
  barovian_date AS "Date",
  barovian_year AS "Year",
  barovian_month AS "Month",
  barovian_day AS "Day",
  join(sessions, ", ") AS "Sessions"
FROM "Timeline/Days"
WHERE type = "timeline-day"
SORT barovian_index ASC```
