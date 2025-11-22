from dotenv import load_dotenv
load_dotenv()
from backend.app import create_app
app = create_app()
print('DB URL:', app.config['SQLALCHEMY_DATABASE_URI'])