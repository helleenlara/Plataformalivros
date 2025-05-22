
import streamlit as st

def get_usuario_logado():
    return st.session_state.get("logged_user", None)
