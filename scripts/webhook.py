"""Envoi d'une fiche de jeu dans le salon forum Discord par un webhook du serveur.

    python -I -X utf8 webhook.py <dossier du jeu>                 ESSAI : contrôle tout, n'envoie rien
    python -I -X utf8 webhook.py <dossier du jeu> --envoyer       crée le post (titre.txt, message.txt, joindre/)
    python -I -X utf8 webhook.py <dossier du jeu> --reponse [--envoyer]
                                                                  répond dans le post déjà créé (reponse/)

Adresse du webhook : fichier webhook.txt du dossier des fiches (parent du dossier du jeu), ou variable
d'environnement DISCORD_WEBHOOK_FICHES. Elle n'est jamais affichée : c'est un secret.
Après un envoi, envoye.txt garde l'identifiant du post (sert à --reponse et empêche un second envoi).
"""
import json, mimetypes, os, re, sys, urllib.error, urllib.request, uuid
from pathlib import Path

MAX_MESSAGE = 2000          # caractères par message Discord
MAX_TITRE = 100             # caractères pour un titre de post
MAX_FICHIERS = 10           # pièces jointes par message
MAX_OCTETS = 10 * 1024 ** 2  # total des pièces jointes sans boost du serveur
FORME = re.compile(r"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[\w-]+")


def adresse(dossier):
    fichier = dossier.parent / "webhook.txt"
    url = os.environ.get("DISCORD_WEBHOOK_FICHES") or (fichier.read_text("utf-8").strip() if fichier.exists() else "")
    if not url:
        sys.exit(f"ERREUR : pas d'adresse de webhook (ni {fichier}, ni DISCORD_WEBHOOK_FICHES).")
    if not FORME.fullmatch(url):
        sys.exit("ERREUR : l'adresse du webhook n'a pas la forme https://discord.com/api/webhooks/<id>/<jeton>.")
    return url


def appel(url, donnees=None, entete=None):
    req = urllib.request.Request(url, data=donnees, headers={"User-Agent": "fiche-jeu-discord", **(entete or {})},
                                 method="POST" if donnees else "GET")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        sys.exit(f"ERREUR Discord {e.code} : {detail}")


def corps(payload, fichiers):
    """multipart/form-data : payload_json + files[n]."""
    borne = uuid.uuid4().hex
    parts = [f'--{borne}\r\nContent-Disposition: form-data; name="payload_json"\r\n'
             f"Content-Type: application/json\r\n\r\n".encode() + json.dumps(payload).encode() + b"\r\n"]
    for i, f in enumerate(fichiers):
        type_ = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        parts.append(f'--{borne}\r\nContent-Disposition: form-data; name="files[{i}]"; filename="{f.name}"\r\n'
                     f"Content-Type: {type_}\r\n\r\n".encode() + f.read_bytes() + b"\r\n")
    parts.append(f"--{borne}--\r\n".encode())
    return b"".join(parts), {"Content-Type": f"multipart/form-data; boundary={borne}"}


def preparer(source):
    message = (source / "message.txt").read_text("utf-8").strip() if (source / "message.txt").exists() else ""
    joindre = source if source.name == "reponse" else source / "joindre"
    fichiers = sorted(f for f in joindre.glob("*") if f.is_file() and f.name != "message.txt") if joindre.exists() else []
    problemes = []
    if not message and not fichiers:
        problemes.append(f"rien à envoyer dans {source}")
    if len(message) > MAX_MESSAGE:
        problemes.append(f"message trop long : {len(message)} caractères (max {MAX_MESSAGE})")
    if len(fichiers) > MAX_FICHIERS:
        problemes.append(f"trop de pièces jointes : {len(fichiers)} (max {MAX_FICHIERS})")
    total = sum(f.stat().st_size for f in fichiers)
    if total > MAX_OCTETS:
        problemes.append(f"pièces jointes trop lourdes : {total / 1024 ** 2:.1f} Mo (max {MAX_OCTETS / 1024 ** 2:.0f} Mo)")
    return message, fichiers, problemes


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-") or set(args[1:]) - {"--envoyer", "--reponse"}:
        sys.exit(__doc__)
    dossier, envoyer, reponse = Path(args[0]).resolve(), "--envoyer" in args, "--reponse" in args
    trace = dossier / "envoye.txt"
    deja = json.loads(trace.read_text("utf-8")) if trace.exists() else {}

    if reponse:
        if not deja.get("post"):
            sys.exit("ERREUR : le post n'a pas encore été créé (pas d'envoye.txt) : pas de réponse possible.")
        if deja.get("reponse"):
            sys.exit(f"ERREUR : la réponse a déjà été envoyée ({deja['reponse']}).")
        titre, (message, fichiers, problemes) = None, preparer(dossier / "reponse")
    else:
        if deja.get("post"):
            sys.exit(f"ERREUR : ce post a déjà été créé ({deja.get('lien', deja['post'])}). Rien envoyé.")
        titre = (dossier / "titre.txt").read_text("utf-8").strip() if (dossier / "titre.txt").exists() else ""
        message, fichiers, problemes = preparer(dossier)
        if not titre:
            problemes.append("titre.txt manquant ou vide")
        elif len(titre) > MAX_TITRE:
            problemes.append(f"titre trop long : {len(titre)} caractères (max {MAX_TITRE})")

    print(f"{'Réponse dans le post ' + deja['post'] if reponse else 'Nouveau post : ' + titre}")
    print(f"Message ({len(message)} caractères) :\n{message}\n")
    for f in fichiers:
        print(f"Pièce jointe : {f.name} ({f.stat().st_size / 1024:.0f} Ko)")
    if problemes:
        sys.exit("\nPROBLÈMES (rien envoyé) :\n- " + "\n- ".join(problemes))
    url = adresse(dossier)
    info = appel(url)  # lecture seule : vérifie que le webhook existe et donne son salon
    print(f"\nWebhook « {info.get('name')} » → salon {info.get('channel_id')} (serveur {info.get('guild_id')})")
    if not envoyer:
        print("\nESSAI : tout est en ordre, rien n'a été envoyé.")
        return

    payload = {"content": message, "allowed_mentions": {"parse": []},
               "attachments": [{"id": i, "filename": f.name} for i, f in enumerate(fichiers)]}
    cible = url + "?wait=true"
    if reponse:
        cible += f"&thread_id={deja['post']}"
    else:
        payload["thread_name"] = titre
    retour = appel(cible, *corps(payload, fichiers))
    lien = f"https://discord.com/channels/{info.get('guild_id')}/{retour['channel_id']}/{retour['id']}"
    if reponse:
        deja["reponse"] = lien
    else:
        deja.update(post=retour["channel_id"], lien=lien)
    trace.write_text(json.dumps(deja, ensure_ascii=False, indent=2), "utf-8")
    print(f"\nENVOYÉ : {lien}")


if __name__ == "__main__":
    main()
