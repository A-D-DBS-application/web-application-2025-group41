from flask import (
    Blueprint, render_template, request, redirect,
    current_app, send_from_directory, abort, jsonify
)
from .models import db, Calculation
from .algorithm import run_user_algorithm  # <-- gebruik de versie uit app/algorithm.py

main = Blueprint("main", __name__)

# -------------------------------------------------
# Afbeeldingen uit /templates rechtstreeks kunnen openen
# (bv. /Logo-Mediwaste-Wit.svg, /greencycle.png, ...)
# -------------------------------------------------
@main.route("/<path:filename>")
def serve_template_assets(filename: str):
    # Alleen veilige extensies uit templates toelaten
    allowed = (".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp", ".ico")
    if filename.lower().endswith(allowed):
        return send_from_directory(current_app.template_folder, filename)
    abort(404)

# -------------------------------------------------
# Front-end pagina’s
# -------------------------------------------------
@main.route("/")
@main.route("/Homepage.html")
def home():
    return render_template("Homepage.html")

@main.route("/login.html")
def login():
    return render_template("Login.html")

@main.route("/register.html", methods=["GET", "POST"])
@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Client-side flow: na registreren naar login
        return redirect("login.html")
    return render_template("Register.html")

@main.route("/Dashboard.html")
def dashboard():
    return render_template("Dashboard.html")

# -------------------------------------------------
# Nieuwe berekening (input)
#   - GET: formulier tonen
#   - POST: formulier lezen → algoritme → opslaan → Output.html
# -------------------------------------------------
@main.route("/input.html", methods=["GET", "POST"])
@main.route("/input", methods=["GET", "POST"])
def new_calc():
    if request.method == "POST":
        # Formvelden exact zoals in Input.html
        rma_kg          = float(request.form["rma_kg"])
        rma_vaten       = int(request.form["rma_vaten"])
        kost_vaten      = float(request.form["kost_vaten"])
        inhoud_vat      = float(request.form["inhoud_vat"])
        kost_ophaling   = float(request.form["kost_ophaling"])
        kost_verwerking = float(request.form["kost_verwerking"])
        paritair        = request.form["paritair"]
        werkdagen       = int(request.form["aantal_werkdagen"])

        # --- Algoritme (in app/algorithm.py) ---
        result = run_user_algorithm(
            rma_kg, rma_vaten, kost_vaten,
            inhoud_vat, kost_ophaling, kost_verwerking,
            paritair, werkdagen
        )

        # --- Opslaan (None is oké voor de resultvelden) ---
        calc = Calculation(
            rma_kg=rma_kg,
            rma_vaten=rma_vaten,
            kost_vaten=kost_vaten,
            inhoud_vat=inhoud_vat,
            kost_ophaling=kost_ophaling,
            kost_verwerking=kost_verwerking,
            paritair=paritair,
            werkdagen=werkdagen,
            recommended_machine=result.get("recommended_machine"),
            new_cost=result.get("new_cost"),
            payback=result.get("payback"),
            dcf=result.get("dcf"),
        )
        db.session.add(calc)
        db.session.commit()

        # Output is statisch (nu nog), dus gewoon tonen
        return redirect("Output.html")

    # GET → formulier tonen
    return render_template("Input.html")

# -------------------------------------------------
# Resultaat (statische template)
# -------------------------------------------------
@main.route("/Output.html")
def output():
    return render_template("Output.html")

# -------------------------------------------------
# Debug: toon wat er in de database zit als JSON
# -------------------------------------------------
@main.route("/debug/calcs")
def debug_calcs():
    rows = Calculation.query.order_by(Calculation.id.desc()).all()

    def row_to_dict(r: Calculation):
        return {
            "id": r.id,
            "rma_kg": r.rma_kg,
            "rma_vaten": r.rma_vaten,
            "kost_vaten": r.kost_vaten,
            "inhoud_vat": r.inhoud_vat,
            "kost_ophaling": r.kost_ophaling,
            "kost_verwerking": r.kost_verwerking,
            "paritair": r.paritair,
            "werkdagen": r.werkdagen,
            "recommended_machine": r.recommended_machine,
            "new_cost": r.new_cost,
            "payback": r.payback,
            "dcf": r.dcf,
        }

    data = [row_to_dict(r) for r in rows]
    payload = {
        "count": len(data),
        "latest": data[0] if data else None,
        "sample": data[:10],  # eerste 10 records
    }
    return jsonify(payload)
