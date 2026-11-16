"""Alertes promos Amazon : lit des flux publics de bons plans, garde les offres
vendues sur Amazon pour les marques choisies avec une remise suffisante, et
envoie une notification ntfy par offre.

Réglages dans config.json. Sujet ntfy dans la variable NTFY_TOPIC.
"""
import argparse
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

RACINE = Path(__file__).parent
FICHIER_ETAT = RACINE / "etat.json"
AGENT = "Mozilla/5.0 (compatible; promo-notif-bot/1.0; +https://github.com/hibo69400/Amazone-notif-promo)"
PEPPER = {"pepper": "http://www.pepper.com/rss"}
# Un nom de marque précédé de ces mots désigne un accessoire, pas un produit de la marque.
PREFIXES_ACCESSOIRE = ("pour", "compatible", "compatibles", "compatible avec", "compatibles avec")
JOURS_MEMOIRE = 45


# ---------- marques ----------

def normaliser(texte):
    """Minuscules, sans accents, ponctuation remplacée par des espaces."""
    sans_accents = unicodedata.normalize("NFKD", texte or "")
    sans_accents = "".join(c for c in sans_accents if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sans_accents.lower()).strip()


def _positions(expression, texte):
    return [m.start() for m in re.finditer(rf"(?<![a-z0-9]){re.escape(expression)}(?![a-z0-9])", texte)]


def trouver_marque(titre, marques):
    """Renvoie la marque suivie dont le nom apparaît dans le titre, sinon None."""
    texte = normaliser(titre)
    for marque in marques:
        contexte = marque.get("contexte")
        if contexte and not any(_positions(mot, texte) for mot in contexte):
            continue
        for alias in marque["alias"]:
            for position in _positions(alias, texte):
                avant = texte[:position].rstrip()
                if not any(avant == p or avant.endswith(" " + p) for p in PREFIXES_ACCESSOIRE):
                    return marque
    return None


# ---------- prix ----------

def lire_prix(texte):
    trouve = re.search(r"\d[\d\s.,]*", texte or "")
    if not trouve:
        return None
    brut = re.sub(r"\s", "", trouve.group(0)).rstrip(".,")
    if "," in brut:
        brut = brut.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", brut):
        brut = brut.replace(".", "")
    try:
        return float(brut)
    except ValueError:
        return None


def remise(prix, reference):
    """Pourcentage de remise arrondi, ou None si on ne peut pas le calculer."""
    if prix is None or not reference or reference <= 0 or prix >= reference:
        return None
    return round((reference - prix) / reference * 100)


def format_prix(valeur):
    entier, centimes = divmod(round(valeur * 100), 100)
    texte = f"{entier:,}".replace(",", " ")
    return f"{texte},{centimes:02d} €" if centimes else f"{texte} €"


def reference_dans_texte(texte):
    trouve = re.search(r"au lieu de\s*(\d[\d\s.,]*)\s*€", texte or "", flags=re.I)
    return lire_prix(trouve.group(1)) if trouve else None


# ---------- lecture des sources ----------

def _date(texte):
    try:
        date = parsedate_to_datetime(texte)
    except (TypeError, ValueError):
        return None
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return date.astimezone(timezone.utc)


def _texte_brut(balises):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", balises or ""))).strip()


def lire_flux_dealabs(contenu):
    offres = []
    for item in ET.fromstring(contenu).findall("./channel/item"):
        page = (item.findtext("link") or item.findtext("guid") or "").strip()
        numero = re.search(r"-(\d+)/?$", page)
        marchand = item.find("pepper:merchant", PEPPER)
        attributs = marchand.attrib if marchand is not None else {}
        offres.append({
            "id": f"dealabs:{numero.group(1)}" if numero else f"dealabs:{page}",
            "titre": (item.findtext("title") or "").strip(),
            "marchand": attributs.get("name", ""),
            "prix": lire_prix(attributs.get("price")),
            "reference": None,
            "lien": f"https://www.dealabs.com/visit/threadmain/{numero.group(1)}" if numero else page,
            "details": page,
            "date": _date(item.findtext("pubDate")),
            "description": _texte_brut(item.findtext("description")),
        })
    return offres


FORMAT_CAMEL = re.compile(r"^(.*) - down [\d.,]+% \([^)]*\) to ([\d.,]+)€ from ([\d.,]+)€\s*$", re.S)


def lire_flux_camel(contenu):
    offres = []
    for item in ET.fromstring(contenu).findall("./channel/item"):
        titre = FORMAT_CAMEL.match((item.findtext("title") or "").strip())
        page = (item.findtext("link") or "").strip()
        asin = re.search(r"/product/([A-Z0-9]{10})", page)
        if not titre or not asin:
            continue
        offres.append({
            "id": f"amazon:{asin.group(1)}",
            "titre": titre.group(1).strip(),
            "marchand": "Amazon",
            "prix": lire_prix(titre.group(2)),
            "reference": lire_prix(titre.group(3)),
            "lien": f"https://www.amazon.fr/dp/{asin.group(1)}",
            "details": page,
            "date": _date(item.findtext("pubDate")),
            "description": "",
        })
    return offres


def prix_page_dealabs(page):
    """(prix, prix barré) de l'offre principale d'une page Dealabs."""
    principal = re.search(r"thread-price[^>]*>([^<]+)<", page or "")
    if not principal:
        return None, None
    suite = page[principal.end():principal.end() + 600]
    autre_offre = suite.find("thread-price")
    if autre_offre != -1:
        suite = suite[:autre_offre]
    barre = re.search(r"text--lineThrough[^>]*>([^<]+)<", suite)
    return lire_prix(principal.group(1)), lire_prix(barre.group(1)) if barre else None


# ---------- sélection ----------

def choisir_offres(offres, config, etat, maintenant, charger_page):
    """Renvoie les offres à notifier. Les offres écartées pour de bon sont
    notées dans etat["vus"] ; celles à notifier le seront après l'envoi."""
    vus = etat.setdefault("vus", {})
    age_max = timedelta(hours=config["age_maximum_heures"])
    candidates, identifiants = [], set()
    for offre in offres:
        if offre["id"] in vus or offre["id"] in identifiants:
            continue
        if "amazon" not in normaliser(offre["marchand"]):
            continue
        if offre["date"] and maintenant - offre["date"] > age_max:
            continue
        marque = trouver_marque(offre["titre"], config["marques"])
        if not marque:
            continue
        identifiants.add(offre["id"])
        candidates.append({**offre, "marque": marque["nom"]})
    candidates.sort(key=lambda o: o["date"] or maintenant, reverse=True)

    retenues = []
    ecartees = {"remise trop faible": 0, "sans prix d'origine": 0}
    for offre in candidates:
        if len(retenues) >= config["max_notifications_par_passage"]:
            break
        if offre["reference"] is None:
            try:
                prix_page, barre = prix_page_dealabs(charger_page(offre))
            except Exception as erreur:  # noqa: BLE001 - on réessaiera au passage suivant
                print(f"  page illisible, à réessayer : {offre['details']} ({erreur})")
                continue
            if offre["prix"] is None:
                offre["prix"] = prix_page
            offre["reference"] = barre or reference_dans_texte(offre["description"])
        offre["remise"] = remise(offre["prix"], offre["reference"])
        if offre["prix"] is None:
            garder = False
        elif offre["remise"] is None:
            garder = config["notifier_si_remise_inconnue"]
        else:
            garder = offre["remise"] >= config["remise_minimum"]
        if garder:
            retenues.append(offre)
        else:
            vus[offre["id"]] = maintenant.isoformat()
            ecartees["sans prix d'origine" if offre["remise"] is None else "remise trop faible"] += 1
    print(f"{len(candidates)} nouvelle(s) offre(s) Amazon de tes marques : {len(retenues)} retenue(s), "
          f"{ecartees['remise trop faible']} sous {config['remise_minimum']} %, "
          f"{ecartees["sans prix d'origine"]} sans prix d'origine.")
    return retenues


def composer_notification(offre, sujet):
    prix = format_prix(offre["prix"])
    if offre["remise"] is None:
        titre = f"{offre['marque']} · {prix}"
        detail = f"{prix} sur Amazon, remise non précisée"
    else:
        titre = f"-{offre['remise']} % · {offre['marque']} · {prix}"
        detail = f"{prix} au lieu de {format_prix(offre['reference'])} sur Amazon"
    actions = [{"action": "view", "label": "Voir sur Amazon", "url": offre["lien"]}]
    if offre.get("details") and offre["details"] != offre["lien"]:
        actions.append({"action": "view", "label": "Détails", "url": offre["details"]})
    return {"topic": sujet, "title": titre, "message": f"{offre['titre']}\n{detail}",
            "click": offre["lien"], "actions": actions}


# ---------- mémoire entre deux passages ----------

def nettoyer_etat(etat, maintenant):
    limite = maintenant - timedelta(days=JOURS_MEMOIRE)
    gardes = {}
    for identifiant, date in etat.get("vus", {}).items():
        try:
            if datetime.fromisoformat(date) >= limite:
                gardes[identifiant] = date
        except (TypeError, ValueError):
            pass
    etat["vus"] = gardes


def passage_complet_du(etat, maintenant, minutes):
    try:
        dernier = datetime.fromisoformat(etat["dernier_passage_complet"])
    except (KeyError, TypeError, ValueError):
        return True
    return maintenant - dernier >= timedelta(minutes=minutes)


def charger_etat():
    try:
        etat = json.loads(FICHIER_ETAT.read_text(encoding="utf-8"))
        if isinstance(etat, dict) and isinstance(etat.get("vus", {}), dict):
            return etat
    except (OSError, ValueError):
        pass
    return {"vus": {}}


# ---------- réseau ----------

def telecharger(url):
    requete = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept-Language": "fr-FR,fr;q=0.9"})
    with urllib.request.urlopen(requete, timeout=25) as reponse:
        return reponse.read()


def envoyer(notification, serveur):
    requete = urllib.request.Request(serveur, data=json.dumps(notification).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "User-Agent": AGENT})
    with urllib.request.urlopen(requete, timeout=25):
        pass


def main():
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--essai", action="store_true",
                           help="affiche les notifications sans les envoyer ni rien mémoriser")
    essai = arguments.parse_args().essai

    config = json.loads((RACINE / "config.json").read_text(encoding="utf-8"))
    sujet = os.environ.get("NTFY_TOPIC", "").strip()
    serveur = os.environ.get("NTFY_SERVER", "").strip() or "https://ntfy.sh"
    if not sujet and not essai:
        sys.exit("NTFY_TOPIC est vide : ajoute le secret NTFY_TOPIC dans les réglages du dépôt.")

    maintenant = datetime.now(timezone.utc)
    etat = charger_etat()
    complet = essai or passage_complet_du(etat, maintenant, config["minutes_entre_passages_complets"])

    sources = [(f"https://www.dealabs.com/rss/{chemin}", lire_flux_dealabs) for chemin in config["flux_dealabs_rapides"]]
    if complet:
        sources += [(f"https://www.dealabs.com/rss/{chemin}", lire_flux_dealabs) for chemin in config["flux_dealabs_complets"]]
        sources += [(f"https://fr.camelcamelcamel.com/top_drops/feed?p={page}", lire_flux_camel)
                    for page in range(1, config["pages_camelcamelcamel"] + 1)]

    offres, echecs = [], 0
    for url, lire in sources:
        try:
            offres += lire(telecharger(url))
        except Exception as erreur:  # noqa: BLE001 - une source en panne ne bloque pas les autres
            echecs += 1
            print(f"  source en erreur : {url} ({erreur})")
        time.sleep(0.4)
    print(f"Passage {'complet' if complet else 'rapide'} : {len(sources) - echecs}/{len(sources)} sources lues, {len(offres)} offres.")

    def charger_page(offre):
        time.sleep(0.5)
        return telecharger(offre["details"]).decode("utf-8", "replace")

    retenues = choisir_offres(offres, config, etat, maintenant, charger_page)
    envois_rates = 0
    for offre in retenues:
        notification = composer_notification(offre, sujet)
        print(f"  {notification['title']} | {offre['titre']}")
        if essai:
            continue
        try:
            envoyer(notification, serveur)
            etat["vus"][offre["id"]] = maintenant.isoformat()
        except Exception as erreur:  # noqa: BLE001 - l'offre reste à envoyer au passage suivant
            envois_rates += 1
            print(f"    envoi raté, à réessayer ({erreur})")
        time.sleep(0.5)
    print(f"{len(retenues) - envois_rates} notification(s) {'à envoyer (essai)' if essai else 'envoyée(s)'}.")

    if not essai:
        if complet and echecs < len(sources):
            etat["dernier_passage_complet"] = maintenant.isoformat()
        nettoyer_etat(etat, maintenant)
        FICHIER_ETAT.write_text(json.dumps(etat, ensure_ascii=False), encoding="utf-8")
    if echecs == len(sources):
        sys.exit("Aucune source n'a répondu.")
    if envois_rates:
        sys.exit(f"{envois_rates} notification(s) non envoyée(s), elles repartiront au prochain passage.")


if __name__ == "__main__":
    main()
