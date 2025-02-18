from flask import Blueprint, request, jsonify
from app import db
from app.models import Book, User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
main = Blueprint('main', __name__)

@main.route('/')
def home():
    return "Library Management System is running!"

# 📌 GET all books
@main.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([{"id": b.id, "title": b.title, "author": b.author, "genre": b.genre} for b in books])

# 📌 POST - Add a new book
@main.route('/books', methods=['POST'])
def add_book():
    data = request.json
    new_book = Book(title=data['title'], author=data['author'], genre=data.get('genre'))
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"message": "Book added successfully!"}), 201

# 📌 PUT - Update a book
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

# 📌 DELETE - Remove a book
@main.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted successfully!"})

# 📌 POST - User Registration
@main.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(email=data['email'], password_hash=hashed_password)

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"}), 201

# 📌 POST - User Login
@main.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({"message": "Login successful!"})
    return jsonify({"error": "Invalid email or password"}), 401