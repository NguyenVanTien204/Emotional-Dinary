from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson.json_util import dumps
from flask_cors import CORS

from collections import Counter
import datetime
import re
import os

from utils import hash_password, generate_token, decode_token, get_current_user, entry_to_json, classify_sentiment, get_random_icon

app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = "mongodb://localhost:27017/emotional_diary_db"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecretkey")
mongo = PyMongo(app)
entries_collection = mongo.db.entries
users_collection = mongo.db.users
#============================================================================================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400
    user = {
        "username": username,
        "password": hash_password(password)
    }
    result = users_collection.insert_one(user)
    return jsonify({"message": "User registered"}), 201
#============================================================================================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    user = users_collection.find_one({"username": username})
    if not user or user["password"] != hash_password(password):
        return jsonify({"error": "Invalid username or password"}), 401
    token = generate_token(user["_id"], username)
    return jsonify({
        "token": token,
        "username": username,
        "user_id": str(user["_id"])
    }), 200