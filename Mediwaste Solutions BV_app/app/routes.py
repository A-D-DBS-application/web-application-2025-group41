from flask import (
    Blueprint, render_template, request, redirect,
    current_app, send_from_directory, abort, jsonify
)
from .models import db, Calculation
from .algorithm import run_user_algorithm

main = Blueprint("main", __name__)

# -------------------------------------------------
# Afbeeldingen in /templates rechtstreeks kunnen openen
# -------------------------------------------------
@main.route("/<path:filename>")
def serve_template_assets(filename: str):
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
        return redirect("login.html")
    return render_template("Register.html")

@main.route("/Dashboard.html")
def dashboard():
    return render_template("Dashboard.html")


# -------------------------------------------------
# Nieuwe berekening (input → algoritme → opslaan → output)
# -------------------------------------------------
@main.route("/input.html", methods=["GET", "POST"])
@main.route("/input", methods=["GET", "POST"])
def new_calc():
    if request.method == "POST":

        # -- Formvelden exact zoals in Input.html --
        hmw_density   = float(request.form["hmw_density"])
        number_of_barrels       = int(request.form["number_of_barrels"])
        cost_hmw_barrels      = float(request.form["cost_hmw_barrels"])
        volume_barrel      = float(request.form["volume_barrel"])
        cost_collection   = float(request.form["cost_collection"])
        cost_hmw = float(request.form["cost_hmw"])
        joint_committee        = request.form["joint_committee"]
        workdays       = int(request.form["workdays"])

        # --- Algoritme ---
        result = run_user_algorithm(
            hmw_density,      # <--- vervangen!
            number_of_barrels,
            cost_hmw_barrels,
            volume_barrel,
            cost_collection,
            cost_hmw,
            joint_committee,
            workdays
        )

        # --- Opslaan in DB ---
        calc = Calculation(
            hmw_density=hmw_density,
            number_of_barrels=number_of_barrels,
            cost_hmw_barrels=cost_hmw_barrels,
            volume_barrel=volume_barrel,
            cost_hmw=cost_hmw,
            cost_collection=cost_collection,
            joint_committee=joint_committee,
            workdays=workdays,

            machine_id=result.get("machine_id"),
            selling_price=result.get("selling_price"),
            payback_period=result.get("payback_period"),
            dcf=result.get("dcf"),
        )
        db.session.add(calc)
        db.session.commit()

        return redirect("Output.html")

    return render_template("Input.html")


# -------------------------------------------------
# Output (nu dynamisch)
# -------------------------------------------------
@main.route("/Output.html")
def output():
    calc = Calculation.query.order_by(Calculation.id.desc()).first()
    return render_template("Output.html", calc=calc)


# -------------------------------------------------
# Debug JSON endpoint
# -------------------------------------------------
@main.route("/debug/calcs")
def debug_calcs():

    rows = Calculation.query.order_by(Calculation.id.desc()).all()

    def row_to_dict(r: Calculation):
        return {
            "id": r.id,
            "hmw_density": r.hmw_density,  # <--- vervangen!
            "number_of_barrels": r.number_of_barrels,
            "cost_hmw_barrels": r.cost_hmw_barrels,
            "volume_barrel": r.volume_barrel,
            "cost_collection": r.cost_collection,
            "cost_hmw": r.cost_hmw,
            "joint_committee": r.joint_committee,
            "workdays": r.workdays,
            "machine_id": r.machine_id,
            "selling_price": r.selling_price,
            "payback_period": r.payback_period,
            "dcf": r.dcf,
        }

    data = [row_to_dict(r) for r in rows]
    payload = {
        "count": len(data),
        "latest": data[0] if data else None,
        "sample": data[:10],
    }
    return jsonify(payload)
