"""Diagnostic : regarde ce que contiennent les flux, pour les offres Amazon uniquement."""
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter

UA = "Mozilla/5.0 (compatible; promo-notif-bot/1.0; +https://github.com/hibo69400/Amazone-notif-promo)"
NS = {"pepper": "http://www.pepper.com/rss"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.read()


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


for url in ["https://www.dealabs.com/rss/nouveaux", "https://www.dealabs.com/rss/hot",
            "https://www.dealabs.com/rss/nouveaux?page=2"]:
    try:
        status, body = get(url)
    except Exception as e:  # noqa: BLE001
        print(f"\n##### {url} -> ERREUR {e}")
        continue
    items = ET.fromstring(body).findall("./channel/item")
    merchants = Counter()
    print(f"\n##### {url} -> {status}, {len(items)} items")
    shown = 0
    for it in items:
        m = it.find("pepper:merchant", NS)
        attrs = dict(m.attrib) if m is not None else {}
        merchants[attrs.get("name", "?")] += 1
        if "amazon" in attrs.get("name", "").lower() and shown < 8:
            shown += 1
            print("---")
            print("merchant:", attrs)
            print("title:", it.findtext("title"))
            print("link:", it.findtext("link"))
            print("guid:", it.findtext("guid"), "| pubDate:", it.findtext("pubDate"))
            print("cats:", [c.text for c in it.findall("category")])
            print("desc:", text(it.findtext("description"))[:500])
    print("marchands:", merchants.most_common(12))
    if items:
        print("premier pubDate:", items[0].findtext("pubDate"), "| dernier:", items[-1].findtext("pubDate"))

for url in ["https://www.dealabs.com/rss/tag/amazon", "https://www.dealabs.com/rss/marchand/amazon",
            "https://www.dealabs.com/rss/merchant/amazon", "https://www.dealabs.com/rss/bons-plans/amazon",
            "https://www.dealabs.com/rss/groupe/electromenager", "https://www.dealabs.com/rss/groupe/puericulture",
            "https://fr.camelcamelcamel.com/top_drops/feed?t=recent",
            "https://fr.camelcamelcamel.com/top_drops/feed?t=daily&p=2",
            "https://fr.camelcamelcamel.com/top_drops/feed?t=weekly",
            "https://fr.camelcamelcamel.com/top_drops/feed?bn=kitchen",
            "https://fr.camelcamelcamel.com/top_drops/feed?bn=baby",
            "https://fr.camelcamelcamel.com/top_drops/feed?s=relative",
            "https://fr.camelcamelcamel.com/popular.xml",
            "https://fr.camelcamelcamel.com/search?sq=dyson"]:
    try:
        status, body = get(url)
        s = body.decode("utf-8", "replace")
        titles = re.findall(r"<title>(.*?)</title>", s, flags=re.S)
        print(f"\n##### {url} -> {status}, {len(body)} octets, {len(titles)} titres")
        for t in titles[:6]:
            print("   ", t.strip()[:200])
    except Exception as e:  # noqa: BLE001
        print(f"\n##### {url} -> ERREUR {e}")
