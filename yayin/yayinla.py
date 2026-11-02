# Kullanım: python yayinla.py <id>   tek paylaşım
#           python yayinla.py sira   zamanı gelmiş paylaşımlar
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

KOK = pathlib.Path(__file__).resolve().parent
ANA = KOK.parent
IG = "17841451996580897"
GRAPH = "https://graph.facebook.com/v24.0/"
TABAN = (KOK / "medya-url.txt").read_text(encoding="utf-8").strip().rstrip("/")
TOKEN = os.environ.get("IG_TOKEN") or [s.split("=", 1)[1].strip() for s in (ANA / ".env").read_text(encoding="utf-8-sig").splitlines() if s.startswith("IG_TOKEN=")][0]
KAYIT = KOK / "kayit.json"


def istek(yol, veri=None):
    govde = urllib.parse.urlencode(veri).encode() if veri is not None else None
    r = urllib.request.Request(GRAPH + yol, data=govde, headers={"Authorization": "Bearer " + TOKEN})
    try:
        with urllib.request.urlopen(r, timeout=120) as c:
            return json.load(c)
    except urllib.error.HTTPError as e:
        hata = json.loads(e.read() or b"{}").get("error", {})
        raise SystemExit(f"Instagram hatası {e.code}: {hata.get('error_user_msg') or hata.get('message')}")


def bekle(kap, sure=300):
    son = time.time() + sure
    while time.time() < son:
        d = istek(f"{kap}?fields=status_code,status")
        if d.get("status_code") == "FINISHED":
            return
        if d.get("status_code") in ("ERROR", "EXPIRED"):
            raise SystemExit(f"Medya işlenemedi: {d.get('status')}")
        time.sleep(5)
    raise SystemExit("Medya zamanında işlenmedi")


def yayinla(k):
    MEDYA = k.get("taban", TABAN)
    if k["tur"] == "carousel":
        cocuk = []
        for ad in k["dosyalar"]:
            kap = istek(f"{IG}/media", {"image_url": f"{MEDYA}/{ad}", "is_carousel_item": "true"})["id"]
            bekle(kap)
            cocuk.append(kap)
        kap = istek(f"{IG}/media", {"media_type": "CAROUSEL", "children": ",".join(cocuk), "caption": k["aciklama"]})["id"]
    elif k["tur"] == "reels":
        kap = istek(f"{IG}/media", {"media_type": "REELS", "video_url": f"{MEDYA}/{k['dosya']}", "caption": k["aciklama"], "share_to_feed": "true"})["id"]
    else:
        kap = istek(f"{IG}/media", {"media_type": "STORIES", "image_url": f"{MEDYA}/{k['dosya']}"})["id"]
    bekle(kap)
    sonuc = istek(f"{IG}/media_publish", {"creation_id": kap})["id"]
    return istek(f"{sonuc}?fields=id,media_product_type,permalink")


def main():
    takvim = json.loads((KOK / "takvim.json").read_text(encoding="utf-8"))
    kayit = json.loads(KAYIT.read_text(encoding="utf-8")) if KAYIT.exists() else {}
    hedef = sys.argv[1]
    simdi = datetime.datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M")
    for k in takvim:
        if k["id"] in kayit:
            continue
        if (hedef == "sira" and k["zaman"] <= simdi) or k["id"] == hedef:
            s = yayinla(k)
            kayit[k["id"]] = {"zaman": simdi, **s}
            KAYIT.write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")
            print("yayınlandı", k["id"], s.get("permalink", s.get("media_product_type")))


main()
