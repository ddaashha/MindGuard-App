import streamlit as st
import os
from database import login_user, add_user


def show_login_page():
    if os.path.exists("auth_style.css"):
        with open("auth_style.css", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown('<div class="auth-header-gradient">', unsafe_allow_html=True)
        st.image("https://img.icons8.com/?size=100&id=2070&format=png&color=ffffff", width=60)
        st.markdown("<h2>MindGuard</h2><p>Твій простір ментального спокою</p></div>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Вхід", "Реєстрація"])

        with tab1:
            with st.form("login_form"):
                user_login = st.text_input("Логін")
                user_password = st.text_input("Пароль", type="password")
                submitted = st.form_submit_button("Увійти", use_container_width=True)

                if submitted:
                    user_data = login_user(user_login, user_password)
                    if user_data:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_data[0]
                        st.session_state.username = user_login
                        st.success(f"Вітаємо, {user_login}!")
                        st.rerun()
                    else:
                        st.error("Невірний логін або пароль")

        with tab2:
            with st.form("reg_form"):
                new_user = st.text_input("Придумайте логін")
                new_pass = st.text_input("Придумайте пароль", type="password")
                reg_submitted = st.form_submit_button("Створити аккаунт", use_container_width=True)

                if reg_submitted:
                    if len(new_user) < 3 or len(new_pass) < 4:
                        st.warning("Логін або пароль занадто короткі")
                    else:
                        if add_user(new_user, new_pass):
                            st.success("Аккаунт створено! Тепер увійдіть у вкладці 'Вхід'")
                        else:
                            st.error("Такий логін вже зайнятий")