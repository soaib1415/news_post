from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import os
import sqlite3
from alembic import op
import sqlalchemy as sa
from flask_migrate import Migrate

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    gender = db.Column(db.String(10))  # Add this line for the gender field
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    name = db.Column(db.String(100))
    user_type = db.Column(db.String(10))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date)
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
# Database initialization
conn = sqlite3.connect('database.db')
conn.execute('''
CREATE TABLE IF NOT EXISTS posts
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL)
''')
conn.execute('''
CREATE TABLE IF NOT EXISTS comments
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    text TEXT NOT NULL)
''')
conn.close()

@app.route('/admin/dashboard')
def admin_dashboard():
    posts = Post.query.all()
    return render_template('admin_dashboard.html', posts=posts)

@app.route('/admin/update_post/<int:post_id>', methods=['GET', 'POST'])
def update_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('update_post.html', post=post)

@app.route('/admin/delete_post/<int:post_id>')
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Index route
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts')
    posts_data = cursor.fetchall()
    conn.close()
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

    # Convert the list of tuples to a list of dictionaries
    posts = [{'id': row[0], 'title': row[1], 'content': row[2]} for row in posts_data]
    return render_template('index.html', posts=posts)


# Single post route
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts WHERE id=?', (post_id,))
    post = cursor.fetchone()

    if request.method == 'POST':
        comment_text = request.form['comment']
        cursor.execute('INSERT INTO comments (post_id, text) VALUES (?, ?)', (post_id, comment_text))
        conn.commit()

    cursor.execute('SELECT * FROM comments WHERE post_id=?', (post_id,))
    comments = cursor.fetchall()
    conn.close()

    return render_template('post.html', post=post, comments=comments)

# Dashboard route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()

    posts = Post.query.all()
    return render_template('dashboard.html', posts=posts)

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        gender = request.form['gender']
        phone_number = request.form['phone_number']
        email = request.form['email']
        name = request.form['name']
        user_type = request.form['user_type']

        new_user = User(
            username=username,
            password=password,
            gender=gender,
            phone_number=phone_number,
            email=email,
            name=name,
            user_type=user_type
        )

        try:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()  # Rollback the transaction
            flash('Username already exists. Please choose a different username.', 'error')

    return render_template('signup.html')

# Login route
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch a single user by username
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['logged_in'] = True
            session['username'] = username  # Store the username in the session
            flash(f'Welcome, {username}!', 'success')
        else:
            flash('Invalid username or password. Please try again.', 'error')

    return render_template('dashboard.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

def upgrade():
    op.add_column('user', sa.Column('gender', sa.String(length=10), nullable=True))


def downgrade():
    op.drop_column('user', 'gender')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

