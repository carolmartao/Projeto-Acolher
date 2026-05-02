from __future__ import annotations
import streamlit as st
import sqlite3
import json
import os
import uuid
import random
from datetime import datetime
from typing import Literal
from openai import OpenAI

# =========================
# 🔧 CONFIG
# =========================
st.set_page_config(page_title="Acolher 🌿", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =========================
# 🎨 UI
# =========================
st.markdown("""
<style>
body { background: #F4F6F1; }
    background-color: #F5F7F4;

.block-container {
    max-width: 420px;
    margin: auto;
}

/* Cards */
.card {
    background: white;
    padding: 22px;
    border-radius: 24px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.04);
    margin-bottom: 16px;
}

/* Tipografia */
h1 {
    font-size: 28px;
    font-weight: 600;
}
.subtitle {
    color: #6B7866;
    font-size: 15px;
}

/* Botões */
.stButton > button {
    width: 100%;
    border-radius: 999px;
    background-color: #7FA37A;
    color: white;
    border: none;
    padding: 12px;
    font-size: 16px;
}
.stButton > button:hover {
    background-color: #6A8F65;
}

/* Inputs */
textarea {
    border-radius: 16px !important;
    border: 1px solid #E4E7E2 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 💾 DB
# =========================
def conn():
    return sqlite3.connect("acolher.db", check_same_thread=False)

def init_db():
    c = conn()
    c.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id TEXT,
        date TEXT,
        mood_before TEXT,
        mood_after TEXT,
        content TEXT
    )
    """)
    c.commit()
    c.close()

init_db()

def save_entry(e):
    c = conn()
    c.execute("INSERT INTO entries VALUES (?,?,?,?,?)",
              (e["id"], e["date"], e["mood_before"], e["mood_after"], e["content"]))
    c.commit()
    c.close()

def get_entries():
    c = conn()
    rows = c.execute("SELECT * FROM entries ORDER BY date DESC").fetchall()
    c.close()
    return [{
        "id": r[0],
        "date": r[1],
        "mood_before": r[2],
        "mood_after": r[3],
        "content": r[4],
    } for r in rows]

# =========================
# 🤖 IA
# =========================
def analyze(entries):
    trimmed = entries[:40]

    prompt = f"""
    Analise padrões emocionais dessas entradas:

    {json.dumps(trimmed, ensure_ascii=False)}

    Retorne JSON com:
    summary, insights, questions
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Seja empático e não clínico."},
            {"role": "user", "content": prompt}
        ]
    )

    return json.loads(res.choices[0].message.content)

# =========================
# 🧠 ESTADO
# =========================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "entry" not in st.session_state:
    st.session_state.entry = {}

def go(p):
    st.session_state.page = p
    st.rerun()

# =========================
# 🌿 HOME
# =========================
def home():
def home():
    st.markdown("## 🌿 Acolher")
    st.markdown("<p class='subtitle'>Um espaço gentil para você</p>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    mood = st.select_slider(
        "Como você chega hoje?",
        options=["😔", "😐", "🙂", "😊", "✨"]
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Começar escrita ✍️"):
        st.session_state.entry["mood_before"] = mood
        go("write")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 Histórico"):
            go("history")
    with col2:
        if st.button("✨ Padrões"):
            go("insights")


# =========================
# ✍️ WRITE
# =========================
def write():
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown("### ✍️ Escreva livremente")

    content = st.text_area(
        "",
        height=220,
        placeholder="Comece pelo que vier..."
    )

    mood_after = st.select_slider(
        "Como você se sente agora?",
        options=["😔", "😐", "🙂", "😊", "✨"]
    )

    if st.button("Guardar esse momento 🌿"):
        save_entry({
            "id": str(uuid.uuid4()),
            "date": datetime.now().isoformat(),
            "mood_before": st.session_state.entry["mood_before"],
            "mood_after": mood_after,
            "content": content
        })
        go("done")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 📖 HISTORY
# =========================
def history():
    st.markdown("## 📖 Histórico")

    for e in get_entries():
        with st.expander(e["date"]):
            st.write(e["content"])

    if st.button("Voltar"):
        go("home")



# =========================
# ✨ INSIGHTS
# =========================
def insights():
    st.title("✨ Padrões emocionais")

    entries = get_entries()

    if st.button("Gerar análise"):
        with st.spinner("Analisando..."):
            r = analyze(entries)

        st.markdown("### 🧠 Resumo")
        st.write(r.get("summary"))

        st.markdown("### 💡 Insights")
        for i in r.get("insights", []):
            st.write("-", i)

        st.markdown("### ❓ Perguntas")
        for q in r.get("questions", []):
            st.write(">", q)

    if st.button("Voltar"):
        go("home")

# =========================
# 🌱 DONE
# =========================
def done():
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown("### 🌱 Você se escutou hoje")
    st.markdown("<p class='subtitle'>Isso já é suficiente por agora.</p>", unsafe_allow_html=True)

    if st.button("Voltar"):
        go("home")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# ROUTER
# =========================
pages = {
    "home": home,
    "write": write,
    "history": history,
    "insights": insights,
    "done": done
}

pages[st.session_state.page]()