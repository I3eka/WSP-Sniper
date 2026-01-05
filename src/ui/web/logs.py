import streamlit as st
from loguru import logger


class StreamlitSink:
    def write(self, message):
        record = message.record
        time = record["time"].strftime("%H:%M:%S")
        level = record["level"].name
        msg = record["message"]
        entry = f"[{time}] {level} | {msg}"
        if "logs" not in st.session_state:
            st.session_state.logs = []
        st.session_state.logs.append(entry)


def setup_web_logger():
    logger.remove()
    logger.add(StreamlitSink(), format="{message}")


def render_logs_widget():
    st.divider()
    st.subheader("📝 Live Operation Logs")
    st.markdown(
        """
        <div class="timer-box">UTC: <span id="utc-time">--:--:--</span> | Local: <span id="local-time">--:--:--</span></div>
        <script>
        setInterval(() => {
            const now = new Date();
            const elU = window.parent.document.getElementById('utc-time');
            const elL = window.parent.document.getElementById('local-time');
            if(elU) elU.innerText = now.toLocaleTimeString('en-GB', {timeZone: 'UTC'});
            if(elL) elL.innerText = now.toLocaleTimeString('en-GB');
        }, 100);
        </script>
        """,
        unsafe_allow_html=True,
    )
    log_container = st.container(height=300)
    with log_container:
        if "logs" in st.session_state and st.session_state.logs:
            st.code("\n".join(st.session_state.logs), language="text")
        else:
            st.info("System ready.")
