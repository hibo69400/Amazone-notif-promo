"""Diagnostic : redirection vers Amazon, offres expirées, autres catégories."""
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (compatible; promo-notif-bot/1.0; +https://github.com/hibo69400/Amazone-notif-promo)"
H = {"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"}
NS = {"pepper": "http://www.pepper.com/rss"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=25) as r:
        return r.read().decode("utf-8", "replace")


opener = urllib.request.build_opener(NoRedirect)
for u in ["https://www.dealabs.com/visit/threadmain/3457304", "https://www.dealabs.com/visit/thread/3457304"]:
    try:
        r = opener.open(urllib.request.Request(u, headers=H), timeout=25)
        print("VISIT", u, r.status, r.headers.get("Location"))
    except urllib.error.HTTPError as e:
        print("VISIT", u, e.code, e.headers.get("Location"))
    except Exception as e:  # noqa: BLE001
        print("VISIT", u, "ERREUR", e)

root = ET.fromstring(get("https://www.dealabs.com/rss/groupe/beaba").encode())
old = root.findall("./channel/item")[-1].findtext("link")
for link in [old, "https://www.dealabs.com/bons-plans/dyson-v8-origin-aspirateur-balai-sans-fil-puissant-3457304"]:
    s = get(link)
    head = s[:s.find("thread-price") + 1500] if "thread-price" in s else s[:3000]
    print("\n##### ", link, len(s), "| position thread-price:", s.find("thread-price"))
    for key in ["xpir", "Expir", "termin", "threadItemCard-price"]:
        ms = list(re.finditer(key, head))
        print(f"[{key}] {len(ms)} avant/pres du prix principal")
        for m in ms[:3]:
            print("    ", repr(head[max(0, m.start() - 160):m.start() + 200]))

for slug in """bijoux montres parfums soin-du-visage soins-du-visage cosmetiques sport sports-plein-air cuisine
petit-electromenager gros-electromenager aspirateurs aspirateurs-robots machines-a-cafe friteuses sieges-auto
poussettes lisseurs seche-cheveux chaussures sneakers sous-vetements maison-habitat famille-enfants
sante-beaute sante-et-cosmetiques vetements-homme vetements-femme bebe jouets hygiene soins-du-corps""".split():
    try:
        root = ET.fromstring(get(f"https://www.dealabs.com/rss/groupe/{slug}").encode())
        items = root.findall("./channel/item")
        d = [i.findtext("pubDate")[5:22] for i in items]
        print(f"{slug:24} OK items={len(items)} {d[:1]} ... {d[-1:]}")
    except Exception as e:  # noqa: BLE001
        print(f"{slug:24} {e}")
    time.sleep(0.3)
