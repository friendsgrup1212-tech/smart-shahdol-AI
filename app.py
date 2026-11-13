
# ============================================================
# SMART SHAHdol AI - DISTRICT INFORMATION CHATBOT
# Google Colab + Gradio + DuckDuckGo + SQLite
# Complete Project in ONE CELL
# ============================================================

import sys
import subprocess
import os
import sqlite3
import datetime
import re
import warnings

warnings.filterwarnings("ignore")

print("Installing required libraries...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "gradio", "ddgs"
])

import gradio as gr
from ddgs import DDGS

# ------------------------------------------------------------
# 1. DATABASE SETUP (Google Drive Persistence)
# ------------------------------------------------------------

try:
    from google.colab import drive
    drive.mount('/content/drive')
    DB_PATH = "/content/drive/MyDrive/Shahdol_AI/shahdol.db"
except Exception:
    DB_PATH = "/content/shahdol.db"

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT,
    source TEXT,
    category TEXT,
    created_at TEXT
)
""")

conn.commit()

# ------------------------------------------------------------
# 2. SHAHdol BASIC KNOWLEDGE
# ------------------------------------------------------------

DISTRICT_INFO = """
शहडोल मध्य प्रदेश के उत्तर-पूर्वी भाग में स्थित जिला है।
जिला मुख्यालय: शहडोल।
क्षेत्रफल: 5610 वर्ग किलोमीटर (जिला पोर्टल के अनुसार)।
जिले में हिंदी सहित स्थानीय भाषाओं का प्रयोग होता है।
प्रमुख क्षेत्र: सोहागपुर, बुढ़ार, ब्यौहारी,
जयसिंहनगर और गोहपारू।
प्रमुख विषय: कृषि, वन, शिक्षा, स्वास्थ्य,
पर्यटन और आदिवासी संस्कृति।
आधिकारिक वेबसाइट: https://shahdol.nic.in/
"""

OFFICIAL_SOURCES = [
    "https://shahdol.nic.in/",
    "https://shahdol.nic.in/en/about-district/",
    "https://shahdol.nic.in/en/health/",
    "https://shahdol.nic.in/en/directory/"
]

# ------------------------------------------------------------
# 3. CATEGORY DETECTION
# ------------------------------------------------------------

def get_category(question):

    q = question.lower()

    if any(x in q for x in [
        "news", "khabar", "समाचार", "खबर",
        "आज की खबर", "local news"
    ]):
        return "Local News"

    if any(x in q for x in [
        "kheti", "fasal", "farmer", "agriculture",
        "कृषि", "किसान", "फसल", "खाद", "बीज",
        "खेती", "मंडी"
    ]):
        return "Agriculture"

    if any(x in q for x in [
        "hospital", "doctor", "health", "स्वास्थ्य",
        "अस्पताल", "डॉक्टर", "एम्बुलेंस", "दवाई"
    ]):
        return "Health"

    if any(x in q for x in [
        "school", "college", "education",
        "शिक्षा", "स्कूल", "कॉलेज"
    ]):
        return "Education"

    if any(x in q for x in [
        "tourism", "temple", "घूमना", "मंदिर",
        "पर्यटन", "दर्शनीय"
    ]):
        return "Tourism"

    if any(x in q for x in [
        "weather", "mausam", "मौसम", "बारिश"
    ]):
        return "Weather"

    return "District Information"


# ------------------------------------------------------------
# 4. INTERNET SEARCH ENGINE
# ------------------------------------------------------------

def search_web(question):

    query = question + " Shahdol Madhya Pradesh"

    results = []

    try:
        with DDGS() as ddgs:

            search_results = ddgs.text(
                query,
                max_results=6
            )

            for item in search_results:

                title = item.get("title", "")
                body = item.get("body", "")
                link = item.get("href", "")

                if title or body:
                    results.append({
                        "title": title,
                        "body": body,
                        "link": link
                    })

    except Exception as e:
        print("Search error:", str(e))

    return results


# ------------------------------------------------------------
# 5. SAVE INFORMATION TO DATABASE
# ------------------------------------------------------------

def save_knowledge(question, answer, source, category):

    try:

        conn.execute("""
        INSERT INTO knowledge
        (question, answer, source, category, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (
            question,
            answer,
            source,
            category,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

    except Exception as e:
        print("Database error:", e)


# ------------------------------------------------------------
# 6. GET PREVIOUSLY SAVED INFORMATION
# ------------------------------------------------------------

def get_saved_information(question):

    words = [
        w for w in re.findall(r'\w+', question.lower())
        if len(w) > 3
    ]

    if not words:
        return []

    conditions = " OR ".join(
        ["LOWER(question) LIKE ?"] * min(len(words), 5)
    )

    params = ["%" + w + "%" for w in words[:5]]

    try:
        cursor = conn.execute(
            f"""
            SELECT answer, source, category
            FROM knowledge
            WHERE {conditions}
            ORDER BY id DESC
            LIMIT 3
            """,
            params
        )

        return cursor.fetchall()

    except Exception:
        return []


# ------------------------------------------------------------
# 7. MAIN CHATBOT
# ------------------------------------------------------------

def shahdol_chat(message, history):

    if not message.strip():
        return "कृपया अपना सवाल लिखिए।"

    category = get_category(message)

    # Basic district information
    basic_words = [
        "शहडोल क्या है", "shahdol district",
        "शहडोल जिला", "about shahdol"
    ]

    if any(x in message.lower() for x in basic_words):
        basic_info = DISTRICT_INFO
    else:
        basic_info = ""

    # Search previous database information
    saved = get_saved_information(message)

    # Search latest internet information
    results = search_web(message)

    response = ""

    response += f"## 🤖 SMART SHAHdol AI\n"
    response += f"**विषय:** {category}\n\n"

    if basic_info:
        response += basic_info + "\n\n"

    if results:

        response += "### 🔎 इंटरनेट से मिली जानकारी\n\n"

        for i, item in enumerate(results, 1):

            response += f"**{i}. {item['title']}**\n\n"
            response += item['body'] + "\n\n"

            if item['link']:
                response += f"[स्रोत देखें]({item['link']})\n\n"

            # Save each search result
            save_knowledge(
                message,
                item['title'] + "\n" + item['body'],
                item['link'],
                category
            )

        response += "---\n"
        response += "ये इंटरनेट सर्च के परिणाम हैं। "
        response += "इनकी तारीख और आधिकारिक पुष्टि जरूर जाँचें।\n"

    else:

        response += """
इंटरनेट सर्च अभी उपलब्ध नहीं है।

आपका सवाल इंटरनेट से खोजा नहीं जा सका।
कृपया दोबारा कोशिश करें या अपना सवाल थोड़ा बदलें।
"""

    # Show previously saved knowledge
    if saved:

        response += "\n### 💾 आपके डेटाबेस में संबंधित जानकारी\n\n"

        for answer, source, old_category in saved:

            response += f"- **{old_category}:** {answer[:400]}\n"

            if source:
                response += f"  [पुराना स्रोत]({source})\n"

    # Health safety
    if category == "Health":
        response += """
\n⚕️ **स्वास्थ्य सूचना:** यह chatbot सामान्य जानकारी देता है,
डॉक्टर की सलाह का विकल्प नहीं है।
आपातकाल में 108 एम्बुलेंस सेवा का उपयोग करें।
"""

    if category == "Agriculture":
        response += """
\n🌾 **किसानों के लिए:** फसल और दवाओं के उपयोग से पहले
स्थानीय कृषि विशेषज्ञ या कृषि विभाग से सलाह लें।
"""

    return response


# ------------------------------------------------------------
# 8. DATABASE STATISTICS
# ------------------------------------------------------------

def database_info():

    count = conn.execute(
        "SELECT COUNT(*) FROM knowledge"
    ).fetchone()[0]

    return f"💾 Database में कुल {count} जानकारी सेव हैं।"


def show_database():

    rows = conn.execute("""
        SELECT question, category, source, created_at
        FROM knowledge
        ORDER BY id DESC
        LIMIT 30
    """).fetchall()

    if not rows:
        return "अभी डेटाबेस खाली है।"

    output = "## 📚 Saved Shahdol Information\n\n"

    for q, cat, source, date in rows:
        output += f"**{cat}** | {date}\n\n"
        output += f"सवाल: {q}\n\n"

        if source:
            output += f"[Source]({source})\n\n"

        output += "---\n"

    return output


# ------------------------------------------------------------
# 9. GRADIO PROFESSIONAL UI
# ------------------------------------------------------------

custom_css = """
.gradio-container {
    max-width: 1100px !important;
    margin: auto !important;
}
#header {
    text-align: center;
    padding: 25px;
    border-radius: 18px;
    background: linear-gradient(120deg, #064e3b, #15803d);
    color: white;
}
#header h1 {
    font-size: 34px;
    font-weight: 800;
}
#header p {
    font-size: 16px;
}
"""

with gr.Blocks(
    theme=gr.themes.Soft(
        primary_hue="green",
        secondary_hue="emerald"
    ),
    css=custom_css,
    title="SMART SHAHdol AI"
) as demo:

    gr.HTML("""
    <div id="header">
        <h1>🌿 SMART SHAHdol AI</h1>
        <p>आपके अपने जिले शहडोल का डिजिटल जानकारी केंद्र</p>
        <p>News | Agriculture | Health | Education | Tourism</p>
    </div>
    """)

    gr.Markdown(
        "### 🙏 नमस्कार! मैं आपका Shahdol District AI Assistant हूँ।"
    )

    gr.Markdown(
        "मुझसे शहडोल जिले से जुड़ा कोई भी सवाल हिंदी या English में पूछिए।"
    )

    gr.ChatInterface(
        fn=shahdol_chat,
        chatbot=gr.Chatbot(
            height=450,
            placeholder="शहडोल के बारे में सवाल पूछें..."
        ),
        textbox=gr.Textbox(
            placeholder="जैसे: शहडोल में कृषि की मुख्य फसल कौन सी है?",
            lines=2
        ),
        examples=[
            "शहडोल जिले का इतिहास बताओ",
            "शहडोल की आज की ताजा खबरें बताओ",
            "शहडोल में किसानों के लिए योजनाएं बताओ",
            "शहडोल के सरकारी अस्पतालों की जानकारी दो",
            "शहडोल के पर्यटन स्थल बताओ",
            "शहडोल के कॉलेजों की जानकारी दो"
        ]
    )

    with gr.Accordion("📚 Saved Information Database", open=False):

        gr.Markdown("आपकी सर्च की गई जानकारी यहाँ सेव होती है।")

        stats = gr.Markdown(database_info())

        view_btn = gr.Button("देखें: सेव की गई जानकारी")

        saved_output = gr.Markdown()

        view_btn.click(
            fn=show_database,
            outputs=saved_output
        )

    gr.Markdown("""
    ---
    **SMART SHAHdol AI | Made for Shahdol, Madhya Pradesh**

    Official District Website:
    https://shahdol.nic.in/

    Emergency: 108 Ambulance | 112 Emergency
    """)

# ------------------------------------------------------------
# 10. START PROJECT
# ------------------------------------------------------------

print("\nSMART SHAHdol AI is starting...")
print("Database:", DB_PATH)

demo.launch(
    share=True,
    debug=False
)
