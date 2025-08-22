from flask import Flask, render_template, session, request, jsonify, g, redirect, url_for
import sqlite3, os
from dotenv import load_dotenv

load_dotenv(".env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")  # Sử dụng biến môi trường

DATABASE = "database.db"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# Tạo bảng ngay khi khởi động
with sqlite3.connect(DATABASE) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manage_post (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_post TEXT,
            content_post TEXT,
            url_image_post TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

# Helper function để kiểm tra admin đã đăng nhập
def is_admin_logged_in():
    return session.get("admin", False)

@app.route("/")
def main():
    return render_template("index.html")

@app.route("/admin")
def admin():
    """Route admin chính - yêu cầu đăng nhập"""
    if not is_admin_logged_in():
        return redirect(url_for("login"))
    return render_template("admin/index.html")

@app.route("/login")
def login():
    """Hiển thị trang đăng nhập"""
    # Nếu đã đăng nhập rồi thì chuyển về admin
    if is_admin_logged_in():
        return redirect(url_for("admin"))
    return render_template("admin/login.html")

@app.route("/admin/login", methods=["POST"])
def admin_login():
    """Xử lý đăng nhập admin"""
    data = request.get_json()
    
    if not data or "password" not in data:
        return jsonify({"status": "not_ok", "message": "Missing password"}), 400
    
    if data["password"] == os.getenv("ADMIN_PASSWORD"):
        session["admin"] = True
        return jsonify({"status": "ok", "redirect": "/admin"}), 200
    
    return jsonify({"status": "not_ok", "message": "Invalid password"}), 401

@app.route("/admin/logout")
def admin_logout():
    """Đăng xuất admin"""
    session.pop("admin", None)
    return redirect(url_for("login"))

@app.route("/submit_post", methods=["POST"])
def submit_post():
    """Thêm bài viết mới - yêu cầu quyền admin"""
    if not is_admin_logged_in():
        return jsonify({"status": "not_ok", "message": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "not_ok", "message": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["title_post", "content_post", "url_image_post"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"status": "not_ok", "message": f"Missing required field: {field}"}), 400
        
        print(data) 
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO manage_post (title_post, content_post, url_image_post)
            VALUES (?, ?, ?)
        """, (data["title_post"], data["content_post"], data["url_image_post"]))
        db.commit()
        return jsonify({"status": "ok", "message": "Post created successfully"})
    except Exception as err:
        print("Error:", err)
        return jsonify({
            "status": "not_ok",
            "error": str(err)
        }), 500

@app.route("/get_posts", methods=["GET"])
def get_posts():
    """Lấy danh sách bài viết - yêu cầu quyền admin"""
    if not is_admin_logged_in():
        return jsonify({"status": "not_ok", "message": "Unauthorized"}), 401
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM manage_post ORDER BY id DESC")
        posts = cursor.fetchall()
        
        posts_list = []
        for post in posts:
            posts_list.append({
                "id": post["id"],
                "title_post": post["title_post"],
                "content_post": post["content_post"],
                "url_image_post": post["url_image_post"]
            })
        
        return jsonify({"status": "ok", "posts": posts_list})
    except Exception as err:
        print("Error:", err)
        return jsonify({
            "status": "not_ok",
            "error": str(err)
        }), 500

@app.route("/countdown")
def countdown():
    return render_template("countdown.html")

@app.route("/document")
def document():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, title_post, content_post, url_image_post, created_at
            FROM manage_post 
            ORDER BY id DESC
        """)
        posts = cursor.fetchall()
        
        # Generate HTML cards
        cards_html = ""
        for post in posts:
            # Format upload time
            from datetime import datetime
            if post['created_at']:
                upload_date = datetime.strptime(post['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            else:
                upload_date = "N/A"
            
            # Tạo link đến tài liệu chi tiết (có thể dùng ID)
            detail_link = f"tailieu?id={post['id']}"
            
            # Sử dụng ảnh mặc định nếu không có URL
            image_url = post['url_image_post'] if post['url_image_post'] else "https://files.catbox.moe/uuahyi.jpg"
            
            card_html = f"""
            <a href="{detail_link}" class="card group relative block overflow-hidden rounded-2xl bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-white/10 backdrop-blur-md transform transition duration-500">
                <div class="overflow-hidden h-48">
                    <img src="{image_url}" alt="Tài liệu" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500">
                </div>
                <div class="p-5">
                    <h3 class="text-xl font-semibold mb-2 transition-colors">
                        {post['title_post']}
                    </h3>
                    <p class="text-sm text-gray-400">Uploaded: {upload_date}</p>
                </div>
            </a>
            """
            cards_html += card_html
        
        return render_template("document.html", materials_html=cards_html)
        
    except Exception as err:
        print("Error loading documents:", err)
        return render_template("document.html", materials_html="<p class='text-red-400'>Lỗi tải tài liệu</p>")

@app.route("/tailieu")
def tailieu_detail():
    """Hiển thị chi tiết một tài liệu"""
    try:
        # Lấy ID từ URL parameter
        post_id = request.args.get('id')
        if not post_id:
            return redirect(url_for('document'))
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, title_post, content_post, url_image_post, created_at
            FROM manage_post 
            WHERE id = ?
        """, (post_id,))
        post = cursor.fetchone()
        
        if not post:
            return redirect(url_for('document'))
        
        # Truyền thông tin bài viết vào template
        return render_template("tailieu.html", 
                             title=post['title_post'],
                             content=post['content_post'],
                             image_url=post['url_image_post'],
                             created_at=post['created_at'])
        
    except Exception as err:
        print("Error loading document detail:", err)
        return redirect(url_for('document'))
if __name__ == "__main__":
    app.run(debug=True, port=3000)