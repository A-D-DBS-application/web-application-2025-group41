from . import db, bcrypt

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password: str):
        if password:
            self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username or self.email}>"

class Calculation(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # --- Inputvelden (exact zoals in Input.html) ---
    rma_kg         = db.Column(db.Float,  nullable=False)   # name="rma_kg"
    rma_vaten      = db.Column(db.Integer, nullable=False)   # name="rma_vaten"
    kost_vaten     = db.Column(db.Float,  nullable=False)    # name="kost_vaten"
    inhoud_vat     = db.Column(db.Float,  nullable=False)    # name="inhoud_vat"
    kost_ophaling  = db.Column(db.Float,  nullable=False)    # name="kost_ophaling"
    kost_verwerking= db.Column(db.Float,  nullable=False)    # name="kost_verwerking"
    paritair       = db.Column(db.String(50), nullable=False)# name="paritair"
    werkdagen      = db.Column(db.Integer, nullable=False)   # name="aantal_werkdagen"

    # --- Berekende output (getoond op Output.html; template blijft ongewijzigd) ---
    recommended_machine = db.Column(db.String(80))
    new_cost            = db.Column(db.Float)
    payback             = db.Column(db.Float)
    dcf                 = db.Column(db.Float)

    # (optioneel) koppeling aan user later toevoegen:
    # user_id = db.Column(db.Integer, db.ForeignKey("user.id"))