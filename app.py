from flask import Flask, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app)

MANIFEST = {
    "id": "org.animesalt.tv",
    "version": "1.0.0",
    "name": "AnimeSalt Addon",
    "description": "L'arsenal ultime pour lire AnimeSalt sur Stremio",
    "types": ["anime", "series", "movie"],
    "catalogs": [],
    "resources": ["stream"],
    "idPrefixes": ["tt"]
}

@app.route('/manifest.json')
def addon_manifest():
    return jsonify(MANIFEST)

def extraire_m3u8_automatique(url):
    lien_trouve = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def ecouter_reseau(requete):
            nonlocal lien_trouve
            if ".m3u8" in requete.url and "ping.gif" not in requete.url and "jwpltx" not in requete.url:
                lien_trouve = requete.url

        page.on("request", ecouter_reseau)

        try:
            page.goto(url, wait_until="load", timeout=10000)
            page.mouse.click(400, 300)
            page.wait_for_timeout(1000)
            page.mouse.click(400, 300)
            page.wait_for_timeout(3000)
        except:
            pass
            
        browser.close()
    return lien_trouve

@app.route('/stream/<type>/<id>.json')
def addon_stream(type, id):
    print(f"\n🎬 Stremio demande l'ID : {id}")
    
    # L'ID de Stremio ressemble à tt12345:saison:episode
    # On découpe l'ID pour récupérer le numéro de saison et d'épisode
    parts = id.split(':')
    if len(parts) >= 3:
        saison = parts[1]
        episode = parts[2]
    else:
        saison = "1"
        episode = "1"

    # On adapte l'URL dynamiquement selon l'épisode cliqué !
    lien_cible = f"https://animesalt.cx/episode/hunter-x-hunter-{saison}x{episode}/"
    print(f"🔗 Le robot cible l'URL : {lien_cible}")

    m3u8_url = extraire_m3u8_automatique(lien_cible)

    if m3u8_url:
        print(f"✅ VICTOIRE ! Vrai lien volé : {m3u8_url}")
        return jsonify({
            "streams": [{"title": f"AnimeSalt 🚀 (S{saison}E{episode})", "url": m3u8_url}]
        })
    else:
        print("❌ ÉCHEC : Trop lent ou épisode introuvable.")
        return jsonify({"streams": []})

if __name__ == '__main__':
    print("🟢 Le serveur FANTÔME Stremio est allumé sur le port 7000 !")
    app.run(port=7000)
