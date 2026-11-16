"""Diagnostic : où se trouvent le prix barré et le lien Amazon dans une page d'offre."""
import re
import urllib.request

UA = "Mozilla/5.0 (compatible; promo-notif-bot/1.0; +https://github.com/hibo69400/Amazone-notif-promo)"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


for link in ["https://www.dealabs.com/bons-plans/dyson-v8-origin-aspirateur-balai-sans-fil-puissant-3457304",
             "https://www.dealabs.com/bons-plans/philips-hue-tap-dial-blanc-3458126"]:
    s = get(link)
    print("\n#####", link, len(s))
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, flags=re.S):
        print("LDJSON:", m.group(1)[:1500])
    for key in ["&quot;price&quot;", "nextBestPrice", "lineThrough", "priceDiscount", "percentage", "&quot;isExpired", "amazon.fr/", "/visit/", "&quot;merchant", "data-vue3="]:
        ms = list(re.finditer(re.escape(key), s))
        print(f"[{key}] {len(ms)} occurrences")
        for m in ms[:2]:
            print("    ", repr(s[max(0, m.start() - 200):m.start() + 400]))
