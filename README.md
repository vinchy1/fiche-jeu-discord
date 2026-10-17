# fiche-jeu-discord — skill Claude Code

Prépare les **fiches de jeux** du salon forum *discussion-par-titre* du Discord **Golden Meeple**, au format
du post épinglé « Bibliothèque » :

```
<Auteur> / <Illustrateur> / <Éditeur> / <joueurs> / <année>
BGG : …   GM : …   LEX PLI : …   Game Market : …
[<Type de jeu>]
Cartes : <nombre> cartes (<format>)
+ couverture et règles en pièces jointes
```

Il suffit de demander à Claude Code « fais les fiches Golden Meeple de Trick of Fixer et The Good Farmer ».

## Ce qu'elle fait
- Vérifie dans le salon que le jeu n'a pas déjà son post (lecture seule).
- Rassemble les infos sur BoardGameGeek, la boutique Golden Meeple, le Tokyo Game Market et la chaîne YouTube
  Golden Meeple (vidéos LEX PLI), sans rien inventer : une info introuvable est laissée vide et signalée.
- Récupère la couverture, et les règles avec la skill
  [recherche-regles-jeu](https://github.com/vinchy1/recherche-regles-jeu) (traduction possible avec
  [traduction-regles-jeu](https://github.com/vinchy1/traduction-regles-jeu)).
- Range chaque jeu dans `C:\Claude\Fiches Golden Meeple\<Jeu>\` :
  `titre.txt`, `message.txt` (à coller tel quel), `notes.txt` (sources, manques), `joindre/`, et `reponse/`
  (VF à poster en réponse, facultatif).

## Publier
- **À la main** (par défaut) : « Nouveau post » → coller le titre et le message, glisser les fichiers.
- **Par webhook** (si un admin du serveur en crée un) : voir `references/webhook.md`. Toujours un essai
  d'abord, et rien n'est envoyé sans accord explicite. Jamais avec le compte personnel de l'utilisateur.

## Contenu
- `SKILL.md` : la méthode suivie par Claude.
- `references/webhook.md` : mise en place et utilisation du webhook.
- `scripts/boutique_gm.py` : recherche et lecture des produits de goldenmeeple.be.
- `scripts/webhook.py` : contrôle (mode essai) et envoi d'une fiche ou d'une réponse par webhook.
