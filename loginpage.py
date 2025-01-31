import streamlit as st
import hashlib
from utils import Database
db = Database()
def authenticate(username, password):
    user = db.get_collection("Users").find_one({"username": username})
    if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
        return True
    return False

def login():
    st.title("Post Discharge Annotation Tool")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['page'] = 'annotation'
                st.rerun()
            else:
                st.error("Invalid username or password")