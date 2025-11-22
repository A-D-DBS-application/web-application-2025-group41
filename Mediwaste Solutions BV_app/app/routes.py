from flask import Blueprint, render_template, request, redirect
from .models import db, Calculation

from flask import current_app, send_from_directory, abort

main = Blueprint("main", __name__)

# Alleen deze bestandsnamen (die in /templates liggen) publiek maken
ALLOWED_TEMPLATE_IMAGES = {
    "Logo-Mediwaste-Wit.svg",
    "kostenbesparend.png",
    "greenrecycle.png",
    "toekomstgericht.png",
    "favicon.ico",
}

@main.route("/<filename>")
def serve_root_template_images(filename):
    if filename in ALLOWED_TEMPLATE_IMAGES:
        return send_from_directory(current_app.template_folder, filename)
    abort(404)


@main.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(
        current_app.template_folder + "/assets",
        filename
    )


# -------------------------------
# 0) ALGORITME-PLACEHOLDER
#    => JIJ vult dit in.
# -------------------------------
def run_user_algorithm(
    rma_kg, rma_vaten, kost_vaten,
    inhoud_vat, kost_ophaling, kost_verwerking,
    paritair, werkdagen
):
    """
    TODO: VUL JE EIGEN ALGORITME IN.
    Geef een dict terug met (minstens) deze keys:
      - "recommended_machine" (str of None)
      - "new_cost"            (float of None)
      - "payback"             (float of None)
      - "dcf"                 (float of None)
    """
    return {
    "recommended_machine": "TEST MACHINE",
    "new_cost": 12345,
    "payback": 7.5,
    "dcf": 99999,
}


# -------------------------------
# 1) FRONT-END PAGINA'S (z.b. niet wijzigen)
# -------------------------------

@main.route("/")
@main.route("/Homepage.html")  # Homepage (buttons naar register/login) :contentReference[oaicite:2]{index=2}
def home():
    return render_template("Homepage.html")

@main.route("/login.html")  # Login werkt client-side redirect → geen backend login nodig :contentReference[oaicite:3]{index=3}
def login():
    return render_template("Login.html")

@main.route("/register.html", methods=["GET", "POST"])  # Register form (server-side alias) :contentReference[oaicite:4]{index=4}
@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Geen opslag vereist voor jullie flow; front-end verwacht vooral navigatie.
        return redirect("login.html")
    return render_template("Register.html")

@main.route("/Dashboard.html")  # Dashboard (knoppen naar input.html / Output.html) :contentReference[oaicite:5]{index=5}
def dashboard():
    return render_template("Dashboard.html")

# -------------------------------
# 2) NIEUWE BEREKENING (INPUT)
#    - GET: toon form
#    - POST: lees form → JOUW algoritme → opslaan → Output.html
# -------------------------------
@main.route("/input.html", methods=["GET", "POST"])  # form post zonder action (post naar zichzelf) :contentReference[oaicite:6]{index=6}
@main.route("/input", methods=["GET", "POST"])
def new_calc():
    if request.method == "POST":
        # Formvelden exact zoals in Input.html
        rma_kg           = float(request.form["rma_kg"])
        rma_vaten        = int(request.form["rma_vaten"])
        kost_vaten       = float(request.form["kost_vaten"])
        inhoud_vat       = float(request.form["inhoud_vat"])
        kost_ophaling    = float(request.form["kost_ophaling"])
        kost_verwerking  = float(request.form["kost_verwerking"])
        paritair         = request.form["paritair"]
        werkdagen        = int(request.form["aantal_werkdagen"])

        # --- JOUW algoritme-aanroep (placeholder) ---
        result = run_user_algorithm(
            rma_kg, rma_vaten, kost_vaten,
            inhoud_vat, kost_ophaling, kost_verwerking,
            paritair, werkdagen
        )

        # --- Opslaan (outputvelden mogen None zijn) ---
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

        # Output.html is statisch met placeholders → gewoon tonen
        return redirect("Output.html")

    # GET → formulier tonen
    return render_template("Input.html")

# -------------------------------
# 3) RESULTAAT (statische template met "X"), ONDERTUSSEN NIET MEER STATISCH
# -------------------------------
@main.route("/Output.html")
def output():
    # import hier houden om circular imports te vermijden
    from .models import Calculation

    last = Calculation.query.order_by(Calculation.id.desc()).first()
    if not last:
        # geen data? toon lege pagina zoals nu
        return render_template("Output.html")

    return render_template(
        "Output.html",
        recommended_machine=last.recommended_machine or "—",
        payback=last.payback if last.payback is not None else "—",
        dcf=last.dcf if last.dcf is not None else "—",
    )


# --- DEBUG: toon wat er in de database staat ---
from flask import jsonify

@main.route("/debug/calcs")
def debug_calcs():
    # import hier houden om circular imports te vermijden
    from .models import Calculation

    rows = Calculation.query.order_by(Calculation.id.desc()).all()

    def row_to_dict(r):
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
    return jsonify({
        "count": len(data),
        "latest": (data[0] if data else None),
        "sample": data[:5]   # eerste 5 voor overzicht
    })
