from app import create_app, db, bcrypt
from app.models import Book, User, BookLoan, AdminUser, Log
from flask_migrate import upgrade
from datetime import date

app = create_app()

with app.app_context():
    upgrade()

    admin = AdminUser.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
    if not admin:
        hashed_password = bcrypt.generate_password_hash(
            app.config['ADMIN_PASSWORD']
        ).decode('utf-8')
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

    if not Book.query.first():
        books = [
            Book(
                title="The Subtle Art of Not Giving a F*ck",
                author="Mark Manson",
                genre="Self-help",
                availability=3,
                publisher="Harper",
                year=2016,
                description="A counterintuitive guide to living a good life.",
                image_url="https://example.com/subtle-art.jpg"
            ),
            Book(
                title="1984",
                author="George Orwell",
                genre="Dystopian",
                availability=2,
                publisher="Secker & Warburg",
                year=1949,
                description="A novel about a dystopian future under total surveillance.",
                image_url="https://example.com/1984-cover.jpg"
            )
        ]
        db.session.add_all(books)
        db.session.commit()
        print("Books seeded.")

    if not User.query.first():
        users = [
            User(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                phone="1234567890",
                password_hash=bcrypt.generate_password_hash("Password123").decode('utf-8')
            ),
            User(
                first_name="Jane",
                last_name="Smith",
                email="jane@example.com",
                phone="0987654321",
                password_hash=bcrypt.generate_password_hash("SecurePass1").decode('utf-8')
            )
        ]
        db.session.add_all(users)
        db.session.commit()
        print("Users seeded.")

    if not BookLoan.query.first():
        user1 = User.query.filter_by(email="john@example.com").first()
        user2 = User.query.filter_by(email="jane@example.com").first()
        book1 = Book.query.filter_by(title="The Subtle Art of Not Giving a F*ck").first()
        book2 = Book.query.filter_by(title="1984").first()

        loans = [
            BookLoan(
                user_id=user1.id,
                book_id=book1.id,
                borrow_date=date(2025, 1, 1),
                return_date=date(2025, 1, 15),
                returned=True
            ),
            BookLoan(
                user_id=user2.id,
                book_id=book2.id,
                borrow_date=date(2025, 2, 1),
                return_date=None,
                returned=False
            )
        ]
        db.session.add_all(loans)
        book1.availability -= 1
        book2.availability -= 1
        db.session.commit()
        print("Book loans seeded.")

    if not Log.query.first():
        user1 = User.query.filter_by(email="john@example.com").first()
        user2 = User.query.filter_by(email="jane@example.com").first()

        logs = [
            Log(user_id=user1.id, action="Checked out 'The Subtle Art of Not Giving a F*ck'"),
            Log(user_id=user2.id, action="Checked out '1984'"),
            Log(admin_id=AdminUser.query.filter_by(email=app.config['ADMIN_EMAIL']).first().id,
                action="Created hard-coded admin account")
        ]
        db.session.add_all(logs)
        db.session.commit()
        print("Logs seeded.")

    print("Database seeding complete!")
