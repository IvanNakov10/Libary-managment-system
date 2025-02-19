from flask import Blueprint, request, jsonify, redirect, url_for, flash, session
from flask import render_template
from app import db
from app.models import Book, User, AdminUser
from flask_bcrypt import Bcrypt
from functools import wraps

bcrypt = Bcrypt()
main = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first", "danger")
            return redirect(url_for('main.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first", "danger")
            return redirect(url_for('main.login_page'))
        if not session.get('is_admin'):
            flash("You must be an admin to access this page", "danger")
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def home():
    books = Book.query.all()
    return render_template('index.html', books=books)

@main.route('/books', methods=['GET'])
def get_books():
    """Returns books as JSON (API)"""
    books = Book.query.all()
    return jsonify([{"id": b.id, "title": b.title, "author": b.author, "genre": b.genre} for b in books])

@main.route('/books_page', methods=['GET'])
def books_page():
    """Renders books in an HTML template"""
    books = Book.query.all()
    return render_template('books.html', books=books)


@main.route('/books', methods=['POST'])
def add_book():
    data = request.json
    new_book = Book(title=data['title'], author=data['author'], genre=data.get('genre'))
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"message": "Book added successfully!"}), 201

@main.route('/books/<int:id>', methods=['PUT'])
def update_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    data = request.json
    book.title = data.get('title', book.title)
    book.author = data.get('author', book.author)
    book.genre = data.get('genre', book.genre)
    
    db.session.commit()
    return jsonify({"message": "Book updated successfully!"})


@main.route('/register_page', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for('main.register_page'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('main.login_page'))


    return render_template('register.html')


@main.route('/login_page', methods=['GET'])
def login_page():
    return render_template('login.html')

@main.route('/login_page', methods=['POST'])
def login():
    email = request.form.get('email')  
    password = request.form.get('password')  

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        session['user_id'] = user.id 
        flash("Login successful!", "success")
        return redirect(url_for('main.home'))  
    
    admin = AdminUser.query.filter_by(email=email).first()
    if admin and bcrypt.check_password_hash(admin.password_hash, password):
        session['user_id'] = admin.id
        session['is_admin'] = True
        flash("Admin login successful!", "success")
        return redirect(url_for('main.home'))

    flash("Invalid email or password", "danger")
    return redirect(url_for('main.login_page')) 

@main.route('/dashboard')
@admin_required
def dashboard():
    books = Book.query.all()
    return render_template('dashboard.html', books=books)
@main.route('/books/add', methods=['GET', 'POST'])
def add_book_page():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        availability_input = request.form.get('availability')  # using availability as quantity

        # Convert availability to integer
        try:
            availability = int(availability_input) if availability_input else 1
        except ValueError:
            flash("Availability must be a valid number.", "danger")
            return redirect(url_for('main.add_book_page'))

        # Validate required fields
        if not title or not author:
            flash("Title and author are required.", "danger")
            return redirect(url_for('main.add_book_page'))
        
        new_book = Book(
            title=title,
            author=author,
            genre=genre,
            availability=availability
        )
        try:
            db.session.add(new_book)
            db.session.commit()
            flash("Book added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error adding book: " + str(e), "danger")
        return redirect(url_for('main.dashboard'))

    return render_template('add_book.html')

@main.route('/books/edit/<int:id>', methods=['GET', 'POST'])
def edit_book_page(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.genre = request.form.get('genre')
        availability_input = request.form.get('availability')

        try:
            book.availability = int(availability_input) if availability_input else 1
        except ValueError:
            flash("Availability must be a valid number.", "danger")
            return redirect(url_for('main.edit_book_page', id=id))
        
        try:
            db.session.commit()
            flash("Book updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating book: " + str(e), "danger")
        return redirect(url_for('main.dashboard'))

    return render_template('edit_book.html', book=book)
@main.route('/books/delete/<int:id>', methods=['GET', 'POST'])
def delete_book(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(book)
            db.session.commit()
            flash("Book deleted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error deleting book: " + str(e), "danger")
        return redirect(url_for('main.dashboard'))
    return render_template('confirm_delete.html', book=book)

    
@main.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('main.login'))
