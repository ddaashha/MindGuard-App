import streamlit as st
import os

st.set_page_config(page_title="Про систему", page_icon="📖")

# Виправляємо шлях до CSS (виходимо з папки pages)
css_path = "style.css" if os.path.exists("style.css") else "../style.css"
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if st.button("⬅️ Назад до аналізу"):
    st.switch_page("app.py")

st.markdown('<div class="main-card">', unsafe_allow_html=True)
st.title("📖 Про технологію PsychAI")
st.write("Тут опис ваших моделей RoBERTa та LSTM...")
st.markdown('</div>', unsafe_allow_html=True)