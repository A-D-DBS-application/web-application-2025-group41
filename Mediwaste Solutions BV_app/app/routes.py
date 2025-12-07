from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import db, User, Request, WasteProfile, MachineSizeCalc1, PaybackPeriodCalc2
from .algorithm import run_user_algorithm
import uuid
from datetime import datetime

main = Blueprint("main", __name__)



def to_null(value):
    """
    bij input: 4 types vaten, indien leeg of spaties -> None
    Converteert lege strings of whitespace naar None.
    SQLAlchemy zet None automatisch om in NULL in de database.
    """
    if value is None:
        return None

    value = str(value).strip()
    if value == "":
        return None

    return value

@main.before_app_request
def set_lang():
    lang = request.args.get("lang")
    if lang in ["nl", "fr"]:
        session["lang"] = lang
    if "lang" not in session:
        session["lang"] = "nl"

# -------------------------
# 1. Homepage
# -------------------------
@main.route("/")
@main.route("/homepage")
def homepage():
    return render_template("homepage.html")

# -------------------------
# 2. Login
# -------------------------
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:  # later vervangen door bcrypt check
            session["user_id"] = str(user.id)  # opslaan als string
            return redirect(url_for("main.homepage"))
        else:
            flash("Ongeldige login.")
            return redirect(url_for("main.login"))

    return render_template("login.html")

# -------------------------
# 3. Register
# -------------------------
@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name_user = request.form["name_user"]
        email = request.form["email"]
        company_number = request.form["company_number"]
        name_organization = request.form["name_organization"]
        position = request.form["position"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            flash("Wachtwoorden komen niet overeen.")
            return redirect(url_for("main.register"))

        new_user = User(
            id=uuid.uuid4(),
            name_user=name_user,
            email=email,
            company_number=company_number,
            name_organization=name_organization,
            position=position,
            password=password,
            confirm=confirm,
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = str(new_user.id)
        return redirect(url_for("main.homepage"))

    return render_template("register.html")

# -------------------------
# 4. Dashboard
# -------------------------
@main.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# -------------------------
# 5. Aanvragen
# -------------------------
@main.route("/aanvragen")
def aanvragen():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("main.login"))

    # converteer naar UUID
    requests = Request.query.filter_by(user_id=uuid.UUID(user_id)).all()
    return render_template("aanvragen.html", requests=requests)

# -------------------------
# 6. Nieuwe berekening (input)
# -------------------------
@main.route("/input", methods=["GET", "POST"])
def input_page():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("main.login"))

    if request.method == "POST":
        # Maak nieuwe request
        new_request = Request(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),   # <-- fix: cast naar UUID
            created_at=datetime.utcnow()
        )
        db.session.add(new_request)
        db.session.flush()

        # Opslaan waste profile
        waste = WasteProfile(
            id=uuid.uuid4(),
            request_id=new_request.id,
            hmw_total_weight=request.form["hmw_total_weight"],
            wiva_types = int(request.form["wiva_types"]),
            number_of_barrels_1=to_null(request.form["number_of_barrels_1"]),
            number_of_barrels_2=to_null(request.form["number_of_barrels_2"]),
            number_of_barrels_3=to_null(request.form["number_of_barrels_3"]),
            number_of_barrels_4=to_null(request.form["number_of_barrels_4"]),
            cost_hmw_barrels_1=to_null(request.form["cost_hmw_barrels_1"]),
            cost_hmw_barrels_2=to_null(request.form["cost_hmw_barrels_2"]),
            cost_hmw_barrels_3=to_null(request.form["cost_hmw_barrels_3"]),
            cost_hmw_barrels_4=to_null(request.form["cost_hmw_barrels_4"]),
            volume_barrels_1=to_null(request.form["volume_barrel_1"]),
            volume_barrels_2=to_null(request.form["volume_barrel_2"]),
            volume_barrels_3=to_null(request.form["volume_barrel_3"]),
            volume_barrels_4=to_null(request.form["volume_barrel_4"]),
            cost_collection_processing=request.form["cost_collection_processing"],
            steam_generator_needed=request.form["steam_generator_needed"] == "true"
        )
        db.session.add(waste)

        # Algoritme draaien
        result = run_user_algorithm(
            hmw_density=float(request.form["hmw_total_weight"]),
            number_of_barrels=int(request.form["number_of_barrels_1"]),
            cost_hmw_barrels=float(request.form["cost_hmw_barrels_1"]),
            volume_barrel=float(request.form["volume_barrel_1"]),
            cost_collection_processing=float(request.form["cost_collection_processing"]),
            cost_hmw=float(request.form["cost_hmw_barrels_1"]),
            joint_committee=None,
            workdays=250
        )

        machine_calc = MachineSizeCalc1(
            id=uuid.uuid4(),
            request_id=new_request.id,
            recommended_machine_size=result.get("machine_id")
        )
        db.session.add(machine_calc)

        payback_calc = PaybackPeriodCalc2(
            id=uuid.uuid4(),
            request_id=new_request.id,
            payback_months=result.get("payback_period")
        )
        db.session.add(payback_calc)

        db.session.commit()

        return redirect(url_for("main.output", request_id=new_request.id))

    return render_template("input.html")

# -------------------------
# 7. Output
# -------------------------
@main.route("/output/<uuid:request_id>")
def output(request_id):
    machine_calc = MachineSizeCalc1.query.filter_by(request_id=request_id).first()
    payback_calc = PaybackPeriodCalc2.query.filter_by(request_id=request_id).first()

    return render_template(
        "output.html",
        calc=machine_calc,
        payback_period=payback_calc.payback_months if payback_calc else None
    )