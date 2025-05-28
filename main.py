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
#============================================================================================
@app.route("/entries", methods=["POST"])
def create_entry():
    user = get_current_user(users_collection)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    if not data or "date" not in data or "content" not in data:
        return jsonify({"error": "Missing required fields: date, content"}), 400
    date = data["date"]
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Date must be in YYYY-MM-DD format"}), 400
    content = data["content"]
    emotions = data.get("emotions", [])
    if not isinstance(emotions, list):
        return jsonify({"error": "Emotions must be a list of strings"}), 400
    icon = data.get("icon")
    entry = {
        "date": date,
        "content": content,
        "emotions": emotions,
        "user_id": user["_id"]
    }
    result = entries_collection.insert_one(entry)
    new_entry = entries_collection.find_one({"_id": result.inserted_id})
    # --- PHÂN TÍCH CẢM XÚC VÀ LƯU VÀO DB ---
    emotion_col = mongo.db.emotion
    sentiment = classify_sentiment(content)
    # Nếu user chọn icon thì dùng, không thì random
    from utils import get_random_icon
    if not icon:
        icon = get_random_icon(sentiment)
    emotion_doc = {
        "user_id": user["_id"],
        "entry_id": new_entry["_id"],
        "content": content,
        "sentiment": sentiment,
        "icon": icon
    }
    emotion_col.replace_one(
        {"user_id": user["_id"], "entry_id": new_entry["_id"]},
        emotion_doc,
        upsert=True
    )
    # --- KẾT THÚC PHÂN TÍCH ---
    return jsonify(entry_to_json(new_entry)), 201
#============================================================================================
@app.route("/entries", methods=["GET"])
def get_all_entries():
    user = get_current_user(users_collection)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = str(user["_id"])
    req_user_id = request.args.get("user_id", user_id)
    entries = entries_collection.find({"user_id": ObjectId(req_user_id)}).sort("date", -1)
    all_entries = [entry_to_json(entry) for entry in entries]
    return jsonify(all_entries), 200
#============================================================================================
@app.route("/entries/<entry_id>", methods=["GET"])
def get_entry(entry_id):
    try:
        entry = entries_collection.find_one({"_id": ObjectId(entry_id)})
        if not entry:
            return jsonify({"error": "Entry not found"}), 404
        return jsonify(entry_to_json(entry)), 200
    except Exception:
        return jsonify({"error": "Invalid entry ID"}), 400
#============================================================================================
@app.route("/entries/<entry_id>", methods=["PUT"])
def update_entry(entry_id):
    user = get_current_user(users_collection)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400
    update_data = {}
    if "date" in data:
        date = data["date"]
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
            update_data["date"] = date
        except ValueError:
            return jsonify({"error": "Date must be in YYYY-MM-DD format"}), 400
    if "content" in data:
        update_data["content"] = data["content"]
    if "emotions" in data:
        emotions = data["emotions"]
        if not isinstance(emotions, list):
            return jsonify({"error": "Emotions must be a list of strings"}), 400
        update_data["emotions"] = emotions
    icon = data.get("icon")
    if not update_data and not icon:
        return jsonify({"error": "No valid fields provided to update"}), 400
    entry = entries_collection.find_one({"_id": ObjectId(entry_id)})
    if not entry or entry["user_id"] != user["_id"]:
        return jsonify({"error": "Entry not found or unauthorized"}), 404
    if update_data:
        entries_collection.update_one({"_id": ObjectId(entry_id)}, {"$set": update_data})
    updated_entry = entries_collection.find_one({"_id": ObjectId(entry_id)})
    # --- PHÂN TÍCH CẢM XÚC VÀ LƯU VÀO DB (khi sửa) ---
    emotion_col = mongo.db.emotion
    content = updated_entry["content"]
    sentiment = classify_sentiment(content)
    from utils import get_random_icon
    if not icon:
        icon = get_random_icon(sentiment)
    emotion_doc = {
        "user_id": user["_id"],
        "entry_id": updated_entry["_id"],
        "content": content,
        "sentiment": sentiment,
        "icon": icon
    }
    emotion_col.replace_one(
        {"user_id": user["_id"], "entry_id": updated_entry["_id"]},
        emotion_doc,
        upsert=True
    )
    # --- KẾT THÚC PHÂN TÍCH ---
    return jsonify(entry_to_json(updated_entry)), 200
#============================================================================================
@app.route("/entries/<entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    user = get_current_user(users_collection)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    entry = entries_collection.find_one({"_id": ObjectId(entry_id)})
    if not entry or entry["user_id"] != user["_id"]:
        return jsonify({"error": "Entry not found or unauthorized"}), 404
    result = entries_collection.delete_one({"_id": ObjectId(entry_id)})
    # --- XÓA DỮ LIỆU PHÂN TÍCH CẢM XÚC LIÊN QUAN ---
    emotion_col = mongo.db.emotion
    emotion_col.delete_one({"user_id": user["_id"], "entry_id": ObjectId(entry_id)})
    # --- KẾT THÚC XÓA ---
    if result.deleted_count == 0:
        return jsonify({"error": "Entry not found"}), 404
    return jsonify({"message": "Entry deleted"}), 200

if __name__ == "__main__":
    app.run(debug=True)