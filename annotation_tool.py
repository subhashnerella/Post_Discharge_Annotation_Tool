import streamlit as st
import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import hashlib


# Set the page layout to wide mode
st.set_page_config(layout="wide")

# Connect to MongoDB
uri = st.secrets["MONGODB_URI"]

client = MongoClient(uri, server_api=ServerApi('1'))
db = client["Post_Discharge"]
collection = db["Annotation"]
users_collection = db["Users"]



# Authentication function
def authenticate(username, password):
    user = users_collection.find_one({"username": username})
    if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
        return True
    return False

# Login page
def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.rerun()
        else:
            st.error("Invalid username or password")

# Main annotation tool
def annotation_tool():
    st.title('Post Discharge Chatbot Annotation Tool')

    left_column, right_column = st.columns(2)

    # Initialize user-specific session state variables
    if 'credentials' not in st.session_state:
        st.session_state['credentials'] = ["Doctor", "Nurse", "General User", "Other"]
    if 'tags' not in st.session_state:
        st.session_state['tags'] = ["sepsis", "ICU", "delirium", "PICS"]
    if 'selected_tags' not in st.session_state:
        st.session_state['selected_tags'] = []
    if 'comments' not in st.session_state:
        st.session_state['comments'] = [{"comment": "", "credential": "Doctor", "sub_comments": []}]

    # Left column: Query and comments
    with left_column:
        st.header("Extract Question and Answers")
        annotator_name = st.text_input("Annotator Name", value=st.session_state['username'], disabled=True)
        question = st.text_area("Enter the question", help='Copy-paste the question from the forum post')

        st.subheader("Comments")
        for idx, comment_data in enumerate(st.session_state['comments']):
            comment_col, credential_col = st.columns(2)
            with comment_col:
                st.session_state['comments'][idx]['comment'] = st.text_area(
                    f"Enter the comment {idx + 1}", 
                    value=comment_data['comment'], 
                    key=f"comment_{idx}"
                )
            with credential_col:
                st.session_state['comments'][idx]['credential'] = st.selectbox(
                    f"Select credential for comment {idx + 1}",
                    st.session_state['credentials'],
                    index=st.session_state['credentials'].index(comment_data['credential']),
                    key=f"credential_{idx}"
                )

            # Sub-comments section
            st.markdown(f"**Sub-comments for Comment {idx + 1}:**")
            for sub_idx, sub_comment in enumerate(comment_data['sub_comments']):
                sub_comment_col, sub_credential_col = st.columns(2)
                with sub_comment_col:
                    comment_data['sub_comments'][sub_idx]['comment'] = st.text_area(
                        f"Sub-comment {sub_idx + 1} for Comment {idx + 1}", 
                        value=sub_comment['comment'], 
                        key=f"sub_comment_{idx}_{sub_idx}"
                    )
                with sub_credential_col:
                    comment_data['sub_comments'][sub_idx]['credential'] = st.selectbox(
                        f"Select credential for Sub-comment {sub_idx + 1} of Comment {idx + 1}",
                        st.session_state['credentials'],
                        index=st.session_state['credentials'].index(sub_comment['credential']),
                        key=f"sub_credential_{idx}_{sub_idx}"
                    )

            if st.button(f"Add Sub-comment to Comment {idx + 1}", key=f"add_sub_comment_{idx}"):
                comment_data['sub_comments'].append({"comment": "", "credential": st.session_state['credentials'][0]})
                st.rerun()

        if st.button("Add Another Comment", key="add_comment"):
            st.session_state['comments'].append({"comment": "", "credential": st.session_state['credentials'][0], "sub_comments": []})
            st.rerun()

    # Right column: Metadata and Tags
    with right_column:
        st.header("Metadata")
        source_url = st.text_input("Enter the source URL", help='Copy-paste the URL')

        st.subheader("Tags")
        selected_tags = st.multiselect("Select Tags", options=st.session_state['tags'], default=st.session_state['selected_tags'])
        st.session_state['selected_tags'] = selected_tags

        # Add/Delete Tags and Credentials
        st.header("Add/Delete")
        tag_col, role_col = st.columns(2)
        with tag_col:
            new_tag = st.text_input("Add New Tag").strip()
            if st.button("Add Tag"):
                if new_tag and new_tag not in st.session_state['tags']:
                    st.session_state['tags'].append(new_tag)
                    st.rerun()
            delete_tag = st.selectbox("Select Tag to Delete", st.session_state['tags'], key="delete_tag")
            if st.button("Delete Tag"):
                if delete_tag in st.session_state['tags']:
                    st.session_state['tags'].remove(delete_tag)
                    if delete_tag in st.session_state['selected_tags']:
                        st.session_state['selected_tags'].remove(delete_tag)
                    st.rerun()
        with role_col:
            new_role = st.text_input("Add New Role").strip()
            if st.button("Add Role"):
                if new_role and new_role not in st.session_state['credentials']:
                    st.session_state['credentials'].append(new_role)
                    st.rerun()
            delete_role = st.selectbox("Select Role to Delete", st.session_state['credentials'], key="delete_role")
            if st.button("Delete Role"):
                if delete_role in st.session_state['credentials']:
                    st.session_state['credentials'].remove(delete_role)
                    st.rerun()

    # Submit Button
    if st.button("Submit"):
        if question and st.session_state['comments']:
            # Prepare data for MongoDB
            data = {
                "annotator_name": annotator_name,
                "source_url": source_url,
                "question": question,
                "tags": selected_tags,
                "comments": st.session_state['comments'],
                "timestamp": datetime.datetime.now()
            }
            # Insert data into MongoDB
            collection.insert_one(data)
            st.success("Data submitted successfully!")

            # Clear all fields by resetting session state
            st.session_state['comments'] = [{"comment": "", "credential": "Doctor", "sub_comments": []}]
            st.session_state['selected_tags'] = []
            st.rerun()
        else:
            st.error("Please fill out the question and at least one comment.")

    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Main app logic
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    annotation_tool()
else:
    login()
