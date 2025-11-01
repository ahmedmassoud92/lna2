import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Optional imports
try:
    import snscrape.modules.twitter as sntwitter
except Exception:
    sntwitter = None

try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except Exception:
    SentimentIntensityAnalyzer = None

app = Flask(__name__, static_folder="static")
CORS(app)

MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "")

LIBYA_CITIES = {
    "طرابلس": (13.1913, 32.8872),
    "Tripoli": (13.1913, 32.8872),
    "بنغازي": (20.0667, 32.1167),
    "Benghazi": (20.0667, 32.1167),
    "مصراتة": (15.0906, 32.3754),
    "Misrata": (15.0906, 32.3754),
    "سبها": (14.4333, 27.0333),
    "Sebha": (14.4333, 27.0333),
    "درنة": (22.6367, 32.7670),
    "Derna": (22.6367, 32.7670),
    "سرت": (16.5887, 31.2066),
    "Sirte": (16.5887, 31.2066),
    "البيضاء": (21.7551, 32.7627),
    "Bayda": (21.7551, 32.7627),
    "طبرق": (23.9764, 32.0836),
    "Tobruk": (23.9764, 32.0836),
    "الزاوية": (12.7278, 32.7571),
    "Zawiya": (12.7278, 32.7571),
    "زليتن": (14.5687, 32.4674),
    "Zliten": (14.5687, 32.4674),
    "غريان": (13.0203, 32.1722),
    "Gharyan": (13.0203, 32.1722),
    "الجفرة": (16.2, 28.9667),
    "Jufra": (16.2, 28.9667),
}

def extract_geo_points(texts):
    counts = {}
    for t in texts:
        for city, (lon, lat) in LIBYA_CITIES.items():
            if city in t:
                info = counts.setdefault(city, {"city": city, "lon": lon, "lat": lat, "score": 0})
                info["score"] += 1
    return list(counts.values())

def analyze_sentiment(texts):
    if not SentimentIntensityAnalyzer:
        return {"positive": 0, "negative": 0, "neutral": 100}
    analyzer = SentimentIntensityAnalyzer()
    pos = neg = neu = 0
    n = max(1, len(texts))
    for t in texts:
        s = analyzer.polarity_scores(t)
        if s["compound"] >= 0.2:
            pos += 1
        elif s["compound"] <= -0.2:
            neg += 1
        else:
            neu += 1
    return {
        "positive": round(100*pos/n, 1),
        "negative": round(100*neg/n, 1),
        "neutral": round(100*neu/n, 1),
    }

def twitter_search(query, since="2019-01-01", until=None, limit=500):
    if not sntwitter:
        return []
    until = until or datetime.utcnow().date().isoformat()
    q = f'{query} lang:ar since:{since} until:{until}'
    results = []
    try:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(q).get_items()):
            if i >= limit:
                break
            results.append({
                "date": str(tweet.date),
                "content": tweet.content,
                "user": getattr(tweet, "user", None) and tweet.user.username,
                "url": getattr(tweet, "url", None)
            })
    except Exception as e:
        print("snscrape error:", e)
    return results

def gtrends_score(query):
    if not TrendReq:
        return {"score": 0}
    try:
        pytrends = TrendReq(hl='ar', tz=120)
        pytrends.build_payload([query], timeframe='today 5-y', geo='LY')
        df = pytrends.interest_over_time()
        if df.empty:
            return {"score": 0}
        series = df[query]
        return {"score": int(series.tail(12).mean())}
    except Exception as e:
        print("pytrends error:", e)
        return {"score": 0}

# ---------- Static frontend routes ----------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    # serve additional static assets if you add any later
    try:
        return send_from_directory("static", path)
    except Exception:
        return send_from_directory("static", "index.html")

# ---------- API ----------
@app.route("/api/config")
def api_config():
    return jsonify({"mapbox_token": MAPBOX_TOKEN})

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "q is required"}), 400

    tweets = twitter_search(q, since="2019-01-01", limit=600)
    tweet_texts = [t["content"] for t in tweets]

    fb_posts = []  # TODO: plug Facebook public pages/comments collector here
    gt = gtrends_score(q)

    texts = tweet_texts + [p.get("message","") for p in fb_posts]
    sent = analyze_sentiment(texts)
    geo_points = extract_geo_points(texts)

    if texts:
        if sent["negative"] > 50:
            ai_advice = "الجمهور يميل للنقد الحاد. خفف لهجة التصعيد وركّز على رسائل تطمين ووحدة."
        elif sent["positive"] > 40:
            ai_advice = "الزخم إيجابي. عزّز الرسائل الملموسة (نتائج/إنجازات) للحفاظ على التأييد."
        else:
            ai_advice = "الصورة متوازنة. غيّر الرسائل حسب المدينة والجمهور لاختبار ما يرفع التفاعل."
    else:
        ai_advice = "بيانات قليلة. وسّع الكلمات المفتاحية أو زِد النطاق الزمني."

    return jsonify({
        "query": q,
        "twitter": {"count": len(tweets), "samples": tweets[:10]},
        "facebook": {"count": len(fb_posts), "samples": fb_posts[:10]},
        "gtrends": gt,
        "sentiment": sent,
        "geo_points": geo_points,
        "ai_advice": ai_advice,
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
