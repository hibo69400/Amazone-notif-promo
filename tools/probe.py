"""Diagnostic : teste quelles sources de bons plans répondent depuis GitHub Actions."""
import sys
import urllib.request

UAS = {
    "bot": "Mozilla/5.0 (compatible; promo-notif-bot/1.0; +https://github.com/hibo69400/Amazone-notif-promo)",
    "browser": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
}
URLS = [
    "https://www.dealabs.com/rss/hot",
    "https://www.dealabs.com/rss/nouveaux",
    "https://www.dealabs.com/rss/tous",
    "https://www.dealabs.com/rss/new",
    "https://www.dealabs.com/rss/all",
    "https://www.dealabs.com/rss/marchands/amazon",
    "https://www.dealabs.com/rss/codes-promo/amazon.fr",
    "https://www.dealabs.com/rss/groupe/amazon",
    "https://www.dealabs.com/rss/search?q=dyson",
    "https://www.dealabs.com/search?q=dyson&merchant-id=37",
    "https://www.dealabs.com/nouveaux",
    "https://fr.camelcamelcamel.com/top_drops/feed",
    "https://fr.camelcamelcamel.com/popular/feed",
    "https://www.frandroid.com/bons-plans/feed",
    "https://www.lesnumeriques.com/bons-plans/rss.xml",
]
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
for url in URLS:
    for name, ua in UAS.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "fr-FR,fr;q=0.9"})
            with urllib.request.urlopen(req, timeout=25) as r:
                body = r.read()
                print(f"\n=== {url} [{name}] -> {r.status} {r.headers.get('Content-Type')} {len(body)} octets")
                print(body[:limit].decode("utf-8", "replace"))
                break
        except Exception as e:  # noqa: BLE001
            print(f"\n=== {url} [{name}] -> ERREUR {e}")
