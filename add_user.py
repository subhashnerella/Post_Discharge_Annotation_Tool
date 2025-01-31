import hashlib
import sys
from utils import Database

def add_user(username, password):
    try:
        db = Database()
        users = db.get_collection("Users")
        
        # Check if user already exists
        if users.find_one({"username": username}):
            print(f"Error: Username '{username}' already exists")
            return False
        
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Add new user
        user_data = {
            "username": username,
            "password": hashed_password
        }
        
        users.insert_one(user_data)
        print(f"Successfully added user: {username}")
        return True
        
    except Exception as e:
        print(f"Error adding user: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_user.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    add_user(username, password)