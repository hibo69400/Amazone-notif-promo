"""Diagnostic : flux par marque et contenu d'une page d'offre."""
import re
import time
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (compatible; promo-notif-bot/1.0; +https://github.com/hibo69400/Amazone-notif-promo)"
NS = {"pepper": "http://www.pepper.com/rss"}
SLUGS = """beaba cybex maxi-cosi kinderkraft chicco joie bosch samsung roborock ecovacs ninja tefal zwilling
moulinex cosori delonghi de-longhi krups dyson nespresso karcher hugo-boss boss nike under-armour adidas
calvin-klein lacoste swarovski fossil amazon-essentials real-techniques maybelline l-oreal loreal l-oreal-paris
nyx nyx-professional-makeup erborian ghd color-wow biodance medicube kerastase olaplex
mode vetements beaute sante-cosmetiques mode-accessoires maquillage soin-des-cheveux amazon""".split()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.read()


first_amazon_link = None
for slug in SLUGS:
    url = f"https://www.dealabs.com/rss/groupe/{slug}"
    try:
        status, body = get(url)
        root = ET.fromstring(body)
        items = root.findall("./channel/item")
        amz = [i for i in items if "amazon" in (i.find("pepper:merchant", NS).attrib.get("name", "") if i.find("pepper:merchant", NS) is not None else "").lower()]
        dates = [i.findtext("pubDate")[5:22] for i in items]
        print(f"{slug:28} {status} items={len(items):2} amazon={len(amz):2} | {root.findtext('./channel/title')[:50]} | {dates[:3]} ... {dates[-1:] }")
        if amz and first_amazon_link is None and slug == "dyson":
            first_amazon_link = amz[0].findtext("link")
    except Exception as e:  # noqa: BLE001
        print(f"{slug:28} ERREUR {e}")
    time.sleep(0.4)

for link in [first_amazon_link, "https://www.dealabs.com/bons-plans/krups-sensation-lait-machine-espresso-automatique-compacte-15-bars-3458106"]:
    if not link:
        continue
    print("\n##### page offre", link)
    try:
        status, body = get(link)
        s = body.decode("utf-8", "replace")
        print(status, len(s))
        for key in ["nextBestPrice", "\"price\"", "percentage", "displayPrice", "priceDiscount", "amazon.fr", "threadId", "isExpired", "visit/thread"]:
            for m in list(re.finditer(re.escape(key), s))[:3]:
                print(f"  [{key}] ...{s[max(0, m.start()-150):m.start()+250]!r}")
    except Exception as e:  # noqa: BLE001
        print("ERREUR", e)
