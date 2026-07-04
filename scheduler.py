"""
School visit scheduler (Question 2).

Reads the two dummy CSVs (schools, team members), builds a November
visit schedule per the rules in plan/REQUIREMENTS.md, and writes:
  - schools_schedule.csv      (school x day -> 'V' / '-' / blank)
  - team_members_schedule.csv (member x day -> school code / '-' / blank)

Reference calendar: a hypothetical month where Nov 1 = Monday.
"""
import csv
from collections import Counter, defaultdict

SCHOOLS_IN = "dataset/Ritabrata Roy_Prework_saharsh_randomised_all_schools - schools.csv"
MEMBERS_IN = "dataset/Ritabrata Roy_Prework_saharsh_randomised_all_schools - team members.csv"
SCHOOLS_OUT = "schools_schedule.csv"
MEMBERS_OUT = "team_members_schedule.csv"

DAYS = list(range(1, 31))
NUM_MEMBERS = 120
NUM_DEDICATED = 50


def weekday(d):
    """0=Mon .. 5=Sat, 6=Sun. Nov 1 = Monday."""
    return (d - 1) % 7


SUNDAYS = [d for d in DAYS if weekday(d) == 6]
SATURDAYS = [d for d in DAYS if weekday(d) == 5]

WEEKS = [
    list(range(1, 8)),
    list(range(8, 15)),
    list(range(15, 22)),
    list(range(22, 29)),
]
TAIL = [29, 30]
FORTNIGHTS = [WEEKS[0] + WEEKS[1], WEEKS[2] + WEEKS[3]]


def load_schools():
    with open(SCHOOLS_IN, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [r[:5] for r in reader if r[0].strip()]
    schools = []
    for code, name, freq, category, shift in rows:
        schools.append({
            "code": code,
            "name": name,
            "freq": freq,
            "is_vj": category.strip() == "Vidya Jyoti school",
        })
    return schools


def eligible_days(window, is_vj):
    closed = set(SUNDAYS) | (set(SATURDAYS) if is_vj else set())
    return [d for d in window if d not in closed]


def operating_days(is_vj):
    closed = set(SUNDAYS) | (set(SATURDAYS) if is_vj else set())
    return [d for d in DAYS if d not in closed]


def rank_candidates(candidates, last_weekday, offset):
    """Rotate the candidate list by `offset`, then prefer days whose
    weekday differs from last_weekday (stable order otherwise)."""
    if not candidates:
        return []
    n = len(candidates)
    rotated = [candidates[(offset + i) % n] for i in range(n)]
    if last_weekday is None:
        return rotated
    preferred = [d for d in rotated if weekday(d) != last_weekday]
    fallback = [d for d in rotated if weekday(d) == last_weekday]
    return preferred + fallback


def build_schedule():
    schools = load_schools()

    school_view = {s["code"]: {d: "" for d in DAYS} for s in schools}
    member_view = {m: {d: "" for d in DAYS} for m in range(1, NUM_MEMBERS + 1)}

    # Step 0: pre-formatting
    for d in SUNDAYS:
        for s in schools:
            school_view[s["code"]][d] = "-"
        for m in range(1, NUM_MEMBERS + 1):
            member_view[m][d] = "-"
    for s in schools:
        if s["is_vj"]:
            for d in SATURDAYS:
                school_view[s["code"]][d] = "-"

    # Step 3: Daily schools -> dedicated members 1..50, in file order
    daily_schools = [s for s in schools if s["freq"] == "Daily"]
    assert len(daily_schools) == NUM_DEDICATED
    for i, s in enumerate(daily_schools):
        member = i + 1
        op_days = operating_days(s["is_vj"])
        for d in DAYS:
            if d in op_days:
                member_view[member][d] = s["code"]
                school_view[s["code"]][d] = "V"
            elif d not in SUNDAYS:  # Saturday closed for this VJ school
                member_view[member][d] = "-"

    # Step 2/4: flexible pool (members 51..120) for non-Daily schools
    flexible_pool = list(range(NUM_DEDICATED + 1, NUM_MEMBERS + 1))
    used = defaultdict(set)  # day -> set of member ids already assigned that day

    def next_free_member(day):
        for m in flexible_pool:
            if m not in used[day]:
                return m
        return None

    def assign(school_code, day, member):
        member_view[member][day] = school_code
        school_view[school_code][day] = "V"
        used[day].add(member)

    freq_groups = ["Weekly", "Two days a week", "Once in two weeks", "Monthly"]
    non_daily_by_freq = {f: [s for s in schools if s["freq"] == f] for f in freq_groups}

    shortfalls = []

    def schedule_school(s, windows, visits_per_window):
        last_weekday = None
        idx_in_group = group_index[s["code"]]
        for window in windows:
            candidates = eligible_days(window, s["is_vj"])
            n = len(candidates) if candidates else 1
            offset = idx_in_group % n
            for _ in range(visits_per_window):
                ranked = rank_candidates(candidates, last_weekday, offset)
                chosen = None
                for day in ranked:
                    m = next_free_member(day)
                    if m is not None:
                        chosen = (day, m)
                        break
                if chosen is None:
                    shortfalls.append((s["code"], window))
                    continue
                day, member = chosen
                assign(s["code"], day, member)
                last_weekday = weekday(day)
                candidates = [d for d in candidates if d != day]
                offset = 0

    # deterministic per-frequency-group index for staggering
    group_index = {}
    for f in freq_groups:
        for i, s in enumerate(non_daily_by_freq[f]):
            group_index[s["code"]] = i

    for s in non_daily_by_freq["Weekly"]:
        schedule_school(s, WEEKS, 1)
    for s in non_daily_by_freq["Two days a week"]:
        schedule_school(s, WEEKS, 2)
    for s in non_daily_by_freq["Once in two weeks"]:
        schedule_school(s, FORTNIGHTS, 1)
    for s in non_daily_by_freq["Monthly"]:
        schedule_school(s, [DAYS], 1)

    return schools, school_view, member_view, shortfalls


def write_outputs(schools, school_view, member_view):
    with open(SCHOOLS_OUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["School Code", "School Name", "School Type", "Sch type - reg/ VJ", "School Shift"]
                         + [f"Nov {d}" for d in DAYS])
        # reload full rows to preserve name/type/shift columns
        with open(SCHOOLS_IN, newline="") as fin:
            reader = csv.reader(fin)
            header = next(reader)
            for row in reader:
                if not row[0].strip():
                    continue
                code = row[0]
                writer.writerow(row[:5] + [school_view[code][d] for d in DAYS])

    with open(MEMBERS_OUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Team Member"] + [f"Nov {d}" for d in DAYS])
        for m in range(1, NUM_MEMBERS + 1):
            writer.writerow([m] + [member_view[m][d] for d in DAYS])


def validate(schools, school_view, member_view):
    problems = []

    expected_visits = {
        "Daily": None,  # varies by category, checked separately
        "Weekly": 4,
        "Two days a week": 8,
        "Once in two weeks": 2,
        "Monthly": 1,
    }

    for s in schools:
        v_count = sum(1 for d in DAYS if school_view[s["code"]][d] == "V")
        if s["freq"] == "Daily":
            expected = len(operating_days(s["is_vj"]))
        else:
            expected = expected_visits[s["freq"]]
        if v_count != expected:
            problems.append(f"{s['code']} ({s['freq']}): expected {expected} visits, got {v_count}")

    # no member double-booked with two different schools same day (not possible by construction,
    # but check no member has >1 non-blank/non-'-' distinct assignment per day is trivially true
    # since member_view[m][d] is a single cell; instead check no closed-day violations)
    for s in schools:
        for d in SUNDAYS:
            if school_view[s["code"]][d] not in ("-",):
                problems.append(f"{s['code']}: non-'-' value on Sunday {d}")
        if s["is_vj"]:
            for d in SATURDAYS:
                if school_view[s["code"]][d] != "-":
                    problems.append(f"{s['code']}: VJ school not marked '-' on Saturday {d}")

    # weekday-repeat check: consecutive 'V' days for a school must differ in weekday
    for s in schools:
        v_days = [d for d in DAYS if school_view[s["code"]][d] == "V"]
        for a, b in zip(v_days, v_days[1:]):
            if s["freq"] != "Daily" and weekday(a) == weekday(b):
                problems.append(f"{s['code']}: consecutive visits on {a} and {b} share weekday")

    return problems


if __name__ == "__main__":
    schools, school_view, member_view, shortfalls = build_schedule()
    write_outputs(schools, school_view, member_view)
    problems = validate(schools, school_view, member_view)

    print(f"Schools: {len(schools)}, shortfalls during scheduling: {len(shortfalls)}")
    if shortfalls:
        print("Shortfalls:", shortfalls[:10])
    print(f"Validation problems: {len(problems)}")
    for p in problems[:20]:
        print(" -", p)
    print(f"\nWrote {SCHOOLS_OUT} and {MEMBERS_OUT}")
