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
st.write(os.getenv("OPENAI_API_KEY"))
# =========================
# 🎨 UI
# =========================
st.markdown("""
<style>
body { background: #F4F6F1; }
.block {
    background: white;
    padding: 20px;
    border-radius: 20px;
    margin-bottom: 15px;
}
button {
    border-radius: 999px !important;
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
    st.title("🌿 Acolher")

    mood = st.select_slider(
        "Como você está hoje?",
        options=["😔", "😐", "🙂", "😊", "✨"]
    )

    if st.button("Começar escrita"):
        st.session_state.entry["mood_before"] = mood
        go("write")

    if st.button("📖 Histórico"):
        go("history")

    if st.button("✨ Ver padrões"):
        go("insights")

# =========================
# ✍️ WRITE
# =========================
def write():
    st.subheader("Escreva livremente")

    content = st.text_area("")

    mood_after = st.select_slider(
        "Como você se sente agora?",
        options=["😔", "😐", "🙂", "😊", "✨"]
    )

    if st.button("Salvar"):
        save_entry({
            "id": str(uuid.uuid4()),
            "date": datetime.now().isoformat(),
            "mood_before": st.session_state.entry["mood_before"],
            "mood_after": mood_after,
            "content": content
        })
        go("done")

# =========================
# 📖 HISTORY
# =========================
def history():
    st.title("📖 Histórico")

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
    st.success("Você se escutou hoje 🌿")
    if st.button("Voltar"):
        go("home")

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