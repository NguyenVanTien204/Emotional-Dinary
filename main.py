
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

# Định nghĩa đường dẫn tới thư mục templates và static
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
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
    # Chỉ cho phép lấy entries của chính user đó
    entries = entries_collection.find({"user_id": user["_id"]}).sort("date", -1)
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
    # --- XÓA DỮ LIỆU PHÂN XÍCH CẢM XÚC LIÊN QUAN ---
    emotion_col = mongo.db.emotion
    emotion_col.delete_one({"user_id": user["_id"], "entry_id": ObjectId(entry_id)})
    # --- KẾT THÚC XÓA ---
    if result.deleted_count == 0:
        return jsonify({"error": "Entry not found"}), 404
    return jsonify({"message": "Entry deleted"}), 200
#============================================================================================
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/diary")
def diary():
    return render_template("index.html")

@app.route("/charts")
def charts():
    return render_template("charts.html")

#============================================================================================
@app.route("/emotions", methods=["GET"])
def get_emotions():
    user = get_current_user(users_collection)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    emotion_col = mongo.db.emotion
    # Chỉ lấy emotions của user hiện tại
    emotions = list(emotion_col.find({"user_id": user["_id"]}))
    entries = list(entries_collection.find({"user_id": user["_id"]}))
    entry_id_to_date = {str(e["_id"]): e["date"] for e in entries}
    result = []
    for emo in emotions:
        item = {
            "entry_id": str(emo.get("entry_id")),
            "sentiment": emo.get("sentiment", ""),
            "icon": emo.get("icon", "")
        }
        entry_id = str(emo.get("entry_id"))
        if entry_id in entry_id_to_date:
            item["date"] = entry_id_to_date[entry_id]
        result.append(item)
    return jsonify(result), 200

#============================================================================================
@app.route("/emotions/stats", methods=["GET"])
def get_emotion_stats():
    """
    API trả về tổng số lần xuất hiện từng loại cảm xúc trong last week/last month/last year.
    Tham số:
        - period: 'week', 'month', 'year'
    """
    user = get_current_user(users_collection)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    period = request.args.get("period", "month")  # default: month

    now = datetime.datetime.now()
    if period == "week":
        start_date = now - datetime.timedelta(days=7)
    elif period == "month":
        start_date = now - datetime.timedelta(days=30)
    elif period == "year":
        start_date = now - datetime.timedelta(days=365)
    else:
        start_date = now - datetime.timedelta(days=30)

    # Sử dụng aggregation pipeline để join emotion với entries và lọc theo ngày
    pipeline = [
        {
            "$match": {
                "user_id": user["_id"]
            }
        },
        {
            "$lookup": {
                "from": "entries",
                "localField": "entry_id",
                "foreignField": "_id",
                "as": "entry"
            }
        },
        {
            "$unwind": "$entry"
        },
        {
            "$addFields": {
                "entry_date": {
                    "$dateFromString": {
                        "dateString": "$entry.date",
                        "format": "%Y-%m-%d"
                    }
                }
            }
        },
        {
            "$match": {
                "entry_date": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": "$sentiment",
                "count": {"$sum": 1}
            }
        }
    ]

    emotion_col = mongo.db.emotion
    agg_result = list(emotion_col.aggregate(pipeline))

    # Đảm bảo đủ 3 loại cảm xúc
    all_sentiments = ["positive", "neutral", "negative"]
    sentiment_counter = {s: 0 for s in all_sentiments}
    for item in agg_result:
        sentiment = item["_id"]
        if sentiment in sentiment_counter:
            sentiment_counter[sentiment] = item["count"]

    data = [sentiment_counter[s] for s in all_sentiments]

    result = {
        "labels": [s.capitalize() for s in all_sentiments],
        "datasets": [{
            "label": "Emotion Count",
            "data": data,
            "backgroundColor": ["#81c784", "#fff176", "#e57373"]
        }]
    }
    return jsonify(result), 200
#============================================================================================
@app.route("/emotions/<entry_id>/icon", methods=["PUT"])
def update_emotion_icon(entry_id):
    user = get_current_user(users_collection)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    icon = data.get("icon")
    if not icon:
        return jsonify({"error": "No icon provided"}), 400
    emotion_col = mongo.db.emotion
    result = emotion_col.update_one(
        {"user_id": user["_id"], "entry_id": ObjectId(entry_id)},
        {"$set": {"icon": icon}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Emotion not found"}), 404
    return jsonify({"message": "Icon updated"}), 200
#============================================================================================
@app.route("/entries/search", methods=["GET"])
def search_entries():
    """
    Tìm kiếm entry theo keyword, trả về danh sách entries và wordcloud.
    Query params:
        - q: từ khóa tìm kiếm
    """
    user = get_current_user(users_collection)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify({"error": "No keyword provided"}), 400

    # Đảm bảo đã tạo text index trên content: db.entries.createIndex({content: "text"})
    query = {
        "user_id": user["_id"],
        "$text": {"$search": keyword}
    }
    projection = {"score": {"$meta": "textScore"}}
    entries = list(entries_collection.find(query, projection).sort([("score", {"$meta": "textScore"})]))
    entry_list = [entry_to_json(e) for e in entries]

    # Tạo wordcloud: đếm tần suất các từ xuất hiện trong các entry tìm được
    words = []
    for e in entries:
        content = e.get("content", "")
        # Tách từ, loại bỏ ký tự đặc biệt, chuyển về lower
        words += re.findall(r'\b\w+\b', content.lower())
    # Loại bỏ stopwords đơn giản
    stopwords = set(["the", "and", "is", "a", "of", "to", "in", "it", "for", "on", "with", "as", "at", "by", "an", "be", "this", "that", "i", "you", "he", "she", "we", "they", "was", "were", "are", "am", "but", "or", "not", "so", "if", "from", "my", "your", "his", "her", "their", "our", "me", "him", "them", "us"])
    filtered_words = [w for w in words if w not in stopwords and len(w) > 2]
    word_freq = Counter(filtered_words)
    wordcloud = [{"text": w, "value": c} for w, c in word_freq.most_common(50)]

    return jsonify({
        "entries": entry_list,
        "wordcloud": wordcloud
    }), 200
#============================================================================================
@app.route("/entries/negative-insights", methods=["GET"])
def negative_insights():
    """
    Phân tích tiêu cực: 
    - Trả về danh sách entry chứa từ tiêu cực.
    - Thống kê số entry tiêu cực, tổng số entry, tỷ lệ tiêu cực (%).
    - Wordcloud các từ tiêu cực xuất hiện nhiều nhất.
    - Thống kê top từ tiêu cực lặp lại nhiều nhất.
    """
    user = get_current_user(users_collection)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    NEGATIVE_KEYWORDS = [
        "lonely", "tired", "surviving", "vulnerable", "numb", "anxious", 
        "lost", "fragile", "hurt", "grief", "sadness", "not okay", "hopeless",
        "empty", "broken", "afraid", "pain", "regret", "guilty", "worthless",
        "buồn", "chán", "mệt", "stress", "lo lắng", "cô đơn", "tức giận", "thất vọng", 
        "khó chịu", "khóc", "đau", "sợ", "áp lực", "bực", "tệ", "không vui", 
        "không ổn", "không tốt", "bỏ cuộc", "thua", "ghét", "không thích"
    ]

    regex_list = [{"content": {"$regex": kw, "$options": "i"}} for kw in NEGATIVE_KEYWORDS]
    regex_list += [{"emotions": {"$regex": kw, "$options": "i"}} for kw in NEGATIVE_KEYWORDS]

    query = {
        "user_id": user["_id"],
        "$or": regex_list
    }

    all_entries = list(entries_collection.find({"user_id": user["_id"]}))
    negative_entries = list(entries_collection.find(query))
    entry_list = [entry_to_json(e) for e in negative_entries]

    # Wordcloud cho các entry tiêu cực
    words = []
    for e in negative_entries:
        content = e.get("content", "")
        words += re.findall(r'\b\w+\b', content.lower())
        if isinstance(e.get("emotions", None), list):
            words += [em.lower() for em in e["emotions"] if isinstance(em, str)]
            
    stopwords = set([
        "the", "and", "is", "a", "of", "to", "in", "it", "for", "on", "with", 
        "as", "at", "by", "an", "be", "this", "that", "i", "you", "he", "she", 
        "we", "they", "was", "were", "are", "am", "but", "or", "not", "so", 
        "if", "from", "my", "your", "his", "her", "their", "our", "me", "him", 
        "them", "us"
    ])
    filtered_words = [w for w in words if w not in stopwords and len(w) > 2]
    word_freq = Counter(filtered_words)
    wordcloud = [{"text": w, "value": c} for w, c in word_freq.most_common(50)]

    # Thống kê số entry tiêu cực, tổng số entry, tỷ lệ
    total_entries = len(all_entries)
    negative_count = len(negative_entries)
    negative_ratio = round(negative_count / total_entries * 100, 2) if total_entries else 0

    # Thống kê top từ tiêu cực lặp lại nhiều nhất trong các entry tiêu cực
    negative_word_counts = {kw: 0 for kw in NEGATIVE_KEYWORDS}
    for e in negative_entries:
        text = (e.get("content", "") + " " + " ".join(e.get("emotions", []))).lower()
        for kw in NEGATIVE_KEYWORDS:
            if kw in text:
                negative_word_counts[kw] += text.count(kw)
    
    top_negative_words = sorted(
        [{"keyword": k, "count": v} for k, v in negative_word_counts.items() if v > 0],
        key=lambda x: x["count"], reverse=True
    )[:10]

    return jsonify({
        "entries": entry_list,
        "wordcloud": wordcloud,
        "negative_count": negative_count,
        "total_entries": total_entries,
        "negative_ratio": negative_ratio,
        "top_negative_words": top_negative_words
    }), 200

if __name__ == "__main__":
    app.run(debug=True)

