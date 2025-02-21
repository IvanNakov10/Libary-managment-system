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
        if not session.get('user_id'):
            flash("You must be logged in!", "danger")
            return redirect(url_for('main.login_page'))
        if not session.get('is_admin'):
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def home():
    books = Book.query.all()
    return render_template('index.html', books=books)


@main.route('/books_page', methods=['GET'])
def books_page():
    """Renders books in an HTML template"""
    books = Book.query.all()
    return render_template('books.html', books=books)


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
    
    # Check regular users
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['is_admin'] = False
        return redirect(url_for('main.home'))
    
    # Check admin users
    admin_user = AdminUser.query.filter_by(email=email).first()
    if admin_user and bcrypt.check_password_hash(admin_user.password_hash, password):
        session['user_id'] = admin_user.id
        session['is_admin'] = True
        return redirect(url_for('main.home'))
    
    flash("Invalid credentials", "danger")
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
        availability_input = request.form.get('availability')
        publisher = request.form.get('publisher')  # NEW
        year_input = request.form.get('year')      # NEW

        # Convert availability to int
        try:
            availability = int(availability_input) if availability_input else 1
        except ValueError:
            flash("Availability must be a valid number.", "danger")
            return redirect(url_for('main.add_book_page'))

        # Convert year to int
        try:
            year = int(year_input) if year_input else None
        except ValueError:
            flash("Year must be a valid number.", "danger")
            return redirect(url_for('main.add_book_page'))

        if not title or not author:
            flash("Title and author are required.", "danger")
            return redirect(url_for('main.add_book_page'))

        new_book = Book(
            title=title,
            author=author,
            genre=genre,
            availability=availability,
            publisher=publisher,  # NEW
            year=year             # NEW
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
        publisher = request.form.get('publisher')  # NEW
        year_input = request.form.get('year')      # NEW

        availability_input = request.form.get('availability')
        try:
            book.availability = int(availability_input) if availability_input else 1
        except ValueError:
            flash("Availability must be a valid number.", "danger")
            return redirect(url_for('main.edit_book_page', id=id))

        # Convert year to int
        try:
            book.year = int(year_input) if year_input else None
        except ValueError:
            flash("Year must be a valid number.", "danger")
            return redirect(url_for('main.edit_book_page', id=id))

        book.publisher = publisher  # NEW

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
    return redirect(url_for('main.login'))
