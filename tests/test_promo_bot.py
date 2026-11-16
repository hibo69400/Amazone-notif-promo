import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import promo_bot as bot

CONFIG = json.loads((Path(__file__).parent.parent / "config.json").read_text(encoding="utf-8"))
MARQUES = CONFIG["marques"]
MAINTENANT = datetime(2026, 11, 16, 20, 30, tzinfo=timezone.utc)

FLUX_DEALABS = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:media="http://search.yahoo.com/mrss/" xmlns:pepper="http://www.pepper.com/rss" version="2.0"><channel>
<title>Dealabs</title>
<item><category><![CDATA[Maison & Habitat]]></category><pepper:merchant name="Amazon" price="229€"/>
<title><![CDATA[Aspirateur balai sans fil Dyson V8 Origin - Aspiration 130AW]]></title>
<description><![CDATA[<strong>229€ - Amazon</strong><br />Bon prix]]></description>
<link>https://www.dealabs.com/bons-plans/dyson-v8-origin-aspirateur-balai-sans-fil-puissant-3457304</link>
<pubDate>Mon, 16 Nov 2026 10:37:00 +0100</pubDate>
<guid>https://www.dealabs.com/bons-plans/dyson-v8-origin-aspirateur-balai-sans-fil-puissant-3457304</guid></item>
<item><pepper:merchant name="Fnac" price="1 149€"/>
<title><![CDATA[Dyson Airwrap]]></title><description><![CDATA[x]]></description>
<link>https://www.dealabs.com/bons-plans/dyson-airwrap-3457999</link>
<pubDate>Mon, 16 Nov 2026 19:58:42 +0100</pubDate>
<guid>https://www.dealabs.com/bons-plans/dyson-airwrap-3457999</guid></item>
<item><title><![CDATA[10% cagnotté sur tout]]></title><description><![CDATA[x]]></description>
<link>https://www.dealabs.com/bons-plans/cagnotte-3458000</link>
<pubDate>Mon, 16 Nov 2026 19:00:00 +0100</pubDate>
<guid>https://www.dealabs.com/bons-plans/cagnotte-3458000</guid></item>
</channel></rss>""".encode()

FLUX_CAMEL = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Top Amazon Price Drops</title>
<item><title>Philips Rasoir i9000 Prestige ..., 5 modes de rasage, XP9404/31 - down 41.51% (177,39€) to 249,99€ from 427,38€</title>
<link>https://fr.camelcamelcamel.com/product/B0983L4CH1</link>
<pubDate>Mon, 16 Nov 2026 11:13:41 PST</pubDate></item>
<item><title>Irix Cine 11mm - down 17.60% (193,56€) to 906,34€ from 1.099,90€</title>
<link>https://fr.camelcamelcamel.com/product/B0AAAAAAAA</link>
<pubDate>Mon, 16 Nov 2026 11:13:41 PST</pubDate></item>
<item><title>Titre sans le format attendu</title><link>https://fr.camelcamelcamel.com/product/B0BBBBBBBB</link></item>
</channel></rss>""".encode()

PAGE_DEALABS = (
    '<h1>Dyson V8</h1><span class="vAlign--all-tt"><span class="threadItemCard-price text--b thread-price">229€</span></span>'
    '<div class="flex boxAlign-ai--all-c"><span class="text--lineThrough space--ml-1 size--all-xl">337,87€</span><button></button></div>'
    + "x" * 900 +
    '<span class="threadItemCard-price text--b thread-price size--all-l">31,51€</span></span><div><span class="text--lineThrough size--all-s">44,90€</span>'
)
PAGE_SANS_PRIX_BARRE = (
    '<span class="threadItemCard-price text--b thread-price">449,99€</span></span><div></div>'
    '<span class="threadItemCard-price text--b thread-price size--all-l">31,51€</span></span><div><span class="text--lineThrough size--all-s">44,90€</span>'
)


def marque(titre):
    m = bot.trouver_marque(titre, MARQUES)
    return m["nom"] if m else None


class TestMarques(unittest.TestCase):
    def test_marque_simple_avec_accents_et_casse(self):
        self.assertEqual(marque("Chauffe-biberon BÉABA Bib'expresso"), "Béaba")
        self.assertEqual(marque("Nettoyeur haute pression Kärcher K5"), "Kärcher")
        self.assertEqual(marque("Shampoing Kérastase Nutritive 250 ml"), "Kérastase")

    def test_marques_en_plusieurs_mots(self):
        self.assertEqual(marque("Machine à café De'Longhi Magnifica S"), "De'Longhi")
        self.assertEqual(marque("Siège auto Maxi-Cosi Pearl 360"), "Maxi-Cosi")
        self.assertEqual(marque("Mascara L'Oréal Paris Telescopic"), "L'Oréal Paris")
        self.assertEqual(marque("Lot de 2 T-shirts Amazon Essentials homme"), "Amazon Essentials")

    def test_pas_de_correspondance_a_l_interieur_d_un_mot(self):
        self.assertIsNone(marque("Jeu LEGO Ninjago 71800"))
        self.assertIsNone(marque("Snikers barre chocolatée"))
        self.assertIsNone(marque("TV 76\" Hisense 75U7SE - QLED Mini LED"))

    def test_marques_ambigues_exigent_un_contexte(self):
        self.assertIsNone(marque("Coffret Joie de vivre - 3 bougies"))
        self.assertEqual(marque("Siège auto Joie i-Spin 360 isofix"), "Joie")
        self.assertIsNone(marque("Ninja Gaiden 4 sur PS5"))
        self.assertEqual(marque("Friteuse sans huile Ninja Foodi AF300EU"), "Ninja")
        self.assertIsNone(marque("Ampli guitare Boss Katana 50"))
        self.assertEqual(marque("Eau de toilette Boss Bottled 100 ml"), "BOSS")
        self.assertEqual(marque("Hugo Boss - Lot de 3 boxers"), "BOSS")

    def test_samsung_et_bosch_limites_a_l_electromenager(self):
        self.assertIsNone(marque("Smartphone Pliable Samsung Galaxy Z Fold8 - 5G, 256 Go"))
        self.assertEqual(marque("Lave-linge Samsung WW90 9 kg"), "Samsung")
        self.assertIsNone(marque("Perceuse-visseuse Bosch Professional GSR 18V"))
        self.assertEqual(marque("Lave-linge Bosch WGE02405FR - 7 kg, 1400 trs/min"), "Bosch")

    def test_accessoires_compatibles_ignores(self):
        self.assertIsNone(marque("100 capsules de café compatibles Nespresso L'Or"))
        self.assertIsNone(marque("Batterie de rechange pour Dyson V8"))
        self.assertEqual(marque("Aspirateur Dyson V8 pour maison avec animaux"), "Dyson")


class TestPrix(unittest.TestCase):
    def test_lire_prix(self):
        self.assertEqual(bot.lire_prix("229€"), 229.0)
        self.assertEqual(bot.lire_prix("284,05€"), 284.05)
        self.assertEqual(bot.lire_prix("1 149€"), 1149.0)
        self.assertEqual(bot.lire_prix("1 149,50 €"), 1149.5)
        self.assertEqual(bot.lire_prix("1.099,90€"), 1099.9)
        self.assertEqual(bot.lire_prix("1.099€"), 1099.0)
        self.assertEqual(bot.lire_prix("12.5"), 12.5)
        self.assertIsNone(bot.lire_prix("Gratuit"))
        self.assertIsNone(bot.lire_prix(None))

    def test_remise(self):
        self.assertEqual(bot.remise(229, 337.87), 32)
        self.assertEqual(bot.remise(70, 100), 30)
        self.assertIsNone(bot.remise(229, None))
        self.assertIsNone(bot.remise(None, 100))
        self.assertIsNone(bot.remise(120, 100))
        self.assertIsNone(bot.remise(10, 0))

    def test_format_prix(self):
        self.assertEqual(bot.format_prix(229), "229 €")
        self.assertEqual(bot.format_prix(337.87), "337,87 €")
        self.assertEqual(bot.format_prix(1149), "1 149 €")
        self.assertEqual(bot.format_prix(5.9), "5,90 €")

    def test_reference_dans_texte(self):
        texte = "proposé à 5,91 € (au lieu de 7,32 € en prix de référence, soit 19 %)"
        self.assertEqual(bot.reference_dans_texte(texte), 7.32)
        self.assertEqual(bot.reference_dans_texte("249 € au lieu de 1 599€ !"), 1599.0)
        self.assertIsNone(bot.reference_dans_texte("Bon prix"))


class TestLecture(unittest.TestCase):
    def test_flux_dealabs(self):
        offres = bot.lire_flux_dealabs(FLUX_DEALABS)
        self.assertEqual(len(offres), 3)
        o = offres[0]
        self.assertEqual(o["id"], "dealabs:3457304")
        self.assertEqual(o["titre"], "Aspirateur balai sans fil Dyson V8 Origin - Aspiration 130AW")
        self.assertEqual(o["marchand"], "Amazon")
        self.assertEqual(o["prix"], 229.0)
        self.assertEqual(o["lien"], "https://www.dealabs.com/visit/threadmain/3457304")
        self.assertEqual(o["details"], "https://www.dealabs.com/bons-plans/dyson-v8-origin-aspirateur-balai-sans-fil-puissant-3457304")
        self.assertEqual(o["date"], datetime(2026, 11, 16, 9, 37, tzinfo=timezone.utc))
        self.assertEqual(offres[1]["marchand"], "Fnac")
        self.assertEqual(offres[1]["prix"], 1149.0)
        self.assertEqual(offres[2]["marchand"], "")
        self.assertIsNone(offres[2]["prix"])

    def test_flux_camel(self):
        offres = bot.lire_flux_camel(FLUX_CAMEL)
        self.assertEqual(len(offres), 2)
        o = offres[0]
        self.assertEqual(o["id"], "amazon:B0983L4CH1")
        self.assertEqual(o["titre"], "Philips Rasoir i9000 Prestige ..., 5 modes de rasage, XP9404/31")
        self.assertEqual(o["marchand"], "Amazon")
        self.assertEqual((o["prix"], o["reference"]), (249.99, 427.38))
        self.assertEqual(o["lien"], "https://www.amazon.fr/dp/B0983L4CH1")
        self.assertEqual(o["date"], datetime(2026, 11, 16, 19, 13, 41, tzinfo=timezone.utc))
        self.assertEqual(offres[1]["reference"], 1099.9)

    def test_flux_illisible_leve_une_erreur(self):
        with self.assertRaises(Exception):
            bot.lire_flux_dealabs(b"<html>Access denied</html><p>")

    def test_prix_page_dealabs(self):
        self.assertEqual(bot.prix_page_dealabs(PAGE_DEALABS), (229.0, 337.87))

    def test_prix_page_sans_prix_barre_n_emprunte_pas_celui_d_une_autre_offre(self):
        self.assertEqual(bot.prix_page_dealabs(PAGE_SANS_PRIX_BARRE), (449.99, None))
        self.assertEqual(bot.prix_page_dealabs("<html>offre expirée</html>"), (None, None))


def offre(ident, titre, prix=70.0, reference=None, marchand="Amazon", age_h=1.0, description=""):
    return {"id": ident, "titre": titre, "marchand": marchand, "prix": prix, "reference": reference,
            "lien": f"https://exemple.test/{ident}", "details": f"https://exemple.test/d/{ident}",
            "date": MAINTENANT - timedelta(hours=age_h), "description": description}


class TestSelection(unittest.TestCase):
    def setUp(self):
        self.pages = {}
        self.appels = []

    def page(self, o):
        self.appels.append(o["id"])
        valeur = self.pages.get(o["id"], "")
        if isinstance(valeur, Exception):
            raise valeur
        return valeur

    def choisir(self, offres, etat=None, **reglages):
        config = {**CONFIG, **reglages}
        etat = etat if etat is not None else {"vus": {}}
        return bot.choisir_offres(offres, config, etat, MAINTENANT, self.page), etat

    def test_garde_une_offre_amazon_d_une_marque_a_30_pourcent(self):
        retenues, etat = self.choisir([offre("a", "Aspirateur Dyson V8", 70.0, 100.0)])
        self.assertEqual([o["id"] for o in retenues], ["a"])
        self.assertEqual(retenues[0]["remise"], 30)
        self.assertEqual(retenues[0]["marque"], "Dyson")
        self.assertNotIn("a", etat["vus"], "marquée vue seulement après l'envoi")

    def test_ecarte_remise_insuffisante_et_la_marque_vue(self):
        retenues, etat = self.choisir([offre("a", "Aspirateur Dyson V8", 71.0, 100.0)])
        self.assertEqual(retenues, [])
        self.assertIn("a", etat["vus"])

    def test_ecarte_autres_marchands_et_autres_marques(self):
        retenues, _ = self.choisir([
            offre("a", "Aspirateur Dyson V8", 50.0, 100.0, marchand="Fnac"),
            offre("b", "Aspirateur Rowenta X-Pert", 50.0, 100.0),
            offre("c", "Aspirateur Dyson V8", 50.0, 100.0, marchand=""),
        ])
        self.assertEqual(retenues, [])
        self.assertEqual(self.appels, [], "aucune page chargée pour une offre écartée d'avance")

    def test_accepte_les_variantes_du_marchand_amazon(self):
        retenues, _ = self.choisir([offre("a", "Aspirateur Dyson V8", 50.0, 100.0, marchand="Amazon Marketplace")])
        self.assertEqual(len(retenues), 1)

    def test_ecarte_les_offres_deja_vues_et_trop_anciennes(self):
        retenues, _ = self.choisir(
            [offre("a", "Aspirateur Dyson V8", 50.0, 100.0), offre("b", "Aspirateur Dyson V11", 50.0, 100.0, age_h=30)],
            etat={"vus": {"a": "2026-11-16T10:00:00+00:00"}})
        self.assertEqual(retenues, [])

    def test_va_chercher_le_prix_barre_sur_la_page(self):
        self.pages["a"] = PAGE_DEALABS
        retenues, _ = self.choisir([offre("a", "Aspirateur Dyson V8", 229.0)])
        self.assertEqual((retenues[0]["prix"], retenues[0]["reference"], retenues[0]["remise"]), (229.0, 337.87, 32))

    def test_utilise_le_au_lieu_de_de_la_description_en_secours(self):
        retenues, _ = self.choisir([offre("a", "Aspirateur Dyson V8", 60.0, description="60 € au lieu de 100 € chez Amazon")])
        self.assertEqual(retenues[0]["remise"], 40)

    def test_remise_inconnue_ecartee_par_defaut_gardee_sur_option(self):
        retenues, etat = self.choisir([offre("a", "Aspirateur Dyson V8", 60.0)])
        self.assertEqual(retenues, [])
        self.assertIn("a", etat["vus"])
        retenues, _ = self.choisir([offre("a", "Aspirateur Dyson V8", 60.0)], notifier_si_remise_inconnue=True)
        self.assertEqual(len(retenues), 1)
        self.assertIsNone(retenues[0]["remise"])

    def test_page_en_erreur_l_offre_sera_retentee(self):
        self.pages["a"] = OSError("timeout")
        retenues, etat = self.choisir([offre("a", "Aspirateur Dyson V8", 60.0)])
        self.assertEqual(retenues, [])
        self.assertNotIn("a", etat["vus"])

    def test_plafond_les_plus_recentes_d_abord_le_reste_au_passage_suivant(self):
        offres = [offre(f"o{i}", f"Aspirateur Dyson V{i}", 50.0, 100.0, age_h=i + 1) for i in range(5)]
        retenues, etat = self.choisir(offres, max_notifications_par_passage=2)
        self.assertEqual([o["id"] for o in retenues], ["o0", "o1"])
        self.assertEqual(etat["vus"], {})

    def test_doublon_dans_plusieurs_flux_notifie_une_fois(self):
        o = offre("a", "Aspirateur Dyson V8", 50.0, 100.0)
        retenues, _ = self.choisir([o, dict(o)])
        self.assertEqual(len(retenues), 1)

    def test_offre_sans_prix_ou_sans_date_ne_plante_pas(self):
        sans_date = offre("b", "Aspirateur Dyson V8", 50.0, 100.0)
        sans_date["date"] = None
        retenues, _ = self.choisir([offre("a", "Aspirateur Dyson V8", None), sans_date])
        self.assertEqual([o["id"] for o in retenues], ["b"])


class TestNotification(unittest.TestCase):
    def test_message(self):
        o = offre("a", "Aspirateur balai Dyson V8 Origin", 229.0, 337.87)
        o.update(remise=32, marque="Dyson")
        n = bot.composer_notification(o, "mon-sujet")
        self.assertEqual(n["topic"], "mon-sujet")
        self.assertEqual(n["title"], "-32 % · Dyson · 229 €")
        self.assertEqual(n["message"], "Aspirateur balai Dyson V8 Origin\n229 € au lieu de 337,87 € sur Amazon")
        self.assertEqual(n["click"], "https://exemple.test/a")
        self.assertEqual(n["actions"][0]["url"], "https://exemple.test/a")
        self.assertEqual(n["actions"][1]["url"], "https://exemple.test/d/a")

    def test_message_remise_inconnue(self):
        o = offre("a", "Aspirateur Dyson V8", 229.0)
        o.update(remise=None, marque="Dyson")
        n = bot.composer_notification(o, "s")
        self.assertEqual(n["title"], "Dyson · 229 €")
        self.assertIn("remise non précisée", n["message"])


class TestEtat(unittest.TestCase):
    def test_nettoyage_des_anciennes_entrees(self):
        etat = {"vus": {"vieux": "2026-09-01T00:00:00+00:00", "recent": "2026-11-15T00:00:00+00:00", "casse": "???"}}
        bot.nettoyer_etat(etat, MAINTENANT)
        self.assertEqual(list(etat["vus"]), ["recent"])

    def test_passage_complet_du(self):
        self.assertTrue(bot.passage_complet_du({"vus": {}}, MAINTENANT, 25))
        recent = {"dernier_passage_complet": (MAINTENANT - timedelta(minutes=10)).isoformat()}
        ancien = {"dernier_passage_complet": (MAINTENANT - timedelta(minutes=26)).isoformat()}
        self.assertFalse(bot.passage_complet_du(recent, MAINTENANT, 25))
        self.assertTrue(bot.passage_complet_du(ancien, MAINTENANT, 25))
        self.assertTrue(bot.passage_complet_du({"dernier_passage_complet": "pas une date"}, MAINTENANT, 25))


if __name__ == "__main__":
    unittest.main()
