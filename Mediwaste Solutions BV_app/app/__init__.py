from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from supabase import create_client
from .config import Config
from .translations import translations_dict

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Config
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

    # Template filter voor vertalingen
    @app.template_filter('t')
    def translate(text):
        lang = session.get("lang", "nl")
        return translations_dict.get(text, {}).get(lang, text)
    
    # Taal instellen vóór elke request
    @app.before_request
    def set_lang():
        lang = request.args.get("lang")
        if lang in ["nl", "fr"]:
            session["lang"] = lang
        if "lang" not in session:
            session["lang"] = "nl"

    # Optioneel: Supabase client
    url = getattr(Config, "SUPABASE_URL", None)
    key = getattr(Config, "SUPABASE_KEY", None)
    app.supabase = create_client(url, key) if url and key else None

    return app
