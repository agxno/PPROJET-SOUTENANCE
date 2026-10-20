import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()
cle = os.environ.get("CINETPAY_API_KEY_CI", "")
mdp = os.environ.get("CINETPAY_API_PASSWORD_CI", "")


def masquer(valeur):
    """Cache tout ce qui ressemble à un jeton ou à un secret."""
    if isinstance(valeur, dict):
        return {
            k: "***masqué***" if any(m in k.lower() for m in ("token", "secret", "password")) else masquer(v)
            for k, v in valeur.items()
        }
    if isinstance(valeur, list):
        return [masquer(v) for v in valeur]
    return valeur


requete = urllib.request.Request(
    "https://api.cinetpay.net/v1/oauth/login",
    data=json.dumps({"api_key": cle, "api_password": mdp}).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MaisonLumiere/1.0",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(requete, timeout=20) as reponse:
        statut = reponse.status
        corps = json.loads(reponse.read().decode("utf-8"))
except urllib.error.HTTPError as erreur:
    statut = erreur.code
    try:
        corps = json.loads(erreur.read().decode("utf-8"))
    except ValueError:
        corps = {"texte": "réponse non lisible"}
except Exception as erreur:
    print("Impossible de joindre CinetPay :", type(erreur).__name__, erreur)
    raise SystemExit(1)

print("Statut HTTP :", statut)
print(json.dumps(masquer(corps), ensure_ascii=False, indent=2))