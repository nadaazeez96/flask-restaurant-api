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
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')
CORS(app)
Swagger(app) 

# --- Connect to MongoDB Atlas ---
try:
    client = client = MongoClient(os.getenv("MONGO_URI"))
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
#@app.route("/restaurants", methods=["GET"])
#def get_all_restaurants():
#    results = list(restaurants.find({}, {"_id": 0}))
#    return jsonify(results)

# --- ROUTE: Search ALL restaurants ---
@app.route("/restaurants", methods=["GET"])
def get_all_restaurants():
    results = list(restaurants.find({}))
    for r in results:
        r["_id"] = str(r["_id"])  # convert ObjectId to string
    return jsonify(results)

#@app.route("/restaurants/<restaurant_id>", methods=["GET"])
#def get_restaurant_by_id(restaurant_id):
#    query = {"_id": restaurant_id}
#    restaurant = restaurants.find_one(query, {"_id": 0})
 #   return jsonify(restaurant or {"error": "Not found"}), (200 if restaurant else 404)

# --- ROUTE: Search by Restaurant ID ---
@app.route("/restaurants/<restaurant_id>", methods=["GET"])
def get_restaurant_by_id(restaurant_id):
    restaurant = restaurants.find_one({"_id": restaurant_id})
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    # Fetch related reviews
    review_list = list(reviews.find({"restaurant_id": restaurant_id}, {"_id": 0}))
    restaurant["_id"] = str(restaurant["_id"])  # Ensure it's JSON serializable
    restaurant["reviews"] = review_list

    return jsonify(restaurant), 200

# --- ROUTE: Search with Cuisine ---
@app.route("/restaurants/cuisine/<cuisine>", methods=["GET"])
def get_by_cuisine(cuisine):
    results = list(restaurants.find({"cuisine": {"$regex": cuisine, "$options": "i"}}, {"_id": 0}))
    return jsonify(results)

# --- ROUTE: Search with Diet ---
@app.route("/restaurants/diet/<diet>", methods=["GET"])
def get_by_diet(diet):
    results = list(restaurants.find({"dietary": {"$regex": diet, "$options": "i"}}, {"_id": 0}))
    return jsonify(results)

# --- ROUTE: Search with Location ---
@app.route("/restaurants/location/<location>", methods=["GET"])
def get_by_location(location):
    results = list(restaurants.find({"location": {"$regex": location, "$options": "i"}}, {"_id": 0}))
    return jsonify(results)

# --- ROUTE: Search for Restaurant with multiple criteria ---
@app.route("/restaurants/filter", methods=["GET"])
def filter_by_combination():
    filters = {}
    if cuisine := request.args.get("cuisine"):
        filters["cuisine"] = {"$regex": cuisine, "$options": "i"}
    if diet := request.args.get("diet"):
        filters["dietary"] = {"$regex": diet, "$options": "i"}
    if location := request.args.get("location"):
        filters["location"] = {"$regex": location, "$options": "i"}
    results = list(restaurants.find(filters, {"_id": 0}))
    return jsonify(results)

# --- ROUTE: Post a restaurant ---
@app.route("/restaurants", methods=["POST"])
def post_restaurant():
    try:
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        decoded = verify_token(token) if token else None
        if not decoded or not decoded.get("role") == "admin":
            return jsonify({"error": "Admin access required"}), 403

        data = request.get_json()
        print("Received data:", data)  # Debug log

        validate_restaurant(data)
        result = restaurants.insert_one(data)
        print("Inserted ID:", result.inserted_id)

        return jsonify({"message": "Restaurant added successfully!"}), 201

    except Exception as e:
        print("❌ Error in POST /restaurants:", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# --- ROUTE: User or Admin Login ---
@app.route("/auth/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    user = users.find_one({"email": data["email"]})
    if user and user["password"] == data["password"]:
        token = generate_token(user["_id"], user.get("role", "user"))
        return jsonify({"message": "Login successful!", "token": token})
    return jsonify({"error": "Invalid credentials"}), 401

# --- ROUTE: Post a Review ---
@app.route("/reviews", methods=["POST"])
def post_review():
    # --- Extract token ---
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    decoded = verify_token(token) if token else None
    if not decoded:
        return jsonify({"error": "Login required"}), 401

    # --- Get user from DB ---
    user = users.find_one({"_id": ObjectId(decoded["user_id"])})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # --- Get data and validate ---
    data = request.get_json()
    required_fields = ["restaurant_id", "rating", "comment"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # --- Get full name or fallback ---
    first = user.get("first_name", "").strip()
    last = user.get("last_name", "").strip()
    full_name = f"{first} {last}".strip() or user.get("email", "").split("@")[0]

    # --- Build and insert review ---
    review = {
        "user": full_name,
        "restaurant_id": data["restaurant_id"],
        "rating": data["rating"],
        "comment": data["comment"],
        "timestamp": datetime.datetime.utcnow()
    }

    print("🔍 Review to insert:", review)  # DEBUG LOG
    reviews.insert_one(review)

    return jsonify({"message": "Review posted successfully!"}), 201



# --- ROUTE: Bookmark a Restaurant ---
@app.route("/bookmarks", methods=["POST"])
def bookmark_restaurant():
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    decoded = verify_token(token) if token else None
    if not decoded:
        return jsonify({"error": "Login required"}), 401

    user = users.find_one({"_id": ObjectId(decoded["user_id"])})
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data.get("restaurant_id"):
        return jsonify({"error": "restaurant_id is required"}), 400

    existing = bookmarks.find_one({
        "user_id": decoded["user_id"],
        "restaurant_id": data["restaurant_id"]
    })
    if existing:
        return jsonify({"message": "Already bookmarked"}), 200

    bookmarks.insert_one({
        "user_id": decoded["user_id"],
        "email": user["email"],
        "restaurant_id": data["restaurant_id"],
        "timestamp": datetime.datetime.utcnow()
    })
    return jsonify({"message": "Restaurant bookmarked!"}), 201


# --- ROUTE: Get All Bookmarked Restaurants for User ---
@app.route("/bookmarks", methods=["GET"])
def get_user_bookmarks():
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    decoded = verify_token(token) if token else None
    if not decoded:
        return jsonify({"error": "Login required"}), 401

    user_id = decoded["user_id"]
    user_bookmarks = list(bookmarks.find({"user_id": user_id}))
    restaurant_ids = [bm["restaurant_id"] for bm in user_bookmarks]

    if not restaurant_ids:
        return jsonify([])

    results = list(restaurants.find({"_id": {"$in": restaurant_ids}}))
    for r in results:
        r["_id"] = str(r["_id"])

    return jsonify(results)


# --- ROUTE: Remove a Bookmark ---
@app.route("/bookmarks/<restaurant_id>", methods=["DELETE"])
def delete_bookmark(restaurant_id):
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    decoded = verify_token(token) if token else None
    if not decoded:
        return jsonify({"error": "Login required"}), 401

    result = bookmarks.delete_one({
        "user_id": decoded["user_id"],
        "restaurant_id": restaurant_id
    })
    if result.deleted_count:
        return jsonify({"message": "Bookmark removed."}), 200
    else:
        return jsonify({"error": "Bookmark not found"}), 404
    
    
# --- Run ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
