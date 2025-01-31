import streamlit as st
from loginpage import login
from annotation_tool import annotation_tool
from download_page import download

# Page configuration
st.set_page_config(layout="wide")

# Initialize session state
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None

def main():
    if not st.session_state['logged_in']:
        login()
    else:
        # Navigation header
        col1, col2, col3, col4 = st.columns([6,1,1,1])
        with col2:
            if st.button("Annotate"):
                st.session_state['page'] = 'annotation'
                st.rerun()
        with col3:
            if st.button("Download"):
                st.session_state['page'] = 'download'
                st.rerun()
        with col4:
            if st.button("Logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # Page routing
        if st.session_state['page'] == 'annotation':
            annotation_tool()
        elif st.session_state['page'] == 'download':
            download()

if __name__ == "__main__":
    main()