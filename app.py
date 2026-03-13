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
        "code": "Telugu",
        "script": "తెలుగు",
        "instruction": """CRITICAL LANGUAGE RULE:
- Write EVERY SINGLE WORD in Telugu script only
- Do NOT write even one word in English in product_listing, instagram_caption, whatsapp_message, key_features
- product_name can be in Telugu
- price must use ₹ symbol with numbers
- hashtags: write 15 in English, 10 in Telugu script
- emojis are allowed everywhere
- If you write even one English word in the content fields, the output is WRONG""",
        "example": "Example Telugu: నేను మట్టి కుండలు అమ్ముతాను — ₹300"
    },
    "Hindi": {
        "code": "Hindi",
        "script": "हिंदी",
        "instruction": """CRITICAL LANGUAGE RULE:
- Write EVERY SINGLE WORD in Hindi Devanagari script only
- Do NOT write even one word in English in product_listing, instagram_caption, whatsapp_message, key_features
- product_name can be in Hindi
- price must use ₹ symbol with numbers
- hashtags: write 15 in English, 10 in Hindi script
- emojis are allowed everywhere
- If you write even one English word in the content fields, the output is WRONG""",
        "example": "Example Hindi: मैं मिट्टी के बर्तन बेचता हूं — ₹300"
    },
    "Tamil": {
        "code": "Tamil",
        "script": "தமிழ்",
        "instruction": """CRITICAL LANGUAGE RULE:
- Write EVERY SINGLE WORD in Tamil script only
- Do NOT write even one word in English in product_listing, instagram_caption, whatsapp_message, key_features
- product_name can be in Tamil
- price must use ₹ symbol with numbers
- hashtags: write 15 in English, 10 in Tamil script
- emojis are allowed everywhere""",
        "example": "Example Tamil: நான் மண் பானைகள் விற்கிறேன் — ₹300"
    },
    "Kannada": {
        "code": "Kannada",
        "script": "ಕನ್ನಡ",
        "instruction": """CRITICAL LANGUAGE RULE:
- Write EVERY SINGLE WORD in Kannada script only
- Do NOT write even one word in English in product_listing, instagram_caption, whatsapp_message, key_features
- product_name can be in Kannada
- price must use ₹ symbol with numbers
- hashtags: write 15 in English, 10 in Kannada script
- emojis are allowed everywhere""",
        "example": "Example Kannada: ನಾನು ಮಣ್ಣಿನ ಮಡಕೆಗಳನ್ನು ಮಾರುತ್ತೇನೆ — ₹300"
    },
    "English": {
        "code": "English",
        "script": "English",
        "instruction": """LANGUAGE RULE:
- Write all content in professional English only
- Use clear simple words that everyone understands
- price must use ₹ symbol with numbers
- hashtags: write all 25 in English
- emojis are allowed everywhere""",
        "example": "Example: I sell handmade clay pots — ₹300"
    }
}

# ── CATEGORY RULES ───────────────────────────
CATEGORY_RULES = {
    "Food and Beverages": {
        "context": "Food product. Highlight taste, freshness, homemade quality, ingredients and health benefits.",
        "hashtags": "#homemadefood #foodie #instafood #indianfood #tasty #fresh #yummy #homekitchen #healthyfood #foodlovers"
    },
    "Clothing and Fashion": {
        "context": "Fashion product. Highlight style, fabric quality, comfort, design and occasions to wear.",
        "hashtags": "#fashion #ethnicwear #indianfashion #handloom #traditional #style #clothing #saree #kurti #ootd"
    },
    "Jewellery and Accessories": {
        "context": "Jewellery product. Highlight design, material, craftsmanship, occasions and gifting value.",
        "hashtags": "#jewellery #handmadejewellery #accessories #gifting #wedding #festivals #traditional #silver #earrings #bangles"
    },
    "Home Decor and Crafts": {
        "context": "Home decor product. Highlight beauty, handmade quality, material, home improvement and gifting.",
        "hashtags": "#homedecor #handmade #craft #artisan #decor #gifting #pottery #interior #traditional #homebeautiful"
    },
    "Plants and Garden": {
        "context": "Plant product. Highlight health benefits, air purification, easy care and home beauty.",
        "hashtags": "#plants #indoorplants #gardening #plantlover #homedecor #nature #greenery #airpurifying #garden #green"
    },
    "Health and Wellness": {
        "context": "Health product. Highlight natural ingredients, health benefits, purity and wellness results.",
        "hashtags": "#health #wellness #natural #organic #ayurveda #herbal #healthy #fitness #pure #naturalremedies"
    },
    "Beauty and Skincare": {
        "context": "Beauty product. Highlight skin benefits, natural ingredients, glow results and daily care.",
        "hashtags": "#skincare #beauty #natural #glowing #skin #selfcare #organic #glow #skincareroutine #beautytips"
    },
    "Toys and Kids": {
        "context": "Kids product. Highlight safety, fun, educational value, age group and durability.",
        "hashtags": "#toys #kids #children #handmadetoys #educational #fun #safe #wooden #playtime #learning"
    },
    "Services": {
        "context": "Service. Highlight expertise, reliability, quality, pricing and customer satisfaction.",
        "hashtags": "#service #professional #quality #reliable #affordable #local #expert #skilled #trusted #bestservice"
    },
    "Agriculture and Farming": {
        "context": "Farm product. Highlight freshness, organic nature, farm to table and nutritional value.",
        "hashtags": "#organic #farming #fresh #farmtotable #natural #pure #healthy #desi #village #localfarm"
    },
    "General": {
        "context": "General product. Highlight quality, uniqueness, value for money and customer benefits.",
        "hashtags": "#handmade #localproduct #india #supportlocal #quality #affordable #shoplocal #madeinIndia #smallbusiness #local"
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

    prompt = f"""You are a world-class social media marketing expert for Indian small businesses and street vendors.

VENDOR PRODUCT DESCRIPTION: "{user_input}"
OUTPUT LANGUAGE: {language} ({lang_rules["script"]})
PRODUCT CATEGORY: {category}

{lang_rules["instruction"]}

CATEGORY FOCUS: {cat_rules["context"]}

YOUR TASK:
Generate highly professional, persuasive, social-media-ready promotional content.
The content must be clear, direct and easy to understand for the target buyer.
Make it feel like content from a real professional brand — not generic text.

CONTENT REQUIREMENTS:

1. product_name:
   - Clear professional name of the product in {language}
   - Maximum 5 words

2. price:
   - Extract price from description
   - Format: ₹XXX
   - If not mentioned write: "ధర కోసం సంప్రదించండి" (Telugu) or "मूल्य के लिए संपर्क करें" (Hindi) or "Contact for price" (English)

3. product_listing:
   - Write in {language} ONLY
   - 4 lines exactly
   - Line 1 🌟: What the product is + main unique feature
   - Line 2 ✨: Material or how it is made + quality
   - Line 3 🎯: Perfect use case or occasion
   - Line 4 📲: Urgency + call to action
   - Each line starts with an emoji
   - NO English words in this field if language is not English

4. instagram_caption:
   - Write in {language} ONLY
   - 5 lines exactly
   - Line 1: Eye catching opening with big emoji
   - Line 2: Main product benefit with emoji
   - Line 3: Emotional connection or story with emoji
   - Line 4: Special offer or limited stock urgency with emoji
   - Line 5: Strong CTA — DM to order, limited stock with emoji
   - Make it feel exciting and premium
   - NO English words if language is not English

5. hashtags:
   - {lang_rules["hashtag_mix"]}
   - Include category specific: {cat_rules["hashtags"]}
   - All on one line separated by spaces
   - Total 25 hashtags

6. whatsapp_message:
   - Write in {language} ONLY
   - Maximum 6 lines
   - Line 1: Product announcement with emoji
   - Line 2: Key benefit
   - Line 3: Price clearly with ₹ symbol
   - Line 4: Why buy now — limited stock or special offer
   - Line 5: How to order — reply or DM
   - Short punchy sentences
   - NO English words if language is not English

7. key_features:
   - Write in {language} ONLY
   - Exactly 3 lines
   - Each line starts with ✅
   - Each line is one powerful benefit sentence
   - NO English words if language is not English

RETURN FORMAT:
Return ONLY a valid JSON object. No markdown. No backticks. No extra text. No explanation.

{{
    "product_name": "write here",
    "price": "write here",
    "product_listing": "write here",
    "instagram_caption": "write here",
    "hashtags": "write here",
    "whatsapp_message": "write here",
    "key_features": "write here"
}}"""

    headers = {
        "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "Meta-Llama-3.3-70B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": f"You are a professional marketing expert. You must write ALL content strictly in {language} language only. Never mix languages. Return valid JSON only. No markdown. No backticks. No extra text."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    print(">>> CALLING SAMBANOVA API")

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

    print(">>> RAW TEXT:", text[:200])

    # Clean markdown if present
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    # Parse JSON safely
    try:
        content = json.loads(text)
    except json.JSONDecodeError:
        # Try to fix truncated JSON
        try:
            if not text.endswith("}"):
                last = text.rfind('",')
                if last != -1:
                    text = text[:last+1] + '\n}'
            content = json.loads(text)
        except:
            # Fallback in correct language
            if language == "Telugu":
                content = {
                    "product_name": user_input[:30],
                    "price": "ధర కోసం సంప్రదించండి",
                    "product_listing": f"🌟 {user_input}\n✨ అత్యుత్తమ నాణ్యత మరియు స్వచ్ఛమైన పదార్థాలతో తయారు చేసినది\n🎯 రోజువారీ వాడకానికి మరియు బహుమతిగా ఇవ్వడానికి అనుకూలం\n📲 ఇప్పుడే ఆర్డర్ చేయండి — పరిమిత స్టాక్ మాత్రమే!",
                    "instagram_caption": f"🌟 {user_input}!\n✨ అత్యుత్తమ నాణ్యత హామీ\n💚 స్థానిక కళాకారులచే ప్రేమతో తయారు చేయబడింది\n⚡ పరిమిత స్టాక్ మాత్రమే అందుబాటులో ఉంది\n📲 ఇప్పుడే DM చేయండి మరియు ఆర్డర్ చేయండి!",
                    "hashtags": "#handmade #localproduct #india #supportlocal #quality #affordable #madeinIndia #smallbusiness #తెలుగు #హస్తకళ #స్థానిక #నాణ్యత #కొనుగోలు #విక్రయం #తెలుగువారు",
                    "whatsapp_message": f"🌟 {user_input} అందుబాటులో ఉంది!\n✨ అత్యుత్తమ నాణ్యత హామీ\n💰 సరసమైన ధరలో\n⚡ పరిమిత స్టాక్ మాత్రమే\n📲 ఆర్డర్ కోసం ఇప్పుడే reply చేయండి!",
                    "key_features": f"✅ అత్యుత్తమ నాణ్యమైన ఉత్పత్తి\n✅ సరసమైన ధరలో అందుబాటులో ఉంది\n✅ స్థానిక కళాకారులచే తయారు చేయబడింది"
                }
            else:
                content = {
                    "product_name": user_input[:30],
                    "price": "Contact for price",
                    "product_listing": f"🌟 {user_input}\n✨ Premium quality guaranteed\n🎯 Perfect for daily use and gifting\n📲 Order now — limited stock available!",
                    "instagram_caption": f"🌟 Introducing {user_input}!\n✨ Premium quality at affordable price\n💚 Handcrafted with love by local artisans\n⚡ Limited stock only\n📲 DM us now to order!",
                    "hashtags": "#handmade #localproduct #india #supportlocal #quality #affordable #shoplocal #madeinIndia #smallbusiness #local #artisan #craft #buy #shop #trending",
                    "whatsapp_message": f"🌟 {user_input} now available!\n✨ Premium quality guaranteed\n💰 Best price assured\n⚡ Limited stock only\n📲 Reply now to order!",
                    "key_features": "✅ Premium quality product\n✅ Affordable and value for money\n✅ Handcrafted by skilled local artisans"
                }

    print(">>> FINAL:", json.dumps(content, ensure_ascii=False)[:200])
    return jsonify({"success": True, "data": content})


# ── REGENERATE SECTION ───────────────────────
@app.route('/regenerate-section', methods=['POST'])
def regenerate_section():

    data = request.get_json()
    user_input = data.get('user_input')
    language = data.get('language', 'English')
    section = data.get('section')

    if not user_input or not section:
        return jsonify({"error": "Missing fields"}), 400

    lang_rules = LANGUAGE_RULES.get(language, LANGUAGE_RULES["English"])

    prompt = f"""Generate only the {section} field for this product: {user_input}
Language: {language}
{lang_rules["instruction"]}
Return plain text only in {language}. No extra explanation."""

    headers = {
        "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "Meta-Llama-3.3-70B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": f"Write only in {language}. Return plain text only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    response = requests.post(
        SAMBANOVA_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

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

import threading

def keep_alive():
    while True:
        try:
            requests.get(
                "https://vendorai-at00.onrender.com/ping",
                timeout=10
            )
            print(">>> Keep alive ping sent")
        except:
            pass
        time.sleep(840)  # ping every 14 minutes

if __name__ == '__main__':
    print("🚀 VendorAI running at http://localhost:5000")
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    app.run(debug=True, port=5000)