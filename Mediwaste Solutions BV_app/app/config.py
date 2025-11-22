#class Config: 
#    SECRET_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1mYmFiaGpuYXliam5qeGJmZGRyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDk0MjYzMSwiZXhwIjoyMDc2NTE4NjMxfQ.KHWrkBboIbumDVLR6e87cT1ErxgsOqU_oAPZRfBY_ps'
#    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:[Group41!!!!]@db.mfbabhjnaybjnjxbfddr.supabase.co:5432/postgres'
#    SQLALCHEMY_TRACK_MODIFICATIONS = False
class Config:
    SECRET_KEY = "dev"
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"   # <— tijdelijk lokaal
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SUPABASE_URL / SUPABASE_KEY laat je zoals ze zijn of weg
