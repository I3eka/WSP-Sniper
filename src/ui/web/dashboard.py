import asyncio
import streamlit as st
from loguru import logger
from src.api.client import WSPAsyncClient
from src.core.registration import RegistrationLogic
from src.core.scheduler import TimeScheduler
from src.ui.web.scheduler import render_web_scheduler


# Класс для перенаправления логов в st.status
class StatusSink:
    def __init__(self, status_container):
        self.status = status_container

    def write(self, message):
        # clean message from tags if needed, or just print
        text = message.record["message"]
        # Пишем в UI
        self.status.write(f"👉 {text}")


def render_dashboard():
    st.title("🎯 WSP Sniper Dashboard")
    if not st.session_state.get("logged_in"):
        st.info("👈 Please login via the sidebar to begin.")
        return

    render_web_scheduler()
    st.divider()

    plan = st.session_state.get("plan", {})
    if not plan:
        st.warning("Plan is empty. Select subjects above.")
        return

    st.subheader("🚀 Launch Control")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.json(plan, expanded=False)
    with col2:
        st.markdown("Ready to engage?")
        if st.button("START SNIPER ATTACK", type="primary", use_container_width=True):
            _launch_sequence(plan)


def _launch_sequence(plan):
    # Создаем контейнер статуса
    status_container = st.status("Sniper Operation In Progress...", expanded=True)

    # Добавляем наш Sink в Loguru
    sink_id = logger.add(StatusSink(status_container), format="{message}", level="INFO")

    async def attack_flow():
        scheduler = TimeScheduler()

        status_container.write("⏳ Synchronizing Time...")
        scheduler.sync_ntp()
        target_ts = scheduler.get_target_timestamp()

        status_container.write(f"🎯 Target Timestamp: {target_ts}")
        status_container.write("⏳ Holding for launch time...")

        await scheduler.wait_until_target(target_ts)

        status_container.write("🚀 LAUNCHING REQUESTS!")
        async with WSPAsyncClient() as client:
            await client.login()
            await RegistrationLogic.execute_sniper_attack(client, plan)

    try:
        asyncio.run(attack_flow())
        status_container.update(label="Operation Complete", state="complete")
        st.balloons()
        st.success("Check detailed logs below.")
    except Exception as e:
        status_container.update(label="Operation Failed", state="error")
        st.error(f"Critical Error: {e}")
        logger.exception(e)
    finally:
        # Обязательно удаляем перехватчик, чтобы не дублировать логи потом
        logger.remove(sink_id)
