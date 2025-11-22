from dotenv import load_dotenv
load_dotenv()
from backend.app import create_app
from backend.extensions import db
from backend.models.user import User
import os

def main():
    app = create_app()
    with app.app_context():
        print(f"DB URL: {db.engine.url}")
        # Assume tables exist, just create user
        user = User.query.filter_by(email='owner@example.com').first()
        if not user:
            user = User(
                email='owner@example.com',
                role='superadmin',
                is_active=True
            )
            user.set_password('ChangeMe123!')
            db.session.add(user)
            db.session.commit()
            print("Superadmin created")
        else:
            print("Superadmin already exists")

if __name__ == "__main__":
    main()