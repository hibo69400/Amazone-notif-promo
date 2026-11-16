# Alertes promos Amazon

Un petit robot qui surveille les bons plans **vendus sur Amazon.fr** pour une liste de marques,
et qui envoie une notification sur le téléphone dès qu'une offre atteint **30 % de remise ou plus**.

Il tourne tout seul sur GitHub, toutes les 10 minutes environ. Aucun ordinateur à laisser allumé.

## Recevoir les notifications

1. Installer l'application **ntfy** (iPhone ou Android), gratuite et sans compte.
2. Dans l'application, s'abonner à son sujet secret (un nom long et difficile à deviner).
3. Dans ce dépôt : **Settings**, **Secrets and variables**, **Actions**, **New repository secret**.
   Nom : `NTFY_TOPIC`. Valeur : le même sujet secret.

Le sujet n'est écrit nulle part dans le code : toute personne qui le connaît peut lire les notifications.

## Changer les réglages

Tout est dans `config.json` :

- `remise_minimum` : la remise minimale en pourcentage (30 par défaut).
- `marques` : la liste des marques suivies. `alias` contient les façons d'écrire la marque, sans accents.
  `contexte` oblige le titre à contenir l'un de ces mots, pour les noms ambigus (Joie, Ninja, Boss)
  et pour limiter Bosch et Samsung à l'électroménager.
- `notifier_si_remise_inconnue` : mettre `true` pour recevoir aussi les offres dont le prix d'origine n'est pas indiqué.
- `max_notifications_par_passage` : le nombre maximal de notifications par passage (le reste part au passage suivant).

## D'où viennent les offres

Amazon bloque les robots, donc le bot ne lit pas Amazon directement. Il lit des flux publics :

- **Dealabs** : les nouveaux bons plans, plus les rubriques et marques utiles. Seules les offres dont le marchand est Amazon sont gardées.
  La remise est calculée avec le prix barré affiché sur la fiche de l'offre.
- **CamelCamelCamel** : les plus fortes baisses de prix du jour sur Amazon.fr.

Conséquence : le bot voit les bonnes affaires repérées par ces sites, pas la totalité du catalogue Amazon.

## Vérifier que ça marche

Onglet **Actions**, tâche **Alertes promos Amazon** : chaque passage affiche les sources lues et les offres retenues.
Le bouton **Run workflow** lance un passage tout de suite ; cocher « Essai » affiche les offres sans rien envoyer.
