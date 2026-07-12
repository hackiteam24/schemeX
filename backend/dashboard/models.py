# Dashboard statistics are computed on demand (see dashboard/views.py) rather
# than stored in a dedicated table. Persisting counts that must be kept in
# sync with Users/Applications/Documents on every change is a common source
# of stale-data bugs; a live aggregate query is cheap and always correct.
# If usage grows large enough that the aggregate becomes slow, introduce a
# periodically-refreshed DashboardSnapshot model at that point.
