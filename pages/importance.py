import streamlit as st
import os

st.set_page_config(page_title="Поради", page_icon="🌿")

if os.path.exists("style.css"):
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown('<div class="main-card">', unsafe_allow_html=True)
st.title("🌿 Чому це важливо?")
st.info("Тут можна розмістити корисні поради, контакти психологів та статті.")
st.markdown('</div>', unsafe_allow_html=True)