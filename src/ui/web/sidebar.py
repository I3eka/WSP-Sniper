import asyncio

import streamlit as st

from config.settings import settings
from src.api.client import WSPAsyncClient
from src.core.scheduler import TimeScheduler


def render_sidebar():
    with st.sidebar:
        st.title("⚙️ Control Panel")
        _render_auth_section()
        st.divider()
        _render_timer_section()


def _render_auth_section():
    st.subheader("Authentication")
    if st.session_state.get("logged_in"):
        st.success(f"Logged in as: **{settings.username}**")
        st.info(f"User ID: {st.session_state.get('user_id')}")
        if st.button("Logout", type="secondary"):
            st.session_state.clear()
            st.rerun()
        return

    username = st.text_input("Username", value=settings.username)
    password = st.text_input("Password", type="password", value=settings.password)

    if st.button("Login & Fetch Subjects", type="primary"):

        async def login_flow():
            async with WSPAsyncClient() as client:
                uid = await client.login()
                subjects = await client.get_accruals()
                return uid, subjects

        try:
            with st.spinner("Authenticating..."):
                uid, subjects = asyncio.run(login_flow())
                st.session_state.user_id = uid
                st.session_state.raw_subjects = subjects
                st.session_state.logged_in = True
                settings.username = username
                settings.password = password
                st.toast(f"Welcome, ID {uid}!")
                st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")


def _render_timer_section():
    st.subheader("Time Synchronization")
    if st.button("Sync NTP"):
        scheduler = TimeScheduler()
        scheduler.sync_ntp()
        st.session_state.time_offset = scheduler.time_offset
        st.toast(f"NTP Offset: {scheduler.time_offset:.4f}s")

    offset = st.session_state.get("time_offset", 0.0)
    st.caption(f"Current Offset: {offset:.4f}s")
    st.divider()
    st.markdown("**/set Target Time (Local)**")
    new_time = st.text_input("HH:MM:SS.fff", value=settings.desired_time_local)
    if new_time != settings.desired_time_local:
        settings.desired_time_local = new_time
