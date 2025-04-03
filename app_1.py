from flask import Flask, request, jsonify, abort
from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS
from dotenv import load_dotenv
from flasgger import Swagger
import os
import jwt, datetime

# --- Environment & Setup ---
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '49ac55b04b76b7553d7da83487a80d5da9795b356a9e0ae5179cd033b5bcc504')
CORS(app)
Swagger(app)

# --- Connect to MongoDB Atlas ---
try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["Restaurants_ALL"]
    restaurants = db["Restaurants"]
    users = db["users"]
    bookmarks = db["bookmarks"]
    reviews = db["reviews"]
    cuisines = db["cuisines"]
    dietary_preferences = db["dietary_preferences"]
    print("✅ Connected to MongoDB Atlas successfully.")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")

# --- Helper Functions ---
def validate_restaurant(data):
    required = ["name", "cuisine", "type", "dietary", "rating", "location", "address", "contact"]
    for field in required:
        if field not in data:
            abort(400, description=f"Missing field: {field}")
    if not isinstance(data["rating"], (int, float)) or data["rating"] < 0:
        abort(400, description="Invalid rating value")

def verify_token(token):
    try:
        return jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def generate_token(user_id, role):
    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")

# --- Routes ---
@app.route("/restaurants", methods=["GET"])
def get_all_restaurants():
    """
    Get all restaurants
    ---
    tags:
      - Restaurants
    responses:
      200:
        description: List of all restaurants
    """
    results = list(restaurants.find({}))
    for r in results:
        r["_id"] = str(r["_id"])
    return jsonify(results)

@app.route("/restaurants/<restaurant_id>", methods=["GET"])
def get_restaurant_by_id(restaurant_id):
    """
    Get restaurant by ID
    ---
    tags:
      - Restaurants
    parameters:
      - name: restaurant_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Restaurant data with reviews
      404:
        description: Restaurant not found
    """
    restaurant = restaurants.find_one({"_id": restaurant_id})
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    review_list = list(reviews.find({"restaurant_id": restaurant_id}, {"_id": 0}))
    restaurant["_id"] = str(restaurant["_id"])
    restaurant["reviews"] = review_list

    return jsonify(restaurant), 200

@app.route("/restaurants", methods=["POST"])
def post_restaurant():
    """
    Add a new restaurant (admin only)
    ---
    tags:
      - Restaurants
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
    requestBody:
      required: true
    responses:
      201:
        description: Restaurant added successfully
      403:
        description: Admin access required
    """
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
    decoded = verify_token(token) if token else None
    if not decoded or decoded.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    validate_restaurant(data)
    restaurants.insert_one(data)
    return jsonify({"message": "Restaurant added successfully!"}), 201

@app.route("/auth/login", methods=["POST"])
def admin_login():
    """
    Login user and return JWT
    ---
    tags:
      - Auth
    requestBody:
      required: true
    responses:
      200:
        description: Login successful with JWT token
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    user = users.find_one({"email": data["email"]})
    if user and user["password"] == data["password"]:
        token = generate_token(user["_id"], user.get("role", "user"))
        return jsonify({"message": "Login successful!", "token": token})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/reviews", methods=["POST"])
def post_review():
    """
    Post a review for a restaurant
    ---
    tags:
      - Reviews
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
    requestBody:
      required: true
    responses:
      201:
        description: Review posted successfully
      401:
        description: Login required
    """
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
    decoded = verify_token(token) if token else None
    if not decoded:
        return jsonify({"error": "Login required"}), 401

    user = users.find_one({"_id": ObjectId(decoded["user_id"])})
    data = request.get_json()
    full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get("email", "").split("@")[0]
    review = {
        "user": full_name,
        "restaurant_id": data["restaurant_id"],
        "rating": data["rating"],
        "comment": data["comment"],
        "timestamp": datetime.datetime.utcnow()
    }
    reviews.insert_one(review)
    return jsonify({"message": "Review posted successfully!"}), 201

@app.route("/bookmarks", methods=["POST"])
def bookmark_restaurant():
    """
    Bookmark a restaurant
    ---
    tags:
      - Bookmarks
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
    requestBody:
      required: true
    responses:
      201:
        description: Restaurant bookmarked
      401:
        description: Login required
    """
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
    decoded = verify_token(token) if token else None
    if not decoded:
        return jsonify({"error": "Login required"}), 401

    user = users.find_one({"_id": ObjectId(decoded["user_id"])})
    data = request.get_json()
    if not data.get("restaurant_id"):
        return jsonify({"error": "restaurant_id is required"}), 400

    existing = bookmarks.find_one({"user_id": decoded["user_id"], "restaurant_id": data["restaurant_id"]})
    if existing:
        return jsonify({"message": "Already bookmarked"}), 200

    bookmarks.insert_one({
        "user_id": decoded["user_id"],
        "email": user["email"],
        "restaurant_id": data["restaurant_id"],
        "timestamp": datetime.datetime.utcnow()
    })
    return jsonify({"message": "Restaurant bookmarked!"}), 201

@app.route("/bookmarks", methods=["GET"])
def get_user_bookmarks():
    """
    Get all bookmarked restaurants for a user
    ---
    tags:
      - Bookmarks
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
    responses:
      200:
        description: List of bookmarked restaurants
    """
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
    decoded = verify_token(token) if token else None
    if not decoded:
        return jsonify({"error": "Login required"}), 401

    user_id = decoded["user_id"]
    user_bookmarks = list(bookmarks.find({"user_id": user_id}))
    restaurant_ids = [bm["restaurant_id"] for bm in user_bookmarks]
    results = list(restaurants.find({"_id": {"$in": restaurant_ids}}))
    for r in results:
        r["_id"] = str(r["_id"])
    return jsonify(results)

@app.route("/bookmarks/<restaurant_id>", methods=["DELETE"])
def delete_bookmark(restaurant_id):
    """
    Remove a bookmark for a restaurant
    ---
    tags:
      - Bookmarks
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
      - name: restaurant_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Bookmark removed
      404:
        description: Bookmark not found
    """
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
    decoded = verify_token(token) if token else None
    if not decoded:
        return jsonify({"error": "Login required"}), 401

    result = bookmarks.delete_one({"user_id": decoded["user_id"], "restaurant_id": restaurant_id})
    if result.deleted_count:
        return jsonify({"message": "Bookmark removed."}), 200
    else:
        return jsonify({"error": "Bookmark not found"}), 404

# --- Run ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
