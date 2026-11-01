"""Twice-daily calendar check for Casa La Fonte (run by .github/workflows/calendar-check.yml).

Reads the iCal exports of each channel (Airbnb, Vrbo, later Booking.com) from GitHub secrets and
checks that no two channels hold a reservation on the same night, and that every reservation is
blocked on every other channel. Any problem makes the job fail, so GitHub emails the owner.
Only dates are read; no guest details are printed.
"""
import datetime, os, re, sys, urllib.request

FEEDS = {"Airbnb": "AIRBNB_ICAL", "Vrbo": "VRBO_ICAL", "Booking.com": "BOOKING_ICAL"}
GRACE_HOURS = 6   # a block may take a few hours to appear on the other channels

def day(v):
    v = v.strip()[:8]
    return datetime.date(int(v[:4]), int(v[4:6]), int(v[6:8]))

def events(text):
    text = re.sub(r"\r?\n[ \t]", "", text)
    out = []
    for ev in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        s = re.search(r"^DTSTART[^:]*:(\d{8})", ev, re.M)
        e = re.search(r"^DTEND[^:]*:(\d{8})", ev, re.M)
        summ = (re.search(r"^SUMMARY[^:]*:(.*)$", ev, re.M) or [None, ""])[1].strip()
        stamp = re.search(r"^(?:CREATED|DTSTAMP|LAST-MODIFIED)[^:]*:(\d{8}T\d{6})Z?", ev, re.M)
        if s and e and day(e.group(1)) > day(s.group(1)):
            out.append({"a": day(s.group(1)), "b": day(e.group(1)), "summary": summ,
                        "stamp": datetime.datetime.strptime(stamp.group(1), "%Y%m%dT%H%M%S") if stamp else None})
    return out

def is_reservation(channel, summary):
    s = summary.lower()
    if channel == "Airbnb":
        return s.startswith("reserved")
    if channel == "Vrbo":
        return s.startswith("reserved") or s.startswith("booked")
    return "closed" not in s and "not available" not in s and "blocked" not in s

def nights(a, b):
    d = a
    while d < b:
        yield d
        d += datetime.timedelta(days=1)

today = datetime.date.today()
now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
cal, problems, notes = {}, [], []
for ch, env in FEEDS.items():
    url = os.environ.get(env, "").strip()
    if not url:
        if ch != "Booking.com":
            notes.append(f"{ch}: no calendar link set ({env}), so it was not checked.")
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "casalafonte-calendar-check"})
        cal[ch] = [e for e in events(urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")) if e["b"] > today]
    except Exception as ex:
        problems.append(f"{ch}: the calendar could not be read ({type(ex).__name__}). Check the link.")

blocked = {ch: {n for e in evs for n in nights(e["a"], e["b"])} for ch, evs in cal.items()}
reserved = {ch: {} for ch in cal}
for ch, evs in cal.items():
    for e in evs:
        if is_reservation(ch, e["summary"]):
            for n in nights(e["a"], e["b"]):
                reserved[ch][n] = e

chs = list(cal)
for i, x in enumerate(chs):
    for y in chs[i + 1:]:
        both = sorted(set(reserved[x]) & set(reserved[y]))
        if both:
            problems.append(f"DOUBLE BOOKING: {x} and {y} both have a reservation on {len(both)} night(s), first {both[0].isoformat()}. Contact both guests and the platforms now.")

for x in chs:
    seen = set()
    for n, e in sorted(reserved[x].items()):
        if id(e) in seen:
            continue
        for y in chs:
            if y == x:
                continue
            missing = [m for m in nights(e["a"], e["b"]) if m not in blocked[y]]
            fresh = e["stamp"] and (now - e["stamp"]).total_seconds() < GRACE_HOURS * 3600
            if missing and not fresh:
                seen.add(id(e))
                problems.append(f"NOT BLOCKED: the {x} reservation {e['a'].isoformat()} – {e['b'].isoformat()} is still open on {y} ({len(missing)} night(s)). Block those dates on {y} now.")

print(f"Calendar check {now.isoformat(timespec='minutes')}Z — channels read: {', '.join(chs) or 'none'}")
for n in notes:
    print("Note:", n)
for p in problems:
    print("PROBLEM:", p)
summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    with open(summary, "a") as f:
        f.write("## Casa La Fonte calendar check\n\n" + ("\n".join(f"- **{p}**" for p in problems) or "- All calendars agree.") + "\n" + "".join(f"- {n}\n" for n in notes))
if not cal:
    sys.exit("No calendar could be read.")
if problems:
    sys.exit(f"{len(problems)} calendar problem(s) found — see above.")
print("All calendars agree.")
