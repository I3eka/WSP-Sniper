import streamlit as st


def apply_styles():
    st.set_page_config(page_title="WSP Sniper UI", page_icon="🎯", layout="wide")
    st.markdown(
        """
        <style>
        .timer-box {
            padding: 10px; border: 1px solid #444; border-radius: 5px;
            background: #0e1117; color: #00ff00; text-align: center;
            font-family: monospace; font-size: 1.2em; margin-bottom: 20px;
        }
        button[kind="primary"] { height: 3rem; font-weight: bold; }
        </style>
    """,
        unsafe_allow_html=True,
    )
