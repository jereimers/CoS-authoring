TABLE barovian_date, primary_location, act, arc, sessions
FROM "Timeline/Days"
WHERE type = "barovian_day"
SORT barovian_date_key ASC