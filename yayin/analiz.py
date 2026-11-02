# Hesap ve paylaşım rakamlarını analiz/ altına yazar. Token çıktıya yazılmaz.
import datetime
import json
import os
import pathlib
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

KOK = pathlib.Path(__file__).resolve().parent
IG = "17841451996580897"
GRAPH = "https://graph.facebook.com/v24.0/"
TOKEN = os.environ.get("IG_TOKEN") or [s.split("=", 1)[1].strip() for s in (KOK.parent / ".env").read_text(encoding="utf-8-sig").splitlines() if s.startswith("IG_TOKEN=")][0]
SIMDI = datetime.datetime.now(ZoneInfo("Europe/Istanbul"))


def al(y):
    r = urllib.request.Request(GRAPH + y, headers={"Authorization": "Bearer " + TOKEN})
    try:
        with urllib.request.urlopen(r, timeout=60) as c:
            return json.load(c)
    except urllib.error.HTTPError as e:
        return {"hata": json.loads(e.read() or b"{}").get("error", {}).get("message", "")[:200]}


hesap = al(f"{IG}?fields=username,followers_count,follows_count,media_count")
medya = al(f"{IG}/media?fields=id,media_type,media_product_type,caption,permalink,timestamp,like_count,comments_count&limit=50").get("data", [])
for m in medya:
    urun = m.get("media_product_type")
    metrik = "reach,saved,shares,total_interactions,views" + (",ig_reels_avg_watch_time,ig_reels_video_view_total_time" if urun == "REELS" else "")
    d = al(f"{m['id']}/insights?metric={metrik}")
    m["istatistik"] = {x["name"]: x["values"][0]["value"] for x in d.get("data", [])} if "data" in d else d
    m["caption"] = (m.get("caption") or "")[:80]
gun = al(f"{IG}/insights?metric=reach,profile_views,follower_count&period=day")
ozet = {"zaman": SIMDI.strftime("%Y-%m-%d %H:%M"), "hesap": hesap, "gunluk": gun.get("data", gun), "medya": medya}
d = KOK / "analiz"
d.mkdir(exist_ok=True)
y = d / (SIMDI.date().isoformat() + ".json")
y.write_text(json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({"hesap": hesap, "gunluk": str(ozet["gunluk"])[:300], "medya": [{k: m.get(k) for k in ("media_product_type", "like_count", "comments_count", "istatistik")} for m in medya]}, ensure_ascii=False))
