from flask import Flask, jsonify
from flask_cors import CORS
import requests
import re
import os

app = Flask(__name__)
CORS(app)

MANIFEST = {
    "id": "org.animesalt.tv",
    "version": "2.0.0",
    "name": "AnimeSalt Ultimate 🚀",
    "description": "L'arsenal ultime pour lire n'importe quel anime sur AnimeSalt",
    "types": ["anime", "series", "movie"],
    "catalogs": [],
    "resources": ["stream"],
    "idPrefixes": ["tt"]
}

@app.route('/manifest.json')
def addon_manifest():
    return jsonify(MANIFEST)

def recuperer_nom_anime(imdb_id):
    try:
        url_meta = f"https://v3-cinemeta.strem.io/meta/series/{imdb_id}.json"
        reponse = requests.get(url_meta, timeout=5)
        data = reponse.json()
        titre = data.get("meta", {}).get("name", "")
        if titre:
            return titre
    except Exception as e:
        print(f"Erreur récupération titre : {e}")
    return None

def transformer_en_slug(titre):
    titre = titre.lower()
    titre = re.sub(r'[^a-z0-9\s-]', '', titre)
    titre = re.sub(r'\s+', '-', titre.strip())
    return titre

def chercher_vrai_lien(url_page):
    """Va chercher le code de la page et extrait directement le lien m3u8 s'il y est caché"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        reponse = requests.get(url_page, headers=headers, timeout=5)
        # Cherche une correspondance .m3u8 dans le code source de la page
        match = re.search(r'(https?://[^\s<>"]+?\.m3u8[^\s<>"]*?)', reponse.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Erreur extraction lien : {e}")
    return None

@app.route('/stream/<type>/<id>.json')
def addon_stream(type, id):
    print(f"\n🎬 Stremio demande l'ID : {id}")
    
    parts = id.split(':')
    imdb_id = parts[0]
    saison = parts[1] if len(parts) >= 3 else "1"
    episode = parts[2] if len(parts) >= 3 else "1"

    nom_anime = recuperer_nom_anime(imdb_id)
    if not nom_anime:
        return jsonify({"streams": []})

    slug_anime = transformer_en_slug(nom_anime)
    lien_cible = f"https://animesalt.cx/episode/{slug_anime}-{saison}x{episode}/"
    print(f"🔗 Analyse de la page : {lien_cible}")

    # Tente de trouver le flux m3u8 directement dans la page
    vrai_lien_video = chercher_vrai_lien(lien_cible)

    if vrai_lien_video:
        print(f"✅ Lien vidéo trouvé : {vrai_lien_video}")
        return jsonify({
            "streams": [{
                "title": f"AnimeSalt Direct 🚀 ({nom_anime} S{saison}E{episode})",
                "url": vrai_lien_video
            }]
        })
    else:
        # Fallback : si le lien direct n'est pas dans le HTML statique, on renvoie un flux webview ou un lien de secours cliquable
        print("⚠️ Lien direct non trouvé dans le code source.")
        return jsonify({
            "streams": [{
                "title": f"AnimeSalt Web 🌐 ({nom_anime} S{saison}E{episode})",
                "url": lien_cible
            }]
        })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
