from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import db, User, Request, WasteProfile, MachineSizeCalc1, PaybackPeriodCalc2, MachineSpecs
from .algorithm import run_user_algorithm
from .algorithm import run_payback_for_request
import uuid
from datetime import datetime
from sqlalchemy.orm import joinedload

main = Blueprint("main", __name__)

def render_lang(template_name, **kwargs):
    lang = session.get("lang", "nl")

    if lang == "fr":
        template_name = f"fr/{template_name}"

    return render_template(template_name, **kwargs)

@main.app_template_filter('format_date')
def format_date(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ""
    return value.strftime(format)

# --- Taalfunctie (set_language) moet nog steeds in dit bestand staan om te werken ---
@main.route('/set-language/<lang_code>')
def set_language(lang_code):
    if lang_code in ['nl', 'fr']:
        session['lang'] = lang_code
        session.modified = True
        print(f"DEBUG: Taal ingesteld op {lang_code}. Sessie nu: {session.get('lang')}")
    return redirect(request.referrer or url_for('main.homepage'))
# ---------------------------------------------------------------------------------

def to_null(value):
    """
    Converteert lege strings of whitespace naar None.
    SQLAlchemy zet None automatisch om in NULL in de database.
    """
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    return value


# -------------------------
# 1. Homepage
# -------------------------
@main.route("/")
@main.route("/homepage")
def homepage():
    return render_lang("homepage.html")

# -------------------------
# 2. Login (Aangepast)
# -------------------------
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        # Succesvolle login
        if user and user.password == password:
            session["user_id"] = str(user.id)
            session["is_admin"] = user.is_admin

            if user.is_admin:
                return redirect(url_for("main.admin_dashboard"))
            else:
                # PAS HIER AAN: Stuur reguliere gebruiker naar Dashboard
                return redirect(url_for("main.dashboard")) 

        # Foute login
        else:
            flash("Ongeldige login.")
            return redirect(url_for("main.login"))

    return render_lang("login.html")


# -------------------------
# 3. Register (Aangepast)
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
        # PAS HIER AAN: Stuur nieuwe gebruiker naar Dashboard
        return redirect(url_for("main.dashboard")) 

    return render_lang("register.html")

# -------------------------
# 4. Dashboard
# -------------------------
@main.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        # Als niet ingelogd, stuur naar login (Belangrijke beveiligingscheck)
        return redirect(url_for("main.login")) 
    return render_lang("dashboard.html")

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
    return render_lang("aanvragen.html", requests=requests)

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
            user_id=uuid.UUID(user_id), 
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

            volume_barrels_1=to_null(request.form["volume_barrels_1"]),
            volume_barrels_2=to_null(request.form["volume_barrels_2"]),
            volume_barrels_3=to_null(request.form["volume_barrels_3"]),
            volume_barrels_4=to_null(request.form["volume_barrels_4"]),

            cost_collection_processing=request.form["cost_collection_processing"],
            steam_generator_needed=request.form["steam_generator_needed"] == "true"
        )
        db.session.add(waste)

        # Machine berekenen + opslaan
        result = run_user_algorithm(request_id=new_request.id)
        # Payback berekenen + opslaan
        run_payback_for_request(new_request.id)

        db.session.commit()
        
        # Doorsturen naar output
        return redirect(url_for("main.output", request_id=new_request.id))

    return render_lang("input.html")

# -------------------------
# 7. Output
# -------------------------
@main.route("/output/<uuid:request_id>")
def output(request_id):
    machine_calc = MachineSizeCalc1.query.filter_by(request_id=request_id).first()
    payback_calc = PaybackPeriodCalc2.query.filter_by(request_id=request_id).first()

    machine = None
    if machine_calc and machine_calc.recommended_machine_id:
        from .models import MachineSpecs
        machine = MachineSpecs.query.filter_by(id=machine_calc.recommended_machine_id).first()

    return render_lang(
        "output.html",
        calc=machine_calc,
        machine=machine,
        payback_period=payback_calc.payback_months if payback_calc else None
    )

# -------------------------
# 8. Admin Dashboard
# -------------------------
@main.route("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("main.homepage"))

    # Pagination
    page = request.args.get("page", default=1, type=int)
    page_size = 20
    offset = (page - 1) * page_size

    # Filtering parameter (ONLY company)
    filter_company = request.args.get("company", default="", type=str)

    # USERS (sorted alphabetically by company)
    users = User.query.order_by(User.name_organization.asc()).all()

    # Base query
    query = (
        db.session.query(
            Request.id.label("request_id"),
            Request.created_at.label("created_at"),

            User.email.label("email"),
            User.name_organization.label("company"),
            User.name_user.label("username"),

            WasteProfile.hmw_total_weight,
            WasteProfile.cost_collection_processing,
            WasteProfile.wiva_types,
            WasteProfile.number_of_barrels_1,
            WasteProfile.number_of_barrels_2,
            WasteProfile.number_of_barrels_3,
            WasteProfile.number_of_barrels_4,
            WasteProfile.volume_barrels_1,
            WasteProfile.volume_barrels_2,
            WasteProfile.volume_barrels_3,
            WasteProfile.volume_barrels_4,
            WasteProfile.cost_hmw_barrels_1,
            WasteProfile.cost_hmw_barrels_2,
            WasteProfile.cost_hmw_barrels_3,
            WasteProfile.cost_hmw_barrels_4,
            WasteProfile.steam_generator_needed,

            MachineSizeCalc1.recommended_machine_id,
            MachineSpecs.size_code.label("machine_type"),
            PaybackPeriodCalc2.payback_months
        )
        .join(User, User.id == Request.user_id)
        .join(WasteProfile, WasteProfile.request_id == Request.id)
        .join(MachineSizeCalc1, MachineSizeCalc1.request_id == Request.id)
        .join(MachineSpecs, MachineSpecs.id == MachineSizeCalc1.recommended_machine_id)
        .join(PaybackPeriodCalc2, PaybackPeriodCalc2.request_id == Request.id)
    )

    # Apply company filter
    if filter_company:
        query = query.filter(User.name_organization.ilike(f"%{filter_company}%"))

    # Pagination
    results = (
        query.order_by(Request.created_at.desc())
        .limit(page_size)
        .offset(offset)
        .all()
    )

    total_filtered = query.count()
    max_pages = (total_filtered + page_size - 1) // page_size

    has_prev = page > 1
    has_next = page < max_pages

    return render_template(
        "admin_dashboard.html",
        users=users,
        requests=results,
        page=page,
        has_prev=has_prev,
        has_next=has_next,
        max_pages=max_pages,
        filter_company=filter_company
    )
