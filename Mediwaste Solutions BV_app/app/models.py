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
    hmw_density        = db.Column(db.Float,  nullable=False)   # name="hmw_density"
    number_of_barrels      = db.Column(db.Integer, nullable=False)   # name="number_of_barrels"
    cost_hmw_barrels     = db.Column(db.Float,  nullable=False)    # name="cost_hmw_barrels"
    volume_barrel     = db.Column(db.Float,  nullable=False)    # name="volume_barrel"
    cost_collection  = db.Column(db.Float,  nullable=False)    # name="cost_collection"
    cost_hmw= db.Column(db.Float,  nullable=False)    # name="cost_hmw"
    joint_committee       = db.Column(db.String(50), nullable=False)# name="joint_committee"
    workdays      = db.Column(db.Integer, nullable=False)   # name="workdays"

    # --- Berekende output (getoond op Output.html; template blijft ongewijzigd) ---
    machine_id = db.Column(db.String(80))
    selling_price            = db.Column(db.Float)
    payback_period             = db.Column(db.Float)
    dcf                 = db.Column(db.Float)

    # (optioneel) koppeling aan user later toevoegen:
    # user_id = db.Column(db.Integer, db.ForeignKey("user.id"))