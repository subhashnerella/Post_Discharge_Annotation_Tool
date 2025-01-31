import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            uri = st.secrets["MONGODB_URI"]
            client = MongoClient(uri, server_api=ServerApi('1'))
            cls._instance.db = client["Post_Discharge"]
            cls._instance.metadata = cls._instance.db["Metadata"]
        return cls._instance
    
    def initialize_metadata(self):
        metadata = self.metadata.find_one({"_id": "metadata"})
        if not metadata:
            self.metadata.insert_one({
                "_id": "metadata",
                "roles": ["Doctor", "Nurse", "General User", "Other"],
                "tags": ["sepsis", "ICU", "delirium", "PICS"]
            })
    
    def get_roles(self):
        metadata = self.metadata.find_one({"_id": "metadata"})
        return metadata["roles"] if metadata else []
    
    def update_roles(self, roles):
        self.metadata.update_one(
            {"_id": "metadata"},
            {"$set": {"roles": roles}}
        )
    
    def get_tags(self):
        metadata = self.metadata.find_one({"_id": "metadata"})
        return metadata["tags"] if metadata else []
    
    def update_tags(self, tags):
        self.metadata.update_one(
            {"_id": "metadata"},
            {"$set": {"tags": tags}}
        )
    def get_collection(self, collection_name):
        return self.db[collection_name]