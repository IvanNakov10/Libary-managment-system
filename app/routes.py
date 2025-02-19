from flask import Blueprint, request, jsonify, redirect, url_for, flash, session
from flask import render_template
from app import db
from app.models import Book, User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
main = Blueprint('main', __name__)

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

@main.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted successfully!"})

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

    flash("Invalid email or password", "danger")
    return redirect(url_for('main.login_page')) 

@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("You must log in first!", "danger")
        return redirect(url_for('main.login'))
    
    return render_template('dashboard.html')
@main.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('main.login'))
