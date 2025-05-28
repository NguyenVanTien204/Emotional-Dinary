from collections import Counter
from textblob import TextBlob
import ast
from pymongo import MongoClient
from bson.objectid import ObjectId
import random

def classify_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"

def pipeline_analyze_and_save(user_secretkey):
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "emotional_diary_db"
    client = MongoClient(mongo_uri)
    db = client[db_name]
    users_col = db.users
    entries_col = db.entries
    emotion_col = db.emotion

    # 1. Kiểm tra user
    user = users_col.find_one({"_id": ObjectId(user_secretkey)})
    if not user:
        print("User not found or invalid secretkey.")
        return

    # 2. Lấy entries của user
    entries = list(entries_col.find({"user_id": ObjectId(user_secretkey)}))
    if not entries:
        print("No entries found for this user.")
        return

    # 3. Phân tích cảm xúc và chuẩn bị dữ liệu lưu
    emotion_results = []
    ICON_SETS = {
        "positive": ["😊", "😃", "😁", "😄", "🥳"],
        "neutral": ["😐", "😶", "😑", "🤔", "🧐"],
        "negative": ["😢", "😞", "😠", "😭", "😔"]
    }
    for entry in entries:
        content = entry.get("content", "")
        sentiment = classify_sentiment(content)
        icon = random.choice(ICON_SETS.get(sentiment, ICON_SETS["neutral"]))
        emotion_results.append({
            "user_id": ObjectId(user_secretkey),
            "entry_id": entry["_id"],
            "content": content,
            "sentiment": sentiment,
            "icon": icon
        })

    # 4. Lưu vào collection emotion (xóa cũ, lưu mới)
    emotion_col.delete_many({"user_id": ObjectId(user_secretkey)})
    if emotion_results:
        emotion_col.insert_many(emotion_results)
    print(f"Saved {len(emotion_results)} emotion results for user {user_secretkey}.")
    client.close()

def analyze_all_users():
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "emotional_diary_db"
    client = MongoClient(mongo_uri)
    db = client[db_name]
    users_col = db.users

    user_ids = users_col.distinct("_id")
    for user_id in user_ids:
        print(f"Analyzing for user: {user_id}")
        pipeline_analyze_and_save(str(user_id))
    client.close()

# Ví dụ chạy pipeline (thay thế bằng _id thực tế của user)
if __name__ == "__main__":
    # user_secretkey = "68307aaf56d677d079593c47"  # ví dụ: "665b7e2e8b3f5e2b8c3e6a1d"
    # pipeline_analyze_and_save(user_secretkey)
    analyze_all_users()







