from flask import Blueprint, request, jsonify, redirect, url_for, flash, session
from flask import render_template
from app import db
from app.models import Book, User, AdminUser, BookLoan
from flask_bcrypt import Bcrypt
from functools import wraps
from datetime import date, timedelta


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
    newest_books = Book.query.order_by(Book.id.desc()).limit(3).all()
    return render_template('index.html', books=newest_books)



@main.route('/books_page', methods=['GET'])
def books_page():
    genre_filter = request.args.get('genre', default='', type=str)
    publisher_filter = request.args.get('publisher', default='', type=str)
    year_filter = request.args.get('year', default='', type=str)
    sort_order = request.args.get('sort', default='', type=str)  

    genres_query = db.session.query(Book.genre).filter(Book.genre.isnot(None)).distinct().all()
    genres = [g[0] for g in genres_query if g[0]]

    query = Book.query

    if genre_filter:
        query = query.filter(Book.genre == genre_filter)
    if publisher_filter:
        query = query.filter(Book.publisher.ilike(f"%{publisher_filter}%"))
    if year_filter:
        try:
            query = query.filter(Book.year == int(year_filter))
        except ValueError:
            pass

    if sort_order == 'availability':
        query = query.order_by(Book.availability.desc())  

    books = query.all()

    return render_template('books.html',
                           books=books,
                           genres=genres,
                           genre_filter=genre_filter,
                           publisher_filter=publisher_filter,
                           year_filter=year_filter,
                           sort_order=sort_order) 


@main.route('/register_page', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('main.register_page'))

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(first_name=first_name, last_name=last_name, email=email, 
                    phone=phone, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful!", "success")
        return redirect(url_for('main.login_page'))

    return render_template('register_page.html')


@main.route('/login_page', methods=['GET'])
def login_page():
    return render_template('login_page.html')

@main.route('/login_page', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['is_admin'] = False
        return redirect(url_for('main.home'))
    
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
        publisher = request.form.get('publisher')  
        year_input = request.form.get('year')
        description = request.form.get('description')      

        try:
            availability = int(availability_input) if availability_input else 1
        except ValueError:
            flash("Availability must be a valid number.", "danger")
            return redirect(url_for('main.add_book_page'))

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
            publisher=publisher,  
            year=year,
            description=description             
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
        publisher = request.form.get('publisher')  
        year_input = request.form.get('year')
        book.description = request.form.get('description')      

        availability_input = request.form.get('availability')
        try:
            book.availability = int(availability_input) if availability_input else 1
        except ValueError:
            flash("Availability must be a valid number.", "danger")
            return redirect(url_for('main.edit_book_page', id=id))

        try:
            book.year = int(year_input) if year_input else None
        except ValueError:
            flash("Year must be a valid number.", "danger")
            return redirect(url_for('main.edit_book_page', id=id))

        book.publisher = publisher  

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
    session.pop('is_admin', None)
    flash("Logged out.", "info")
    return redirect(url_for('main.login_page'))

@main.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    latest_book = Book.query.order_by(Book.id.desc()).first()
    user_name = "John Doe"  # Example user name or get from session
    return render_template(
        'book_detail.html',
        book=book,
        latest_book=latest_book,
        user_name=user_name
    )

@main.route('/books/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    if request.method == 'GET':
        return redirect(url_for('main.home'))

    if 'user_id' not in session:
        return redirect(url_for('main.login_page'))
    
    book = Book.query.get_or_404(book_id)
    
    if book.availability <= 0:
        flash("No copies left to borrow.", "danger")
        return redirect(url_for('main.home'))
    
    borrow_date = date.today()
    expected_return_date = borrow_date + timedelta(days=7)
    
    new_loan = BookLoan(
        book_id=book.id,
        user_id=session['user_id'],
        borrow_date=borrow_date,
        return_date=expected_return_date,
        returned=False
    )
    db.session.add(new_loan)
    
    book.availability -= 1
    
    try:
        db.session.commit()
        flash("Book borrowed successfully! Please return it by " + expected_return_date.strftime('%Y-%m-%d'), "success")
    except Exception as e:
        db.session.rollback()
        flash("Error borrowing book: " + str(e), "danger")
    
    return redirect(url_for('main.home'))

@main.route('/user_dashboard')
@login_required
def user_dashboard():
    if session.get('is_admin'):
        flash("Access denied for admin users.", "danger")
        return redirect(url_for('main.home'))
    
    user_id = session.get('user_id')
    loans = BookLoan.query.filter_by(user_id=user_id, returned=False).all()
    
    return render_template('user_dashboard.html', loans=loans)

@login_required
@main.route('/books/return/<int:loan_id>', methods=['POST'])
def return_book(loan_id):


    loan = BookLoan.query.get_or_404(loan_id)
    
    if loan.returned:
        flash("Book is already returned.", "warning")
        return redirect(url_for('main.user_dashboard'))
    
    loan.returned = True
    loan.return_date = date.today()
    
    if loan.book:
        loan.book.availability += 1
    else:
        book = Book.query.get(loan.book_id)
        if book:
            book.availability += 1

    try:
        db.session.commit()
        flash("Book returned successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error returning book: " + str(e), "danger")
    
    return redirect(url_for('main.user_dashboard'))

