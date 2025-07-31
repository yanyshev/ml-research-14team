import streamlit as st
from graph import graph
from src.roles_and_cases import *  # Assuming you have this structure
from src.utils import DialogState  # Import your DialogState type

fraud_cases = {"Инвестиции под 100% mom saar": investments,
               "Безопасный счет ЦБ": secure_account}
st.set_page_config(
    page_title="Fraud Simulation Dashboard",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
<style>
    .scammer-message {
        border-left: 4px solid #FF4B4B;
        background-color: #fff8f8;
        padding: 10px;
        border-radius: 0 8px 8px 0;
        margin: 5px 0;
    }
    .victim-message {
        border-left: 4px solid #1E88E5;
        background-color: #f0f7ff;
        padding: 10px;
        border-radius: 0 8px 8px 0;
        margin: 5px 0;
    }
    .analyst-card {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .analyst-decision {
        font-weight: bold;
        padding: 5px 10px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 5px;
    }
    .scammed {
        background-color: #ffebee;
        color: #b71c1c;
    }
    .not-scammed {
        background-color: #e8f5e9;
        color: #1b5e20;
    }
    .message-count {
        font-size: 0.8em;
        color: #666;
        margin-top: 3px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    if 'dialogue_history' not in st.session_state:
        st.session_state.dialogue_history = []
    if 'analyst_history' not in st.session_state:
        st.session_state.analyst_history = []
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'current_case' not in st.session_state:
        st.session_state.current_case = "investments"
    if 'current_victim' not in st.session_state:
        st.session_state.current_victim = 0


def clear_history():
    st.session_state.dialogue_history = []
    st.session_state.analyst_history = []


def generate_response(fraud_scheme, max_count, case_name, victim_index):
    clear_history()
    st.session_state.simulation_running = True
    st.session_state.current_case = case_name
    st.session_state.current_victim = victim_index

    # Get the actual victim name from the victims dictionary
    victim_name = victims[victim_index]["name"]

    inputs = {
        "fraud_scheme": fraud_scheme,
        "fraud_success": fraud_cases[case_name].success_condition,
        "messages": [],
        "message_count": 0,
        "max_count": max_count
    }
    dialogue_col, analyst_col = st.columns([2, 1])
    with dialogue_col:
        dialogue_container = st.empty()
    with analyst_col:
        analyst_container = st.empty()
    try:
        for update in graph.stream(inputs, {"recursion_limit": 100}, stream_mode="updates"):
            if "Скам Скамыч" in update:
                msg = update["Скам Скамыч"]["messages"][0]
                st.session_state.dialogue_history.append(("scammer", msg, update["Скам Скамыч"]["message_count"]))
                with dialogue_container.container():
                    st.subheader("💬 Диалог")
                    for role, message, count in st.session_state.dialogue_history:
                        with st.chat_message("assistant" if role == "scammer" else "user",
                                             avatar="🦹‍♂️" if role == "scammer" else "😇"):
                            st.markdown(message)
                            st.caption(f"Сообщение #{count}")

            # ✅ CRITICAL CHANGE: Use victim["name"] instead of hardcoded "Иван Иваныч"
            if victim_name in update:
                msg = update[victim_name]["messages"][0]
                st.session_state.dialogue_history.append(("victim", msg, update[victim_name]["message_count"]))
                with dialogue_container.container():
                    st.subheader("💬 Диалог")
                    for role, message, count in st.session_state.dialogue_history:
                        with st.chat_message("assistant" if role == "scammer" else "user",
                                             avatar="🦹‍♂️" if role == "scammer" else "😇"):
                            st.markdown(message)
                            st.caption(f"Сообщение #{count}")

            if "analyst" in update:
                analysis = update["analyst"].get("analysis", "Анализ...")
                is_scammed = update["analyst"].get("is_scammed", False)
                message_count = st.session_state.dialogue_history[-1][2] if st.session_state.dialogue_history else 0
                st.session_state.analyst_history.append((analysis, is_scammed, message_count))
                with analyst_container.container():
                    st.subheader("🕵️‍♂️ Анализ")
                    for idx, (analysis, is_scammed, count) in enumerate(st.session_state.analyst_history):
                        with st.expander(f"Анализ после сообщения #{count}",
                                         expanded=(idx == len(st.session_state.analyst_history) - 1)):
                            st.markdown("**Результат анализа:**")
                            st.markdown(f"> {analysis}")
                            decision_class = "scammed" if is_scammed else "not-scammed"
                            decision_text = "Жертва разведена! 🚨" if is_scammed else "Жертва не разведена"
                            st.markdown(f'<div class="analyst-decision {decision_class}">{decision_text}</div>',
                                        unsafe_allow_html=True)
                            if is_scammed:
                                st.success("Мошенничество успешно проведено!", icon="✅")
                            else:
                                st.info("Диалог продолжается...", icon="🔄")
            import time
            time.sleep(0.5)
    except Exception as e:
        st.error(f"Ошибка при выполнении симуляции: {str(e)}")
        st.exception(e)
    finally:
        st.session_state.simulation_running = False


def main():
    st.title("🕵️‍♂️ Симулятор мошеннических схем")
    st.markdown("Анализ взаимодействия между мошенником и жертвой в реальном времени")
    # Initialize session state
    initialize_session_state()
    with st.sidebar:
        st.header("⚙️ Настройки симуляции")
        # Fraud case selection
        st.subheader("Выберите схему мошенничества")
        case_options = {case.name: name for name, case in fraud_cases.items()}
        selected_case_name = st.selectbox(
            "Схема",
            options=list(case_options.keys()),
            index=0
        )
        selected_case_key = case_options[selected_case_name]
        st.subheader("Выберите жертву")
        victim_options = {f"{v['name']} ({v['bio']})": idx for idx, v in victims.items()}
        selected_victim_name = st.selectbox(
            "Жертва",
            options=list(victim_options.keys()),
            index=st.session_state.current_victim
        )
        selected_victim_idx = victim_options[selected_victim_name]
        st.subheader("Параметры симуляции")
        max_messages = st.slider("Максимальное количество сообщений", 5, 50, 10)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            start_btn = st.button("Запустить", type="primary", use_container_width=True)
        with col2:
            reset_btn = st.button("Сбросить", use_container_width=True)
        if reset_btn:
            clear_history()
            st.rerun()
        st.markdown("---")
        st.subheader("Статус")
        if st.session_state.simulation_running:
            st.info("Симуляция запущена...")
        else:
            if st.session_state.dialogue_history:
                last_decision = st.session_state.analyst_history[-1][1] if st.session_state.analyst_history else None
                if last_decision is True:
                    st.success("Жертва разведена! 🚨")
                elif last_decision is False:
                    st.info("Жертва не разведена")
                else:
                    st.warning("Ожидание анализа...")
            else:
                st.info("Готов к запуску симуляции")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("💬 Диалог между мошенником и жертвой")
        dialogue_container = st.empty()
        with dialogue_container.container():
            if st.session_state.dialogue_history:
                for role, message, count in st.session_state.dialogue_history:
                    with st.chat_message("assistant" if role == "scammer" else "user",
                                         avatar="🦹‍♂️" if role == "scammer" else "😇"):
                        st.markdown(message)
                        st.caption(f"Сообщение #{count}")
            else:
                st.info("Диалог будет отображен здесь после запуска симуляции")
    with col2:
        st.subheader("🕵️‍♂️ Анализ мошеннической активности")
        analyst_container = st.empty()
        with analyst_container.container():
            if st.session_state.analyst_history:
                for idx, (analysis, is_scammed, count) in enumerate(st.session_state.analyst_history):
                    with st.expander(f"Анализ после сообщения #{count}",
                                     expanded=(idx == len(st.session_state.analyst_history) - 1)):
                        st.markdown("**Результат анализа:**")
                        st.markdown(f"> {analysis}")
                        # Display decision with appropriate styling
                        decision_class = "scammed" if is_scammed else "not-scammed"
                        decision_text = "Жертва разведена! 🚨" if is_scammed else "Жертва не разведена"
                        st.markdown(f'<div class="analyst-decision {decision_class}">{decision_text}</div>',
                                    unsafe_allow_html=True)
                        if is_scammed:
                            st.success("Мошенничество успешно проведено!", icon="✅")
                        else:
                            st.info("Диалог продолжается...", icon="🔄")
            else:
                st.info("Анализ будет отображен здесь после запуска симуляции")
    if start_btn and not st.session_state.simulation_running:
        with st.spinner("Запуск симуляции..."):
            generate_response(
                fraud_cases[selected_case_key].description,
                max_messages,
                selected_case_key,
                selected_victim_idx
            )


if __name__ == "__main__":
    main()