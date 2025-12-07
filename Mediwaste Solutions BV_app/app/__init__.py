from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from supabase import create_client
from .config import Config
from .translations import translations

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Config met hardcoded keys (zoals jullie prof wil)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # Zorg dat models gekend zijn voor migrations
    from . import models  # noqa: F401

    # Blueprints registreren
    from .routes import main
    app.register_blueprint(main)

   

    @app.template_filter('t')
    def translate(text):
        lang = session.get("lang", "nl")
        if lang == "fr":
            return translations.get(text, text)
        return text

    
    # (optioneel) Supabase client – past bij jullie config
    # Supabase is optioneel: alleen aanmaken als keys bestaan in Config
    url = getattr(Config, "SUPABASE_URL", None)
    key = getattr(Config, "SUPABASE_KEY", None)
    app.supabase = create_client(url, key) if url and key else None

    return app
