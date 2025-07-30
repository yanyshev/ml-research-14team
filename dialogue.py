import streamlit as st
from graph import graph

def generate_response(input_text, max_count):
    inputs = {"fraud_scheme": input_text, "messages": [], "max_count": max_count}
    for update in graph.stream(inputs, {"recursion_limit": 100}, stream_mode="updates"):
        if "Скам Скамыч" in update:
            st.info(update["Скам Скамыч"]["messages"][0], icon="🚀")
        if "Иван Иваныч" in update:
            st.info(update["Иван Иваныч"]["messages"][0], icon="🧑")

st.title("...")

with st.form("my_form"):
    text = st.text_area(
        "Схема мошенничества:",
        "Вложение под 100% годовых",
    )
    max_count = st.number_input("Количество сообщений", 5, 50, 10)
    submitted = st.form_submit_button("Submit")
    if submitted:
        generate_response(text, max_count)