# Requirements & Constraints: School Visit Scheduler (November)

## 1. Purpose

Labhya runs classroom observations across 500 partner schools in Tripura, using a 120-member field team. Each school has an assigned visit frequency, and schools operate on different weekly calendars (Mon–Fri vs Mon–Sat). This document captures the requirements, data structure, assumptions, and known gaps needed to design and build an automated monthly visit scheduler. It is meant to be used as the spec for the next step (algorithm design + implementation) — no scheduling logic is implemented here.

## 2. Data Structure

### `schools.csv` (500 rows)

| Column | Description | Observed values |
|---|---|---|
| School Code | Unique school ID | 500 unique codes |
| School Name | School name | Free text, not unique (many schools share names) |
| School Type | **Visit frequency** | Daily (50), Weekly (173), Two days a week (50), Once in two weeks (177), Monthly (50) |
| Sch type - reg/VJ | Operating calendar | Regular school, Mon–Sat (431) / Vidya Jyoti (VJ) school, Mon–Fri (69) |
| School Shift | Single/Double shift | Single (240), Double (259), 1 blank (code `1692736479`, Aarohan Vidyalaya) — descriptive metadata only, does not affect visit count |
| Nov 1 ... Nov 30 | Output grid, currently empty | To be filled with `V` on days a visit is scheduled |

Frequency × category cross-tab confirms **11 schools are both Daily and VJ** (Mon–Fri only) — flagged below as a scheduling edge case.

### `team members.csv` (120 rows)

| Column | Description |
|---|---|
| Team Member | ID 1–120 |
| Nov 1 ... Nov 30 | Output grid, currently empty. To be filled with the **school code** the member visits that day (this is the sheet the field team actually reads to plan their day) |

No other attributes exist — no name, zone, or location/geography field for either schools or members.

### Reference calendar

No year is specified for "November" in the prework, and pinning to a real year adds no value here, so we use a **hypothetical month where Nov 1 = Monday**:
- Clean Mon–Sun weeks: Week 1 = Nov 1–7, Week 2 = Nov 8–14, Week 3 = Nov 15–21, Week 4 = Nov 22–28, tail = Nov 29–30 (Mon–Tue, no weekend in it)
- Sundays: 7, 14, 21, 28. Saturdays: 6, 13, 20, 27.
- 26 Mon–Sat operating days (Regular schools), 22 Mon–Fri operating days (VJ schools)

This is a stated assumption, not a hard requirement — the actual scheduler should treat the reference calendar as a parameter.

## 3. Requirements

1. Every school is visited exactly according to its assigned frequency in November (Daily / Weekly / Two days a week / Once in two weeks / Monthly).
2. A field member visits at most **one school per day**.
3. Members assigned to a **Daily**-frequency school are dedicated **1:1** to that single school for the entire month (50 members ↔ 50 Daily schools).
4. The remaining **70 "flexible" members** are not tied to one school — they cover the other 450 schools (Weekly / Two days a week / Once in two weeks / Monthly), potentially different schools on different days of the week.
5. Repeat visits to the same school must **not fall on the same weekday twice in a row** — e.g. if visited Monday this cycle, the next visit must land on a different weekday. Applies to all repeat frequencies (not Daily, where every operating day is visited anyway).
6. Field members work Monday–Saturday; VJ schools are open Monday–Friday only, Regular schools Monday–Saturday.

## 4. Resolved Assumptions & Conflicts

- **Output format**: two distinct deliverables, not mirrored grids.
  - `team members.csv` — for each member × day, the **school code** visited (primary sheet for field team planning).
  - `schools.csv` — for each school × day, a **`V`** marker when a visit is scheduled (no member identity needed here).
- **Idle capacity vs. "all 120 members visit every day"**: Total real demand from the 70 flexible members (~1,496 visits/month, see §5) is *less* than their available capacity (70 × 25 = 1,750 member-days). We do **not** manufacture filler/buffer visits to force every day to be booked. "All 120 members make visits every day" is interpreted as *on duty*, not *booked solid* — unassigned member-days are simply left blank/idle.
- **Daily + VJ schools' Saturdays (11 schools)**: these schools are shut on Saturday, so their dedicated member has nothing to visit that day. Resolution: the member is idle on Saturday rather than being temporarily reassigned into the flexible pool.
- **School Shift column**: confirmed descriptive-only; a Double Shift school does not require two visits.

## 5. Known Gap (documented, not resolved)

**No geography/location/cluster data exists** for either schools or members (no district, cluster, lat/long, or "home base" field). This means the scheduler **cannot** optimize field-member-to-school assignment by travel distance or proximity — any grouping of flexible members to schools will necessarily be arbitrary (e.g., by school-code order or round-robin), not geography-aware. This is a limitation of the provided data, not of the scheduling design, and should be stated plainly in any writeup or dashboard built on top of this.

## 6. Feasibility Snapshot (hypothetical Nov-1-is-Monday reference calendar)

| Frequency | Schools | Est. visits/month |
|---|---|---|
| Daily | 50 | 1,256 (39 Regular × 26 + 11 VJ × 22) |
| Weekly | 173 | 692 |
| Two days a week | 50 | 400 |
| Once in two weeks | 177 | 354 |
| Monthly | 50 | 50 |
| **Total** | **500** | **~2,752** |

- Total field-member-day capacity: 120 × 26 = **3,120** → ~88.2% overall utilization. The ask is feasible with a 120-person team.
- Daily schools (50) fully consume 50 dedicated members.
- Remaining 450 schools need ~1,496 visits from 70 flexible members against 1,820 available member-days (~82.2% utilization) — comfortable slack, consistent with the "allow idle days" resolution in §4.

## 7. Open for Next Step

Not covered by this document — to be addressed in algorithm design:
- Concrete day-by-day assignment logic for the 70 flexible members across 450 schools, respecting the weekday-rotation rule (§3.5) and one-visit-per-member-per-day (§3.2).
- How to group/batch schools for flexible members in the absence of geography data (§5) — e.g. a simple deterministic partitioning scheme.
- Exact output generation (populating the two CSV grids) and any validation checks (e.g. confirming every school hit its required visit count, no member double-booked).
