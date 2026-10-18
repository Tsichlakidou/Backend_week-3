"""Flask REST API for managing and searching blog posts."""
import json
import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint


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


def load_posts() -> list[dict]:
    """Load blog posts from the JSON file."""
    try:
        with open(POSTS_FILE, "r") as file:
            posts = json.load(file)
        return posts
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_posts(posts):
    """Save blog posts to the JSON file."""
    try:
        with open(POSTS_FILE, "w") as file:
            json.dump(posts, file)
    except OSError:
        print("Error saving posts to file.")


@app.route('/api/posts', methods=['GET', 'POST'])
def get_posts():
    """Retrieve blog posts or create a new blog post."""
    if request.method == 'GET':
        posts = load_posts()
        sort = request.args.get('sort')
        direction = request.args.get('direction')
        if (
            sort is not None
            and sort not in ("title", "content", "author", "date")
        ):
            return jsonify({"error": "Invalid sort field"}), 400
        elif direction is not None and direction not in ("asc", "desc"):
            return jsonify({"error": "Invalid direction field"}), 400
        elif sort == "date" and direction:
            rev = True
            if direction == "asc":
                rev = False
            sorted_list = sorted(
                posts,
                key=lambda item: datetime.strptime(item["date"], "%Y-%m-%d"),
                reverse=rev
            )
            return jsonify(sorted_list), 200
        elif sort and direction:
            rev = True
            if direction == "asc":
                rev = False
            sorted_list = sorted(
                posts,
                key=lambda item: item[sort],
                reverse=rev
            )
            return jsonify(sorted_list), 200
        return jsonify(posts)
    elif request.method == 'POST':
        posts = load_posts()
        new_post = request.get_json()
        if not isinstance(new_post, dict):
            return jsonify({"error": "Invalid JSON object"}), 400
        if (
            new_post.get("title") is None
            or new_post.get("content") is None
            or new_post.get("author") is None
            or new_post.get("date") is None
        ):
            return jsonify({
                "error": "Please provide title, content, author and date."
            }), 400
        if (
            not isinstance(new_post["title"], str)
            or not isinstance(new_post["content"], str)
            or not isinstance(new_post["author"], str)
            or not isinstance(new_post["date"], str)
        ):
            return jsonify({
                "error": "Title, content, author and date must be strings"
            }), 400
        if (
            not new_post.get("title", "").strip()
            or not new_post.get("content", "").strip()
            or not new_post.get("author", "").strip()
            or not new_post.get("date", "").strip()
        ):
            return jsonify({
                "error": "Title, content, author and date cannot be empty"
            }), 400

        new_id = max((post["id"] for post in posts), default=0) + 1
        new_post['id'] = new_id
        new_post['title'] = new_post['title'].strip()
        new_post['content'] = new_post['content'].strip()
        new_post['author'] = new_post['author'].strip()
        new_post['date'] = new_post['date'].strip()

        posts.append(new_post)
        save_posts(posts)
        return jsonify(new_post), 201
    return jsonify({"error": "Method not allowed"}), 405


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete(post_id):
    """Delete a blog post by its ID."""
    posts = load_posts()
    post = next(
        (blog_post for blog_post in posts if blog_post['id'] == post_id),
        None
    )
    if post:
        posts.remove(post)
        save_posts(posts)
        return jsonify({
            "message": f"Post with id {post_id} has been deleted successfully."
        }), 200
    else:
        return jsonify(
            {"message": f"Post with id {post_id} is not found"}
        ), 404


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update(post_id):
    """Update an existing blog post by its ID."""
    posts = load_posts()
    post = next(
        (blog_post for blog_post in posts if blog_post['id'] == post_id),
        None
    )
    if post is None:
        return jsonify(
            {"message": f"Post with id {post_id} is not found"}
        ), 404
    new_data = request.get_json()
    title = new_data.get("title", post["title"])
    content = new_data.get("content", post["content"])
    author = new_data.get("author", post["author"])
    date = new_data.get("date", post["date"])

    post['title'] = title
    post['content'] = content
    post['author'] = author
    post['date'] = date
    save_posts(posts)
    return jsonify(post), 200


@app.route('/api/posts/search', methods=['GET'])
def search():
    """Search blog posts by title, content, or a general search term."""
    posts = load_posts()
    search_term = request.args.get('search')
    title = request.args.get('title')
    content = request.args.get('content')
    results = []

    for post in posts:
        title_match = title and title.lower() in post['title'].lower()
        content_match = content and content.lower() in post['content'].lower()
        search_match = search_term and (
            search_term.lower() in post['title'].lower()
            or search_term.lower() in post['content'].lower()
            or search_term.lower() in post['author'].lower()
            or search_term.lower() in post['date'].lower()
        )
        if title_match or content_match or search_match:
            results.append(post)
    return jsonify(results)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
