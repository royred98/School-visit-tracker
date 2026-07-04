# School Visit Tracker

An automated monthly (November) classroom-observation visit scheduler for 500 partner schools in Tripura, covered by a 120-member field team. Built for Labhya's Data Engineer prework (Question 2).

Given each school's assigned visit frequency and operating calendar, the scheduler produces a day-by-day schedule showing which field member visits which school, while respecting all stated constraints (frequency, one-visit-per-member-per-day, weekday rotation, dedicated vs. flexible member pools).

## Repo structure

```
dataset/    Source CSVs (schools + team members) — the given input data
plan/       Requirements analysis and algorithm design docs
output/     Generated schedule CSVs (produced by scheduler.py)
scheduler.py  The scheduling script
```

- **`plan/REQUIREMENTS.md`** — data structure, requirements, resolved assumptions/conflicts, and feasibility analysis.
- **`plan/ALGORITHM_PLAN.md`** — the step-by-step scheduling algorithm design, plus known limitations.
- **`scheduler.py`** — reads the two dataset CSVs and generates the schedule.
- **`output/schools_schedule.csv`** — school × day grid; `V` marks a scheduled visit, `-` marks a closed day (Sunday for all, Saturday for Vidya Jyoti schools).
- **`output/team_members_schedule.csv`** — member × day grid; each cell holds the school code the member visits that day (this is the sheet a field team member reads to plan their day).

## Running it

```bash
python3 scheduler.py
```

Requires only the Python standard library (no dependencies). Re-running regenerates both files in `output/` and prints a validation summary (visit-count checks, closed-day checks, weekday-rotation checks).

## Key assumptions

- Reference calendar: a hypothetical month where Nov 1 falls on a Monday (see `plan/REQUIREMENTS.md` for details).
- No location/geography data exists in the source CSVs, so flexible field members are assigned to schools deterministically (by index), not by travel distance.
- Idle days for flexible members are allowed — the schedule doesn't manufacture filler visits just to fill every day.

Full rationale for these and other decisions is in `plan/REQUIREMENTS.md` and `plan/ALGORITHM_PLAN.md`.
