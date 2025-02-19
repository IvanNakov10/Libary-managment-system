from app import create_app, db
from app.models import Book, User, BookLoan, AdminUser, Log
from flask_bcrypt import generate_password_hash
from flask_migrate import upgrade
from datetime import date

app = create_app()

with app.app_context():

    admin = AdminUser.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
    if not admin:
        hashed_password = generate_password_hash(app.config['ADMIN_PASSWORD']).decode('utf-8')
        admin = AdminUser(
            username=app.config['ADMIN_USERNAME'],
            email=app.config['ADMIN_EMAIL'],
            password_hash=hashed_password
        )
        db.session.add(admin)
        db.session.commit()
        print("Hard-coded admin created successfully!")
    else:
        print("Hard-coded admin already exists.")
    


    upgrade()

    # Seed Books
    if not Book.query.first():
        books = [
            Book(title="The Subtle Art of Not Giving a F*ck", author="Mark Manson", genre="Self-help"),
            Book(title="Atomic habits", author="James Clear", genre="Self-help")
        ]
        db.session.add_all(books)

    # Seed Users
    if not User.query.first():
        users = [
            User(first_name="John", last_name="Doe", email="john@example.com", phone="1234567890", password_hash=generate_password_hash("password123").decode('utf-8')),
            User(first_name="Jane", last_name="Smith", email="jane@example.com", phone="0987654321", password_hash=generate_password_hash("securepass").decode('utf-8'))
        ]
        db.session.add_all(users)

    

    # Seed Book Loans
    user1 = User.query.filter_by(email="john@example.com").first()
    user2 = User.query.filter_by(email="jane@example.com").first()
    book1 = Book.query.filter_by(title="The Great Gatsby").first()
    book2 = Book.query.filter_by(title="1984").first()

    if user1 and book1 and not BookLoan.query.first():
        book_loans = [
            BookLoan(user_id=user1.id, book_id=book1.id, borrow_date=date(2024, 1, 1), return_date=date(2024, 1, 15), returned=True),
            BookLoan(user_id=user2.id, book_id=book2.id, borrow_date=date(2024, 2, 1), return_date=None, returned=False)
        ]
        db.session.add_all(book_loans)

    # Seed Logs
    if not Log.query.first():
        logs = [
            Log(user_id=user1.id, action="Checked out 'The Great Gatsby'"),
            Log(user_id=user2.id, action="Checked out '1984'"),
            Log(admin_id=1, action="Created a new admin account")
        ]
        db.session.add_all(logs)

    db.session.commit()
    print("Database seeded successfully!")


