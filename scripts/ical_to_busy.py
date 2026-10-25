"""Turn the Airbnb calendar export (iCal) into busy.json for the website.

Reads the iCal URL from the AIRBNB_ICAL environment variable (a GitHub secret)
and writes busy.json with booked or blocked nights as [start, end) date pairs.
No guest names or other details are written.
"""
import datetime, json, os, re, urllib.request

url = os.environ.get("AIRBNB_ICAL", "").strip()
if not url:
    raise SystemExit("AIRBNB_ICAL is not set")
req = urllib.request.Request(url, headers={"User-Agent": "casalafonte-availability"})
text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
text = re.sub(r"\r?\n[ \t]", "", text)  # unfold long lines

def day(v):
    v = v.strip()[:8]
    return datetime.date(int(v[:4]), int(v[4:6]), int(v[6:8]))

spans = []
for ev in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
    s = re.search(r"^DTSTART[^:]*:(\d{8})", ev, re.M)
    e = re.search(r"^DTEND[^:]*:(\d{8})", ev, re.M)
    if s and e:
        a, b = day(s.group(1)), day(e.group(1))
        if b > a:
            spans.append([a, b])

spans.sort()
merged = []
for a, b in spans:
    if merged and a <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], b)
    else:
        merged.append([a, b])

today = datetime.date.today()
out = {
    "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"),
    "busy": [[a.isoformat(), b.isoformat()] for a, b in merged if b >= today],
}
new = json.dumps(out, indent=0)
old = open("busy.json").read() if os.path.exists("busy.json") else ""
try:
    same = json.loads(old).get("busy") == out["busy"]
except Exception:
    same = False
if not same:
    open("busy.json", "w").write(new + "\n")
    print("busy.json updated:", len(out["busy"]), "spans")
else:
    print("no change")
