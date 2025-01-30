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
metadata_collection = db["Metadata"]

# Initialize metadata
def initialize_metadata():
    metadata = metadata_collection.find_one({"_id": "metadata"})
    if not metadata:
        metadata_collection.insert_one({
            "_id": "metadata",
            "roles": ["Doctor", "Nurse", "General User", "Other"],
            "tags": ["sepsis", "ICU", "delirium", "PICS"]
        })

initialize_metadata()

# Functions to manage roles and tags in the database
def get_roles_from_db():
    metadata = metadata_collection.find_one({"_id": "metadata"})
    return metadata["roles"] if metadata else []

def update_roles_in_db(roles):
    metadata_collection.update_one(
        {"_id": "metadata"},
        {"$set": {"roles": roles}}
    )

def get_tags_from_db():
    metadata = metadata_collection.find_one({"_id": "metadata"})
    return metadata["tags"] if metadata else []

def update_tags_in_db(tags):
    metadata_collection.update_one(
        {"_id": "metadata"},
        {"$set": {"tags": tags}}
    )

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
    if 'roles' not in st.session_state:
        st.session_state['roles'] = get_roles_from_db()
    if 'tags' not in st.session_state:
        st.session_state['tags'] = get_tags_from_db()
    if 'selected_tags' not in st.session_state:
        st.session_state['selected_tags'] = []
    if 'comments' not in st.session_state:
        st.session_state['comments'] = [{"comment": "", "role": "", "is_question": False, "sub_comments": []}]

    # Left column: Query and comments
    with left_column:
        st.header("Extract Question and Answers")
        annotator_name = st.text_input("Annotator Name", value=st.session_state['username'], disabled=True)
        question = st.text_area("Enter the question", help='Copy-paste the question from the forum post')

        st.subheader("Comments")
        for idx, comment_data in enumerate(st.session_state['comments']):
            comment_col, role_col = st.columns([3,1])
            with comment_col:
                st.session_state['comments'][idx]['comment'] = st.text_area(
                    f"Enter the comment {idx + 1}", 
                    value=comment_data['comment'], 
                    key=f"comment_{idx}"
                )
            with role_col:
                st.session_state['comments'][idx]['is_question'] = st.toggle(
                    "Is Question?",
                    value=comment_data.get('is_question', False),
                    key=f"is_question_{idx}"
                )
                st.session_state['comments'][idx]['role'] = st.selectbox(
                    f"Select role for comment {idx + 1}",
                    [""] + st.session_state['roles'],
                    index=st.session_state['roles'].index(comment_data['role']) + 1 if 'role' in comment_data and comment_data['role'] else 0,
                    key=f"role_{idx}"
                )

            # Sub-comments section
            st.markdown(f"**Sub-comments for Comment {idx + 1}:**")
            for sub_idx, sub_comment in enumerate(comment_data.get('sub_comments', [])):
                sub_comment_col, sub_role_col = st.columns([3,1])
                with sub_comment_col:
                    comment_data['sub_comments'][sub_idx]['comment'] = st.text_area(
                        f"Sub-comment {sub_idx + 1} for Comment {idx + 1}", 
                        value=sub_comment['comment'], 
                        key=f"sub_comment_{idx}_{sub_idx}"
                    )
                with sub_role_col:
                    comment_data['sub_comments'][sub_idx]['is_question'] = st.toggle(
                            "Is Question?",
                            value=sub_comment.get('is_question', False),
                            key=f"sub_is_question_{idx}_{sub_idx}"
                        )
                    comment_data['sub_comments'][sub_idx]['role'] = st.selectbox(
                        f"Select role for Sub-comment {sub_idx + 1} of Comment {idx + 1}",
                        [""] + st.session_state['roles'],
                        index=st.session_state['roles'].index(sub_comment['role']) + 1 if 'role' in sub_comment and sub_comment['role'] else 0,
                        key=f"sub_role_{idx}_{sub_idx}"
                    )


            if st.button(f"Add Sub-comment to Comment {idx + 1}", key=f"add_sub_comment_{idx}"):
                comment_data.setdefault('sub_comments', []).append({"comment": "", "role": ""})
                st.rerun()

        if st.button("Add Another Comment", key="add_comment"):
            st.session_state['comments'].append({"comment": "", "role": "", "sub_comments": []})
            st.rerun()

    # Right column: Metadata and Tags
    with right_column:
        st.header("Metadata")
        source_url = st.text_input("Enter the source URL", help='Copy-paste the URL')

        st.subheader("Tags")
        selected_tags = st.multiselect("Select Tags", options=st.session_state['tags'], default=st.session_state['selected_tags'])
        st.session_state['selected_tags'] = selected_tags

        # Add/Delete Tags and Roles
        st.header("Add/Delete")
        tag_col, role_col = st.columns(2)
        with tag_col:
            new_tag = st.text_input("Add New Tag").strip()
            if st.button("Add Tag"):
                if new_tag and new_tag not in st.session_state['tags']:
                    st.session_state['tags'].append(new_tag)
                    update_tags_in_db(st.session_state['tags'])
                    st.rerun()
            delete_tag = st.selectbox("Select Tag to Delete", st.session_state['tags'], key="delete_tag")
            if st.button("Delete Tag"):
                if delete_tag in st.session_state['tags']:
                    st.session_state['tags'].remove(delete_tag)
                    update_tags_in_db(st.session_state['tags'])
                    if delete_tag in st.session_state['selected_tags']:
                        st.session_state['selected_tags'].remove(delete_tag)
                    st.rerun()
        with role_col:
            new_role = st.text_input("Add New Role").strip()
            if st.button("Add Role"):
                if new_role and new_role not in st.session_state['roles']:
                    st.session_state['roles'].append(new_role)
                    update_roles_in_db(st.session_state['roles'])
                    st.rerun()
            delete_role = st.selectbox("Select Role to Delete", st.session_state['roles'], key="delete_role")
            if st.button("Delete Role"):
                if delete_role in st.session_state['roles']:
                    st.session_state['roles'].remove(delete_role)
                    update_roles_in_db(st.session_state['roles'])
                    for comment in st.session_state['comments']:
                        if comment['role'] == delete_role:
                            comment['role'] = ""
                        for sub_comment in comment.get('sub_comments', []):
                            if sub_comment['role'] == delete_role:
                                sub_comment['role'] = ""
                    st.rerun()

    # Submit Button
    if st.button("Submit"):
        if question and st.session_state['comments']:
            data = {
                "annotator_name": annotator_name,
                "source_url": source_url,
                "question": question,
                "tags": selected_tags,
                "comments": st.session_state['comments'],
                "timestamp": datetime.datetime.now()
            }
            collection.insert_one(data)
            st.success("Data submitted successfully!")
            st.session_state['comments'] = []
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
