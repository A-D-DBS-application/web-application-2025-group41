import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from supabase import create_client
from dotenv import load_dotenv


db = SQLAlchemy()
migrate = Migrate()




def create_app():
load_dotenv()


app = Flask(__name__)


# Database configuratie (Supabase PostgreSQL)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)
migrate.init_app(app, db)


# Supabase client
app.supabase = create_client(
os.getenv("SUPABASE_URL"),
os.getenv("SUPABASE_KEY")
)


# Blueprint registreren
from .routes import main
app.register_blueprint(main)


return app