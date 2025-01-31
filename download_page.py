import streamlit as st
import json
import datetime
from bson import ObjectId
from utils import Database

db = Database()

def json_serial(obj):
    try:
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return str(obj)
    except Exception as e:
        st.error(f"Serialization error: {str(e)}")
        return None

def clean_mongodb_doc(doc):
    if isinstance(doc, dict):
        return {k: clean_mongodb_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [clean_mongodb_doc(item) for item in doc]  # Fixed variable name
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime.datetime):
        return doc.isoformat()
    return doc

def download():
    st.title("Download Annotation Data")
    
    collection = db.get_collection("Annotation")
    users_collection = db.get_collection("Users")

    try:
        users = list(users_collection.find({}, {"username": 1}))
        usernames = ["All Users"] + [user["username"] for user in users]
        selected_user = st.selectbox("Select User", usernames)

        if st.button("Download Data"):
            if selected_user == "All Users":
                data = list(collection.find({}))
            else:
                data = list(collection.find({"annotator_name": selected_user}))

            if data:
                cleaned_data = [clean_mongodb_doc(doc) for doc in data]
                json_str = json.dumps(cleaned_data, default=json_serial, indent=2)
                st.download_button(
                    label="Save JSON",
                    data=json_str,
                    file_name=f"annotation_data_{selected_user}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.warning("No data found for selected criteria")
    except Exception as e:
        st.error(f"Error: {str(e)}")