from flask import Flask, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import requests
import re
import os

app = Flask(__name__)
CORS(app)

MANIFEST = {
    "id": "org.animesalt.tv",
    "version": "2.0.0",
    "name": "AnimeSalt Ultimate 🚀",
    "description": "Lecture directe via Render Optimisé",
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
        titre = reponse.json().get("meta", {}).get("name", "")
        if titre: return titre
    except:
        pass
    return None

def transformer_en_slug(titre):
    titre = titre.lower()
    titre = re.sub(r'[^a-z0-9\s-]', '', titre)
    return re.sub(r'\s+', '-', titre.strip())

def extraire_m3u8(url):
    lien_trouve = None
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage", 
                "--disable-gpu", 
                "--single-process"
            ]
        )
        context = browser.new_context()
        page = context.new_page()
        
        # ⚡ L'arme secrète : on bloque toutes les images, CSS et médias pour charger la page instantanément
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] else route.continue_())
        
        def ecouter_reseau(requete):
            nonlocal lien_trouve
            if ".m3u8" in requete.url and "ping.gif" not in requete.url:
                lien_trouve = requete.url
                
        page.on("request", ecouter_reseau)
        
        try:
            # On n'attend plus que la page soit 100% chargée, juste le code principal
            page.goto(url, wait_until="domcontentloaded", timeout=10000)
            page.mouse.click(400, 300)
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Erreur Playwright: {e}")
        finally:
            browser.close()
            
    return lien_trouve

@app.route('/stream/<type>/<id>.json')
def addon_stream(type, id):
    print(f"\n🎬 Demande ID : {id}")
    parts = id.split(':')
    imdb_id = parts[0]
    saison = parts[1] if len(parts) >= 3 else "1"
    episode = parts[2] if len(parts) >= 3 else "1"

    nom_anime = recuperer_nom_anime(imdb_id)
    if not nom_anime:
        return jsonify({"streams": []})

    slug_anime = transformer_en_slug(nom_anime)
    lien_cible = f"https://animesalt.cx/episode/{slug_anime}-{saison}x{episode}/"

    vrai_lien_video = extraire_m3u8(lien_cible)

    if vrai_lien_video:
        return jsonify({
            "streams": [{"title": f"AnimeSalt 🚀\nDirect S{saison}E{episode}", "url": vrai_lien_video}]
        })
    else:
        return jsonify({"streams": []})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
