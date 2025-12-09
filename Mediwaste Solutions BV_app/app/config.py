import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    # ---------------------------------------------------------
    # TIJDELIJKE TEST: We zetten de URL er hard in.
    # Als dit werkt, weten we dat je .env bestand het probleem is.
    # ---------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres.mfbabhjnaybjnjxbfddr:Group41!!!!@aws-1-eu-west-3.pooler.supabase.com:6543/postgres"

    SQLALCHEMY_TRACK_MODIFICATIONS = False