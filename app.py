from flask import Flask, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(name)
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
    """Va chercher le vrai nom de l'anime sur Cinemeta grâce à l'ID IMDb de Stremio"""
    try:
        url_meta = f"https://v3-cinemeta.strem.io/meta/series/{imdb_id}.json"
        reponse = requests.get(url_meta, timeout=5)
        data = reponse.json()
        titre = data.get("meta", {}).get("name", "")
        if titre:
            print(f"Nom de l'anime détecté : {titre}")
            return titre
    except Exception as e:
        print(f"Erreur récupération titre : {e}")
    return None

def transformer_en_slug(titre):
    """Transforme 'Jujutsu Kaisen' en 'jujutsu-kaisen' pour coller à l'URL d'AnimeSalt"""
    titre = titre.lower()
    titre = re.sub(r'[^a-z0-9\s-]', '', titre)
    titre = re.sub(r'\s+', '-', titre.strip())
    return titre

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
    print(f"🔗 Le robot cible l'URL : {lien_cible}")

    # Mode direct sans Playwright (ultra stable sur Render)
    return jsonify({
        "streams": [{
            "title": f"AnimeSalt 🚀 ({nom_anime} S{saison}E{episode}) - Cliquer pour ouvrir",
            "url": lien_cible
        }]
    })

if name == 'main':
    app.run(port=7000)
