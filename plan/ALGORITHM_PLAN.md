# Plan: Scheduling Algorithm Design (Question 2 — School Visit Tracker)

## Context

Requirements/data-analysis for this task were already established in an earlier planning pass (500 schools in `schools.csv`, 120 team members in `team members.csv`, both with an empty `Nov 1...Nov 30` grid to be filled in), and written up at `plan/REQUIREMENTS.md`. Its key facts are recapped below for convenience.

Now that the requirements are settled, this plan designs the actual **scheduling algorithm** — the concrete, deterministic procedure that walks school-by-school and day-by-day to populate both output grids, following the exact flow the user specified:

> pick a school → start from week 1 → mark a visit on a day → go to member view → for that date, scroll to the next free member slot → put the school assignment

## Recap of governing facts (from prior analysis)

- **500 schools**: Daily (50), Weekly (173), Two days a week (50), Once in two weeks (177), Monthly (50).
- **Category**: Regular (Mon–Sat, 431 schools) vs Vidya Jyoti/VJ (Mon–Fri, 69 schools) — 11 schools are both Daily + VJ.
- **120 team members**, no location data for either members or schools (round-robin/index-based assignment is the only option — no travel-distance optimization possible).
- **Reference calendar**: a hypothetical month where **Nov 1 = Monday** (simplifies reasoning — no need to anchor to a real year). Each week is a clean Mon–Sun block: Week 1 = Nov 1–7, Week 2 = Nov 8–14, Week 3 = Nov 15–21, Week 4 = Nov 22–28, tail = Nov 29–30 (Mon–Tue, no Sat/Sun in it). Sundays fall on 7/14/21/28; Saturdays on 6/13/20/27. This gives **26 Regular (Mon–Sat) operating days** and **22 VJ (Mon–Fri) operating days** in the month.
- Resolved earlier: idle days for flexible members are fine (not filled with buffer visits); VJ-daily members are idle on Saturday; School Shift column is descriptive only and ignored by the algorithm.
- Output split: `team members.csv` gets the **school code** per member per day; `schools.csv` gets a **`V`** marker per school per day.

## Step 0 — Pre-formatting (both grids initialized before any assignment)

1. For every date in Nov 1–30 that is a **Sunday**, mark `'-'` in *both* views for *all* rows (schools and members) — nobody works Sundays.
2. For every **VJ school**, additionally mark `'-'` on all **Saturdays** in the **school view only** (the school is shut; this does not touch the member view, since a VJ-dedicated member's Saturday idleness is a consequence of having no school to visit, handled naturally in Step 1, and flexible members remain free to work Saturdays at Regular schools).

## Step 1 — Week/cycle definition

Using the Mon–Sun weeks defined above (Weeks 1–4 = Nov 1–28, plus a Mon–Tue tail on Nov 29–30):

- **Weekly** schools → 1 visit in each of the 4 full weeks (tail unused) → 173 × 4 = **692** visits.
- **Two days a week** schools → 2 visits in each of the 4 full weeks (tail unused) → 50 × 8 = **400** visits.
- **Once in two weeks** schools → 1 visit per fortnight, Weeks 1+2 = fortnight A, Weeks 3+4 = fortnight B (tail unused) → 177 × 2 = **354** visits.
- **Monthly** schools → 1 visit anywhere in Nov 1–30 (tail is fair game here) → 50 × 1 = **50** visits.
- **Daily** schools → every operating day of the month (handled separately in Step 3, not week-based) → 39 Regular × 26 + 11 VJ × 22 = **1,256** visits.

**Total demand ≈ 2,752 visits.** Capacity = 120 members × 26 Regular operating days = **3,120 member-days → ~88.2% utilization**, feasible. Daily schools consume 50 dedicated members; the remaining 450 schools need 1,496 visits from the 70-member flexible pool against 70 × 26 = 1,820 member-days (**~82.2% utilization**) — comfortable slack, consistent with the "allow idle days" resolution.

## Step 2 — Member pools (deterministic, reproducible)

- **Dedicated pool**: Team Member IDs 1–50, mapped 1:1 in order to the 50 Daily schools (in the order they appear in `schools.csv`).
- **Flexible pool**: Team Member IDs 51–120 (70 members), available for all non-Daily schools.
- Maintain `used[date] = set of flexible member IDs already assigned on that date`.
- **`next_free_member(date)`**: scan the flexible pool in fixed ID order (51, 52, ... 120) and return the first ID not in `used[date]`. This is the "scroll to next free member slot" step.

## Step 3 — Daily schools (fixed 1:1, no member-scanning needed)

For each of the 50 Daily schools (in file order) paired with dedicated members 1–50 (in order):
- Operating days = Nov 1–30 minus Sundays, minus Saturdays if the school is VJ.
- On every operating day: `member_view[member][day] = school_code`, `school_view[school][day] = 'V'`.
- On every non-operating day for that school (Sunday always, + Saturday if VJ): `member_view[member][day] = '-'` (dedicated member idle, per resolved conflict — the school view is already `'-'` from Step 0).

## Step 4 — Non-Daily schools: the core assignment loop

Process frequency groups **in this order**: Weekly → Two days a week → Once in two weeks → Monthly (matches the user's specified sequence). Within each group, iterate schools in their original `schools.csv` order.

For each school, track `last_weekday` (the weekday of its most recent scheduled visit; `None` initially). For each required visit (in cycle order — week 1, then week 2, etc., or fortnight A/B, or the single monthly visit):

1. **Determine the candidate window** — the days in the current week/fortnight/month window, excluding Sundays and (if VJ) Saturdays.
2. **Rank candidate days**: prefer the earliest day in the window whose weekday ≠ `last_weekday` (satisfies requirement 5 — no repeat weekday back-to-back). To avoid every school in a frequency group piling onto the same day (day 1 of each window) and starving the flexible pool, **stagger the starting candidate by the school's index within its frequency group** (`offset = school_index % num_eligible_days_in_window`), then walk forward from that offset.
3. **Find a free member** for the top-ranked candidate day via `next_free_member(date)` and assign — `member_view[member][date] = school_code`, `school_view[school][date] = 'V'`, add member to `used[date]`, set `last_weekday = weekday(date)`. (Given ~82% flexible-pool utilization headroom, a window ever having zero free members across all its eligible days is not a realistic case, so no fallback/relaxation logic is needed here.)
4. Move to the next window/cycle for this school and repeat.

## Step 5 — Output population

- `schools.csv`: for each school row, days already have `'V'` or `'-'` from Steps 0/3/4; any day untouched by an assignment stays blank (no visit due that day, school open but not scheduled).
- `team members.csv`: for each member row, dedicated members (1–50) are fully populated from Step 3 (`school_code` or `'-'`); flexible members (51–120) get `school_code` on days they were assigned via Step 4, `'-'` on Sundays (Step 0), and blank on any day they had no assignment (idle, per the resolved "allow idle capacity" decision).

## Step 6 — Validation pass (run after generation, before calling it done)

- Every school's total `'V'` count for the month matches its expected visit count for its frequency (Daily = operating days; Weekly = 4; Two days a week = 8; Once in two weeks = 2; Monthly = 1).
- No member has two different school codes on the same date.
- No school has two consecutive scheduled visits on the same weekday.
- No assignment falls on a school's closed day (Sunday for all; Saturday for VJ).

## Implementation notes

- Language: Python (plain `csv`/`dict` handling — both CSVs are simple enough not to need pandas).
- Deliverables: the scheduling script itself, the two populated CSVs, and the validation report from Step 6 — all committed together so the logic and its output are traceable.
- `plan/REQUIREMENTS.md` documents the hypothetical-month convention (Nov 1 = Monday, 26/22 operating days, ~2,752 total visits) used in this plan, so the two documents agree.

## Verification

- Run the script end-to-end on the two provided CSVs and inspect a handful of schools by hand (one Daily, one Weekly, one Two-days-a-week, one Once-in-two-weeks, one Monthly, one VJ) to confirm the visit pattern matches the rules.
- Run the Step 6 validation checks programmatically and confirm zero violations.
- Spot-check that Sundays and VJ-Saturdays are correctly blank/`'-'` in both views.

## Result (implemented in `scheduler.py`)

Built and run against the two source CSVs. Output: `schools_schedule.csv`, `team_members_schedule.csv`. Both views agree on total visits (2,752), 0 scheduling shortfalls, 0 validation violations (visit counts per frequency, no closed-day writes, no consecutive same-weekday repeats).

## Known limitation / future improvement

`next_free_member(date)` (Step 2) always scans the flexible pool starting from member ID 51 and returns the first free one. This means lower IDs get picked far more often than higher ones: in the actual run, members 116–120 sit idle 15 of their 26 working days each, while others are booked almost solid. Every stated rule is still satisfied (nothing in the requirements demands even workload), but it's an unrealistic real-world schedule — field staff would notice the imbalance.

**Fix (deferred, not implemented):** make the scan start from a rotating pointer instead of always ID 51 — e.g. advance a `last_start_index` each time a member is assigned, or round-robin the starting offset per calendar day — so assignments spread evenly across all 70 flexible members over the month. Left as a future improvement rather than blocking the current deliverable.
