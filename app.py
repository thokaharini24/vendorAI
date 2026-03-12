from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import json
import time

load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY")
SAMBANOVA_URL = "https://api.sambanova.ai/v1/chat/completions"

# ── LANGUAGE RULES ───────────────────────────
LANGUAGE_RULES = {
    "Telugu": {
        "instruction": "Write ALL content strictly in Telugu language only. Every word must be Telugu script.",
        "hashtag_mix": "15 English hashtags and 10 Telugu hashtags"
    },
    "Hindi": {
        "instruction": "Write ALL content strictly in Hindi (Devanagari).",
        "hashtag_mix": "15 English hashtags and 10 Hindi hashtags"
    },
    "Tamil": {
        "instruction": "Write ALL content strictly in Tamil script.",
        "hashtag_mix": "15 English hashtags and 10 Tamil hashtags"
    },
    "Kannada": {
        "instruction": "Write ALL content strictly in Kannada script.",
        "hashtag_mix": "15 English hashtags and 10 Kannada hashtags"
    },
    "English": {
        "instruction": "Write all content in professional English.",
        "hashtag_mix": "Write all 25 hashtags in English"
    }
}

# ── CATEGORY RULES ───────────────────────────
CATEGORY_RULES = {
    "Home Decor and Crafts": {
        "context": "Focus on aesthetics, handmade quality, gifting value and decoration.",
        "hashtags": "#homedecor #handmade #craft #artisan #decor #gifting"
    },
    "Food and Beverages": {
        "context": "Focus on taste, freshness and homemade quality.",
        "hashtags": "#foodie #homemadefood #indianfood #tasty #fresh"
    },
    "Clothing and Fashion": {
        "context": "Focus on style, comfort and fabric quality.",
        "hashtags": "#fashion #ethnicwear #indianfashion #style"
    },
    "General": {
        "context": "Focus on product quality and value for money.",
        "hashtags": "#handmade #localproduct #india #supportlocal"
    }
}

# ── TEST ROUTE ───────────────────────────────
@app.route('/ping')
def ping():
    return jsonify({
        "status": "running",
        "key_loaded": SAMBANOVA_API_KEY is not None
    })

# ── GENERATE CONTENT ─────────────────────────
@app.route('/generate', methods=['POST'])
def generate():

    data = request.get_json()

    user_input = data.get('user_input', '')
    language = data.get('language', 'English')
    category = data.get('category', 'General')

    print("\n>>> INPUT:", user_input)
    print(">>> LANGUAGE:", language)
    print(">>> CATEGORY:", category)

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    if not SAMBANOVA_API_KEY:
        return jsonify({"error": "API key not found"}), 500

    lang_rules = LANGUAGE_RULES.get(language, LANGUAGE_RULES["English"])
    cat_rules = CATEGORY_RULES.get(category, CATEGORY_RULES["General"])

    prompt = f"""
You are a professional social media marketing expert helping Indian small businesses promote products.

PRODUCT: "{user_input}"
LANGUAGE: {language}

RULE: {lang_rules["instruction"]}

CATEGORY CONTEXT:
{cat_rules["context"]}

Generate professional promotional content ready for social media.

Return ONLY valid JSON:

{{
"product_name": "",
"price": "",
"product_listing": "",
"instagram_caption": "",
"hashtags": "",
"whatsapp_message": "",
"key_features": ""
}}
"""

    headers = {
        "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "Meta-Llama-3.1-8B-Instruct",
        "messages": [
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1200
    }

    print(">>> CALLING SAMBANOVA API")

    # ── SAFE API CALL WITH RETRY ─────────────
    max_retries = 3
    retry_delay = 4
    response = None

    for attempt in range(max_retries):

        try:

            response = requests.post(
                SAMBANOVA_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            print(">>> STATUS:", response.status_code)

            if response.status_code == 200:
                break

            if response.status_code == 429:
                print("⚠️ Rate limit. Waiting...")
                time.sleep(retry_delay)
                continue

            return jsonify({
                "error": "SambaNova API error",
                "details": response.text
            }), 500

        except Exception as e:
            print(">>> NETWORK ERROR:", e)
            time.sleep(retry_delay)

    if response is None or response.status_code != 200:
        return jsonify({
            "error": "AI service busy. Please try again."
        }), 503

    result = response.json()

    text = result['choices'][0]['message']['content'].strip()

    # Clean markdown
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()

    try:
        content = json.loads(text)
    except:
        content = {
            "product_name": user_input,
            "price": "Contact for price",
            "product_listing": f"{user_input}\nHigh quality product\nPerfect for daily use\nOrder now!",
            "instagram_caption": f"✨ {user_input}\nPremium quality\nLimited stock\nDM to order!",
            "hashtags": "#handmade #india #smallbusiness #supportlocal",
            "whatsapp_message": f"{user_input}\nGreat quality\nLimited stock\nReply to order",
            "key_features": "✅ High quality\n✅ Affordable\n✅ Handmade"
        }

    return jsonify({"success": True, "data": content})


# ── REGENERATE SECTION ───────────────────────
@app.route('/regenerate-section', methods=['POST'])
def regenerate_section():

    data = request.get_json()

    user_input = data.get('user_input')
    language = data.get('language')
    section = data.get('section')

    if not user_input or not section:
        return jsonify({"error": "Missing fields"}), 400

    prompt = f"""
Generate only {section} for product: {user_input}
Language: {language}
Return plain text only.
"""

    headers = {
        "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "Meta-Llama-3.1-8B-Instruct",
        "messages": [
            {"role": "system", "content": "Return plain text only."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(SAMBANOVA_URL, headers=headers, json=payload)

    if response.status_code != 200:
        return jsonify({"error": "API error"}), 500

    result = response.json()
    text = result['choices'][0]['message']['content'].strip()

    return jsonify({
        "success": True,
        "section": section,
        "content": text
    })


# ── SERVE FRONTEND ───────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


if __name__ == '__main__':
    print("🚀 VendorAI running at http://localhost:5000")
    app.run(debug=True, port=5000)