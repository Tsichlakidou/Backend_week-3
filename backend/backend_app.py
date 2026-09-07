from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime
import json,os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_FILE = os.path.join(BASE_DIR, "posts.json")
app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
SWAGGER_URL = "/api/docs"
API_URL = "/static/masterblog.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Masterblog API'
    }
)

app.register_blueprint(
    swagger_ui_blueprint,
    url_prefix=SWAGGER_URL
)

def load_posts()-> list[dict]:
    try:
        with open(POSTS_FILE, "r") as file:
            posts = json.load(file)
        return posts
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_posts(posts):
    try:
        with open(POSTS_FILE, "w") as file:
            json.dump(posts, file)
    except OSError:
        print("Error saving posts to file.")


@app.route('/api/posts', methods=['GET', 'POST'])
def get_posts():
    if request.method == 'GET':
        posts = load_posts()
        sort = request.args.get('sort')
        direction = request.args.get('direction')
        if sort is not None and sort not in ("title", "content", "author", "date"):
            return jsonify({"error": "Invalid sort field"}), 400
        elif direction is not None and direction not in ("asc", "desc"):
            return jsonify({"error": "Invalid direction field"}), 400
        elif sort == "date" and direction:
            rev = True
            if direction == "asc":
                rev = False
            sorted_list = sorted(posts,
                key=lambda item: datetime.strptime(item["date"], "%Y-%m-%d"),
                reverse=rev)
            return jsonify(sorted_list), 200
        elif sort and direction:
            rev = True
            if direction == "asc":
                rev = False
            sorted_list = sorted(posts, key=lambda item: item[sort], reverse=rev)
            return jsonify(sorted_list), 200
        return jsonify(posts)
    elif request.method == 'POST':
        posts = load_posts()
        new_post = request.get_json()
        if new_post.get("title") is None or new_post.get("content") is None or new_post.get("author") is None or new_post.get("date") is None:
            return jsonify({"error": "Please provide title, content, author and date."}), 400
        max_id = 0
        for post in posts:
            if post['id'] > max_id:
                max_id = post['id']
        new_id = max_id + 1
        new_post['id'] = new_id
        posts.append(new_post)
        save_posts(posts)
        return jsonify(new_post), 201
    return jsonify({"error": "Method not allowed"}), 405

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
# Delete a blog post by its ID
def delete(post_id):
# Find the blog post with the given id and remove it from the list
# Redirect back to the home page
    posts = load_posts()
    post = next((blog_post for blog_post in posts if blog_post['id'] == post_id), None)
    if post:
        posts.remove(post)
        save_posts(posts)
        return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200
    else:
        return jsonify({"message": f"Post with id {post_id} is not found"}), 404


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update(post_id):
    # Fetch the blog posts from the JSON file
    # Find and return a blog post by its unique ID
    posts = load_posts()
    post = next((blog_post for blog_post in posts if blog_post['id'] == post_id), None)
    if post is None:
        # Post not found
        return jsonify({"message": f"Post with id {post_id} is not found"}), 404
    new_data = request.get_json()
    title = new_data.get("title", post["title"])
    content = new_data.get("content", post["content"])
    author = new_data.get("author", post["author"])
    date = new_data.get("date", post["date"])
    # Save the updated posts back to the JSON file
    post['title'] = title
    post['content'] = content
    post['author'] = author
    post['date'] = date
    save_posts(posts)
    return jsonify(post), 200


@app.route('/api/posts/search', methods=['GET'])
def search():
    posts = load_posts()
    search_term = request.args.get('search')
    results = []
    if search_term:
        search_term = search_term.lower()
        for post in posts:
            if search_term in post['title'].lower() or search_term in post['content'].lower() or\
                search_term in post['author'].lower() or search_term in post['date'].lower():
                results.append(post)
    return jsonify(results)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
