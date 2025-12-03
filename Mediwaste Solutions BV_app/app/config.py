import os
from dotenv import load_dotenv

load_dotenv()  # laad variabelen uit .env bestand

class Config:
    # Gebruik een veilige secret key (voor Flask sessions, JWT, etc.)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    # Connection string naar Supabase Postgres
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SUPABASE_DB_URL",
        "postgresql://postgres:Group41!!!!@db.mfbabhjnaybjnjxbfddr.supabase.co:5432/postgres"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
