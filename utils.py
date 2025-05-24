import hashlib
import jwt
from flask import request, jsonify
from bson.objectid import ObjectId
from textblob import TextBlob
from flask import current_app as app
import random

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id, username):
    token = jwt.encode({"user_id": str(user_id), "username": username}, app.config["SECRET_KEY"], algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_token(token):
    try:
        return jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    except Exception:
        return None

def get_current_user(users_collection):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        return None
    user = users_collection.find_one({"_id": ObjectId(payload["user_id"])})
    return user

def entry_to_json(entry):
    return {
        "_id": str(entry["_id"]),
        "date": entry["date"],
        "content": entry["content"],
        "emotions": entry["emotions"],
        "user_id": str(entry["user_id"])
    }
