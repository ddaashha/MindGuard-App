import streamlit as st
import tensorflow as tf
from transformers import pipeline
import joblib
import re
import os
import gdown
import zipfile
from tensorflow.keras.preprocessing.sequence import pad_sequences
import time
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime
from auth_page import show_login_page

# --- БЛОК АВТОМАТИЧНОГО ЗАВАНТАЖЕННЯ МОДЕЛЕЙ ---
def download_models_from_gdrive():
    # ID твоїх файлів з посилань
    MODELS_CONFIG = {
        "models/bilstm_model": "1Jw03wPtIbgmwmWrldNp8TZG1ZzhMucB-",
        "models/lstm_model": "1RPMSSwh6Y7jJDjZyvHmuFfQRc5JT2IK8",
        "models/roberta_model": "1p56mmm-n8TGglvsDDPXYcl0ZvMa1ux9_"
    }

    if not os.path.exists("models"):
        os.makedirs("models")

    for folder_path, file_id in MODELS_CONFIG.items():
        if not os.path.exists(folder_path):
            with st.spinner(f'Завантаження {folder_path}... Зачекайте, це лише раз.'):
                zip_path = folder_path + ".zip"
                url = f'https://drive.google.com/uc?id={file_id}'
                
                # Скачуємо
                gdown.download(url, zip_path, quiet=False)
                
                # Розпаковуємо
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall("models")
                
                # Видаляємо архів після розпаковки
                os.remove(zip_path)

# Викликаємо завантаження перед усім іншим
download_models_from_gdrive()

# --- БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect('mindguard_system.db')
    c = conn.cursor()
    # Створюємо таблицю користувачів (якщо вона зникла)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    # Створюємо таблицю історії
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT,
            user_text TEXT,
            model_used TEXT,
            top_emotion TEXT,
            confidence REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(text, model, emotion, score):
    init_db() # Гарантуємо, що таблиці існують
    conn = sqlite3.connect('mindguard_system.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO history (user_id, timestamp, user_text, model_used, top_emotion, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (st.session_state.user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text, model, emotion, score))
    conn.commit()
    conn.close()

def get_history(days=None):
    conn = sqlite3.connect('mindguard_system.db')
    user_id = st.session_state.get('user_id', 0)
    
    base_query = f"SELECT timestamp as Дата, user_text as Текст, model_used as Консультант, top_emotion as Емоція, confidence as Впевненість FROM history WHERE user_id = {user_id}"

    if days == 0:
        query = base_query + " AND date(timestamp) = date('now', 'localtime') ORDER BY id DESC"
    elif days == 7:
        query = base_query + " AND date(timestamp) >= date('now', '-7 days', 'localtime') ORDER BY id DESC"
    else:
        query = base_query + " ORDER BY id DESC"

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Ініціалізація
init_db()

st.set_page_config(page_title="MindGuard", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    show_login_page()
    st.stop()
    
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")


st.markdown("""
<style>
    div.analysis-area button {
        background-color: #1e293b !important;
        color: white !important;
        min-height: 4.8rem !important;
        width: 100% !important;
        border-radius: 20px !important;
        border: none !important;

        font-size: 1.4rem !important;
        font-weight: 750 !important;

        background-image: url('https://img.icons8.com/?size=100&id=HWCi4PO4E8Uf&format=png&color=ffffff') !important;
        background-repeat: no-repeat !important;
        background-position: 25px center !important;
        background-size: 32px !important;
        padding-left: 70px !important;

        box-shadow: 0 4px 15px rgba(30, 41, 59, 0.3) !important;
        transition: all 0.3s ease-in-out !important;
    }

    div.analysis-area button:hover {
        background-color: #6366f1 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
    }

    div.analysis-area button p {
        font-size: 1.4rem !important;
        color: white !important;
        font-weight: 750 !important;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
    header, [data-testid="stHeader"] { display: none !important; }
    .stApp { margin-top: 0 !important; }

    .block-container {
        padding-top: 80px !important;
        padding-left: 5% !important;
        padding-right: 5% !important;
        max-width: 100% !important;
    }

    .custom-header-fixed {
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 70px;
        background-color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 5%;
        border-bottom: 1px solid #e2e8f0;
        z-index: 999999;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }

    .mg-nav-item {
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
    }

    .mg-nav-item:hover {
        transform: translateY(-2px) !important;
        filter: brightness(0.9) !important;
    }

    .mg-menu-btn:hover {
        background-color: #f1f5f9 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }

    .mg-login-btn:hover {
        background-color: #6366F1 !important;
        border-color: #6366F1 !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)


header_html = f"""
<div class="custom-header-fixed">
    <div style="display: flex; align-items: center; gap: 12px;">
        <img src="https://img.icons8.com/?size=100&id=2070&format=png&color=6366F1" width="30">
        <span style="font-weight: 800; font-size: 1.3rem; color: #1e293b; letter-spacing: -0.5px; font-family: sans-serif;">MindGuard</span>
    </div>
    <div style="display: flex; align-items: center; gap: 18px; font-family: sans-serif;">
        <div class="mg-nav-item" style="display: flex; align-items: center; gap: 6px; color: #64748b; font-size: 0.9rem; font-weight: 500;">
            <img src="https://img.icons8.com/?size=100&id=3685&format=png&color=1E293B" width="22">UA
        </div>
        <div class="mg-nav-item mg-menu-btn" title="Розширення функцій меню з'явиться згодом" 
             style="padding: 6px 14px; border-radius: 10px; background: #f1f5f9; color: #475569; font-size: 0.85rem; font-weight: 600;">
             Меню
        </div>
        <div class="mg-nav-item mg-login-btn" title="Особистий кабінет у розробці" 
             style="padding: 6px 18px; background: #eff6ff; border: 1px solid #dbeafe; border-radius: 12px; color: #1e40af; font-weight: 700; font-size: 0.85rem;">
             Профіль
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

st.markdown(header_html, unsafe_allow_html=True)

@st.cache_resource
def load_models():
    # Шляхи тепер відповідають структурі розпакованих ZIP
    try:
        classifier_rb = pipeline("text-classification", model="models/roberta_model", use_fast=False)
    except: classifier_rb = None

    try:
        model_lstm = tf.keras.models.load_model("models/lstm_model/lstm_model.keras")
        tokenizer_lstm = joblib.load("models/lstm_model/tokenizer_lstm.pkl")
        id2label_lstm = joblib.load("models/lstm_model/id2label_lstm.pkl")
    except: model_lstm, tokenizer_lstm, id2label_lstm = None, None, None

    try:
        model_bilstm = tf.keras.models.load_model("models/bilstm_model/bilstm_model.keras")
        tokenizer_bilstm = joblib.load("models/bilstm_model/tokenizer_bilstm.pkl")
        id2label_bilstm = joblib.load("models/bilstm_model/id2label_bilstm.pkl")
    except: model_bilstm, tokenizer_bilstm, id2label_bilstm = None, None, None

    return classifier_rb, model_lstm, tokenizer_lstm, id2label_lstm, model_bilstm, tokenizer_bilstm, id2label_bilstm

rb_model, lstm_model, lstm_tok, lstm_labels, bilstm_model, bilstm_tok, bilstm_labels = load_models()

def clean_text(t):
    t = t.lower()
    t = re.sub(r"[^а-щьюяґєії'\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


main_col, info_col = st.columns([0.7, 0.3], gap="large")

with main_col:
    st.markdown("""
        <div class="custom-card">
            <div class="header-container">
                <img src="https://img.icons8.com/?size=100&id=2070&format=png&color=6366F1" class="header-logo">
                <div class="header-text-inline">
                    <h1 class="header-title-inline">MindGuard - твій простір ментальної підтримки</h1>
                </div>
            </div>
            <p class="description-text">
            Ти не наодинці зі своїми думками. Розкажи нам про них, і ми підкажемо твій емоційний вектор за допомогою нейромереж. </p>
        </div>
    """, unsafe_allow_html=True)

    model_choice = st.radio(
        "Оберіть ШІ-консультанта для аналізу:",
        ("ШІ - консультант 1 (RoBERTa)", "ШІ - консультант 2 (LSTM)", "ШІ - консультант 3 (BiLSTM)"),
        index=0,
        horizontal=True,
        help="Кожен консультант використовує різну архітектуру нейромереж для оцінки вашого стану."
    )

    # Прив'язка вибору до типу моделі
    if "RoBERTa" in model_choice:
        model_type = "Модель RoBERTa"
    elif "BiLSTM" in model_choice:
        model_type = "Мережа BiLSTM"
    else:
        model_type = "Мережа LSTM"

    user_input = st.text_area(
        "Ваш поточний стан:",
        placeholder="Напишіть те, що вас зараз турбує...",
        height=150,
        help="Ви можете писати у вільній формі. Чим більше деталей, тим точнішим буде аналіз."
    )


    viz_type = st.selectbox(
        "Оберіть спосіб візуалізації результатів:",
        ["Кругова діаграма", "Стовпчикова гістограма", "Радарний профіль емоцій"],
        index=0,
        help="Виберіть, як саме ви хочете побачити розподіл ваших емоцій."
    )
    st.markdown('<div class="analysis-area">', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_btn, col_right = st.columns([1, 2, 1])

    with col_btn:
        start_analysis = st.button("Почати аналіз", key="analysis_btn")

    if start_analysis:
        if not user_input.strip():
            st.warning("Будь ласка, введіть текст.")
        else:
            cleaned = clean_text(user_input)
            status_text = st.empty()
            progress_bar = st.progress(0)

            wait_time = 2.0
            steps = 100
            for i in range(steps):
                time.sleep(wait_time / steps)
                current_left = round(wait_time - (i * (wait_time / steps)), 1)
                if current_left < 0: current_left = 0
                status_text.markdown(f"Залишилось: `{current_left} сек.`")
                progress_bar.progress(i + 1)

            status_text.empty()
            progress_bar.empty()

            st.subheader("Результат аналізу:")

            labels = []
            scores = []

            if "RoBERTa" in model_type and rb_model:
                results = sorted(rb_model(user_input)[0], key=lambda x: x['score'], reverse=True)
                for res in results:
                    labels.append(res['label'])
                    scores.append(res['score'])

                    col_label, col_score = st.columns([0.4, 0.6])
                    percent = round(res['score'] * 100)
                    col_label.write(f"**{res['label']}** — `{percent}%` ")
                    col_score.progress(res['score'])


            elif "BiLSTM" in model_type and bilstm_model:

                seq = bilstm_tok.texts_to_sequences([cleaned])

                padded = pad_sequences(seq, maxlen=80, padding='post')

                preds = bilstm_model.predict(padded, verbose=0)[0]

                res_list = sorted(zip(bilstm_labels.values(), preds), key=lambda x: x[1], reverse=True)

                for label, score in res_list:
                    labels.append(label)

                    scores.append(float(score))

                    col_label, col_score = st.columns([0.4, 0.6])

                    percent = round(float(score) * 100)

                    col_label.write(f"**{label}** — `{percent}%` ")

                    col_score.progress(float(score))


            elif "LSTM" in model_type and lstm_model:
                seq = lstm_tok.texts_to_sequences([cleaned])
                padded = pad_sequences(seq, maxlen=80, padding='post')
                preds = lstm_model.predict(padded, verbose=0)[0]
                lstm_res = sorted(zip(lstm_labels.values(), preds), key=lambda x: x[1], reverse=True)
                for label, score in lstm_res:
                    labels.append(label)
                    scores.append(float(score))

                    col_label, col_score = st.columns([0.4, 0.6])
                    percent = round(float(score) * 100)
                    col_label.write(f"**{label}** — `{percent}%` ")
                    col_score.progress(float(score))

            if labels and scores:
                top_emo = labels[0]
                top_score = float(scores[0])
                save_to_db(user_input, model_choice, top_emo, top_score)

                st.write("---")
                df = pd.DataFrame({"Емоція": labels, "Частка": scores})

                if viz_type == "Кругова діаграма":
                    fig = px.pie(df, values='Частка', names='Емоція', hole=0.5,
                                 color_discrete_sequence=px.colors.qualitative.Pastel, height=400)
                    fig.update_traces(textposition='inside', textinfo='percent+label')

                elif viz_type == "Стовпчикова гістограма":
                    fig = px.bar(df, x='Емоція', y='Частка', color='Емоція', text_auto='.1%',
                                 color_discrete_sequence=px.colors.qualitative.Pastel, height=400)
                    fig.update_layout(showlegend=False, yaxis_tickformat='.0%')

                elif viz_type == "Радарний профіль емоцій":
                    import plotly.graph_objects as go

                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(r=scores + [scores[0]], theta=labels + [labels[0]], fill='toself',
                                                  line_color='#6366f1'))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False,
                                      height=450)

                fig.update_layout(margin=dict(t=30, b=30, l=30, r=30), paper_bgcolor='rgba(0,0,0,0)',
                                  font=dict(size=14))

                st.plotly_chart(fig, use_container_width=True)

            st.success("Аналіз завершено успішно")

    st.markdown('</div>', unsafe_allow_html=True)

with info_col:
    st.markdown("""
<div style="background: white; padding: 25px; border-radius: 20px; border: 1px solid #efefef; box-shadow: 0px 4px 10px rgba(0,0,0,0.03);">
<h3 style="margin-top:0; color:#1e293b; display: flex; align-items: center; gap: 12px; font-size: 1.6rem;">
<img src="https://img.icons8.com/?size=100&id=tIzSQyc7iRz9&format=png&color=1E293B" width="30">
Про додаток</h3>

<p style="color: #475569; font-size: 1.15rem; line-height: 1.6;">
<b>MindGuard</b> - це твій цифровий помічник для саморефлексії. Він допомагає зрозуміти, що насправді стоїть за твоїми словами, коли емоції важко висловити прямо.
</p>

<div style="margin: 20px 0;">
    <p style="color: #6366f1; font-size: 1rem; font-weight: bold; margin-bottom: 10px; text-transform: uppercase;">Що дає MindGuard?</p>
    <div style="background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #edf2f7; margin-bottom: 12px; display: flex; align-items: flex-start; gap: 14px;">
        <img src="https://img.icons8.com/?size=100&id=21101&format=png&color=6366f1" width="28" style="margin-top: 2px;">
        <div>
            <b style="font-size: 1.15rem; color: #1e293b; display: block;">Погляд з боку</b>
            <p style="font-size: 1rem; color: #64748b; margin: 4px 0 0 0; line-height: 1.4;">Допомагає побачити емоції, які важко помітити самому в потоці думок.</p>
        </div>
    </div>
    <div style="background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #edf2f7; display: flex; align-items: flex-start; gap: 14px;">
        <img src="https://img.icons8.com/?size=100&id=18082&format=png&color=6366f1" width="28" style="margin-top: 2px;">
        <div>
            <b style="font-size: 1.15rem; color: #1e293b; display: block;">Емоційна розрядка</b>
            <p style="font-size: 1rem; color: #64748b; margin: 4px 0 0 0; line-height: 1.4;">Просте виписування думок вже знижує стрес.</p>
        </div>
    </div>
</div>

<p style="font-size: 1.1rem; color: #1e3a8a; background: #eff6ff; padding: 15px; border-radius: 12px; border-left: 5px solid #6366f1;">
<b>Порада:</b> Пиши відкрито та детально, так нейромережа зможе побачити справжню картину та дати коректніший результат.
</p>

<div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 18px;">
<img src="https://img.icons8.com/?size=100&id=94&format=png&color=94A3B8" width="16">
<p style="color: #94a3b8; font-size: 0.95rem; margin: 0;">Твої думки приватні й ніде не зберігаються</p>
</div>
</div>
""", unsafe_allow_html=True)
st.write("---")
col_header, col_filter = st.columns([0.7, 0.3])

with col_header:
    st.subheader("Архів твоїх думок")

with col_filter:
    period_label = st.selectbox(
        "Період:",
        ["Весь архів", "За сьогодні", "За останній тиждень"],
        label_visibility="collapsed",
        index=0
    )

days_map = {
    "За сьогодні": 0,
    "За останній тиждень": 7,
    "Весь архів": None
}

try:
    history_df = get_history(days_map[period_label])

    if not history_df.empty:
        history_df['Впевненість'] = history_df['Впевненість'].apply(
            lambda x: f"{round(float(str(x).replace('%', '')) if '%' in str(x) else x * 100)}%"
        )

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Текст": st.column_config.TextColumn("Що було на душі", width="large"),
                "Дата": st.column_config.DatetimeColumn("Час запису", format="D MMM, HH:mm"),
            }
        )
    else:
        st.warning(f"За обраний період записів не знайдено.")
except Exception as e:
    st.error(f"Помилка завантаження архіву: {e}")



with st.container():
    st.markdown("<br>", unsafe_allow_html=True)


st.markdown("""
    <div class="footer-warning">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
            <img src="https://img.icons8.com/?size=100&id=KarJz0n4bZSj&format=png&color=EF4444" width="32">
            <h3>Важливе попередження</h3>
        </div>
        <p>Цей інструмент працює на базі математичних моделей і <b>не є заміною реального лікаря</b>. 
        Штучний інтелект може помилятися, він не розуміє вашого життєвого досвіду повністю. Довіряти цим прогнозам на 100% не варто, вони мають лише ознайомчий характер.</p>
        <p>Якщо вам погано, ви відчуваєте безвихідь або маєте cуїцидальні думки - <b>не залишайтеся наодинці</b>.</p>
        <hr>
        <p style="display: flex; align-items: center; gap: 8px;">
        <img src="https://img.icons8.com/?size=100&id=9730&format=png&color=000000" width="20">
        <b>Гарячі лінії допомоги в Україні:</b>
        </p>
        <ul>
            <li><span class="help-line">7333</span> - Lifeline Ukraine (запобігання самогубствам та підтримки психічного здоров'я, цілодобово)</li>
            <li><span class="help-line">0 800 60 20 19</span> - Гаряча лінія для медичної консультації через контакт-центр МОЗ (цілодобово) </li>
            <li><span class="help-line">1547</span> - Урядова лінія. Підтримка постраждалих від домашнього насильства, а також загальна психологічна допомога (цілодобово)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
