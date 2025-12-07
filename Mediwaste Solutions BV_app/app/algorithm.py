from app.algorithm_settings import values, models
import math
from .models import db, WasteProfile, MachineSizeCalc1, MachineSpecs, PaybackPeriodCalc2

# CONSTANTEN – AANNAMES
# -----------------------------
ELECTRICITY_PRICE_PER_KWH = 0.25   # € / kWh (placeholder)
WATER_PRICE_PER_L = 0.005           # € / m³ (1000 L) (placeholder)
VOLUME_REDUCTION_FACTOR = 0.20     # er blijft 40% volume/gewicht over na behandeling
COLLECTION_REDUCTION_FACTOR = 0.50 # ophaalkost wordt 50% van origineel
STEAM_GENERATOR_COST = 15_000.0    # extra investering indien geen stoomgenerator (placeholder)
MAX_PAYBACK_YEARS = 15             # zoek max 15 jaar
WORKDAYS_PER_YEAR = 300          # aangenomen aantal werkdagen
MAX_DAILY_CYCLES = 8

def recommend_machine(request_id):
    """
    Aanbevolen machine op basis van:
    - Jaarvolume afval (uit 1 tot 4 vattypes)
    - MAX_DAILY_CYCLES (uit constant bovenaan)
    - WORKDAYS_PER_YEAR (uit constant bovenaan)
    - 90% van machinecapaciteit is effectief bruikbaar
    """

    waste = WasteProfile.query.filter_by(request_id=request_id).first()
    if waste is None:
        return None

    # 1. Jaarvolume berekenen
    annual_volume_l = 0
    barrel_streams = [
        (waste.number_of_barrels_1, waste.volume_barrels_1),
        (waste.number_of_barrels_2, waste.volume_barrels_2),
        (waste.number_of_barrels_3, waste.volume_barrels_3),
        (waste.number_of_barrels_4, waste.volume_barrels_4),
    ]

    for n, vol in barrel_streams:
        if n and vol:
            annual_volume_l += n * vol

    # 2. Max cycli per jaar
    max_yearly_cycles = MAX_DAILY_CYCLES * WORKDAYS_PER_YEAR

    if max_yearly_cycles <= 0:
        return None

    # 3. Vereist volume per cyclus
    required_volume_per_cycle = annual_volume_l / max_yearly_cycles

    # 4. Machines ophalen en sorteren
    machines = MachineSpecs.query.order_by(MachineSpecs.capacity.asc()).all()

    # 5. Kies kleinste machine met effectieve capaciteit >= required
    for machine in machines:
        effective_capacity = machine.capacity * 0.9  # 90% regel

#annuiteit berekenen voor aankoop prijs machine
def annuity(price, months):
    i = values.yearly_interest / 12
    if not price or price <= 0 or months <= 0:
        return None
    return (price * i) / (1 - (1 + i) ** (-months))

#hoofdfunctie van het algoritme
def run_user_algorithm(hmw_density, number_of_barrels, cost_hmw_barrels,
    volume_barrel, cost_collection, cost_hmw, joint_committee, workdays,):

    #machine aanbevelen
    machine = recommend_machine(hmw_density, number_of_barrels, volume_barrel, workdays)
    if machine is not None:
        advice_machine = machine.name
        machine_price = machine.price
    else:
        advice_machine = None
        machine_price = None

    #maandelijkse annuiteit berekenen
    if machine_price is not None:
        monthly_cost = annuity(machine_price, 120)
    else:
        monthly_cost = None

    #output
    return {"machine_id": advice_machine,
        "selling_price": monthly_cost,
        "payback_period": None,
        "dcf": None,}


#CALC2
# HULPFUNCTIE: payback in maanden (discounted)
# -----------------------------

def _payback_period_months(investment: float, annual_savings: float) -> int | None:
    #Discounted payback in maanden.
    if annual_savings <= 0 or investment <= 0:
        return None

    monthly_savings = annual_savings / 12.0
    monthly_rate = values.yearly_interest / 12.0

    cumulative_saved = 0.0
    max_months = MAX_PAYBACK_YEARS * 12

    for month in range(1, max_months + 1):
        discounted_cf = monthly_savings / ((1 + monthly_rate) ** month)
        cumulative_saved += discounted_cf
        if cumulative_saved >= investment:
            return month

    return None


# HOOFDFUNCTIE: run payback voor een request
# -----------------------------

def run_payback_for_request(request_id) -> dict:
    """
    Hoofdalgoritme.
    - Haalt gegevens uit WASTE_PROFILE, MACHINE_SIZE_CALC, MACHINE_SPECS
    - Berekent jaarlijkse kosten zonder/ met machine
    - Berekent discounted payback in maanden
    - Schrijft resultaat weg in PAYBACK_PERIOD_CALC2
    - Geeft resultaat ook terug als dict (voor templates / debug) (?????waarom)
    """

    # 1. WASTE_PROFILE ophalen
    # -----------------------------
    waste = WasteProfile.query.filter_by(request_id=request_id).first()
    if waste is None:
        raise ValueError(f"WASTE_PROFILE not found for request_id={request_id}")

    annual_volume_l = 0.0

    barrel_streams = [
        (waste.number_of_barrels_1, waste.volume_barrels_1),
        (waste.number_of_barrels_2, waste.volume_barrels_2),
        (waste.number_of_barrels_3, waste.volume_barrels_3),
        (waste.number_of_barrels_4, waste.volume_barrels_4)
    ]

    for n_barrels, vol_per_barrel in barrel_streams:
        if n_barrels is not None and vol_per_barrel is not None:
            annual_volume_l += n_barrels * vol_per_barrel

    if waste.total_cost_hmw_barrels is not None:
        # Supabase heeft al de totale vatkost berekend
        barrel_cost_annual = waste.total_cost_hmw_barrels
    else:
        # Zelf uitrekenen als fallback
        barrel_cost_annual = 0.0
        cost_streams = [
            (waste.number_of_barrels_1, waste.cost_hmw_barrels_1),
            (waste.number_of_barrels_2, waste.cost_hmw_barrels_2),
            (waste.number_of_barrels_3, waste.cost_hmw_barrels_3),
            (waste.number_of_barrels_4, waste.cost_hmw_barrels_4)
        ]
        for n_barrels, cost_per_barrel in cost_streams:
            if n_barrels is not None and cost_per_barrel is not None:
                barrel_cost_annual += n_barrels * cost_per_barrel

    # Verwerking/verbranding en ophaling, excl. WIVA-vaten
    processing_cost_annual = waste.cost_collection_processing or 0.0

    # Totale huidige kost zonder machine
    baseline_annual_cost = barrel_cost_annual + processing_cost_annual


    # 2. Machinekeuze ophalen
    # -----------------------------
    msize = MachineSizeCalc1.query.filter_by(request_id=request_id).first()
    if msize is None:
        raise ValueError(f"MACHINE_SIZE_CALC not found for request_id={request_id}")

    machine = MachineSpecs.query.filter_by(size_code=msize.recommended_machine_id).first()
    if machine is None:
        raise ValueError(
            f"MACHINE_SPECS not found for size_code={msize.recommended_machine_id}"
        )


    # 3. Cycli per jaar + gebruikskosten
    # -----------------------------
    if machine.capacity <= 0:
        raise ValueError("Machine capacity must be > 0")

    cycles_per_year = math.ceil(annual_volume_l / machine.capacity) #niet vol -> max % gevuld? 95%?

    electricity_cost_annual = cycles_per_year * machine.electricity_consumption * ELECTRICITY_PRICE_PER_KWH
    water_cost_annual = cycles_per_year * machine.water_consumption  * WATER_PRICE_PER_L


    # 4. Kosten mét machine
    # -----------------------------
    processing_cost_with_machine = processing_cost_annual * COLLECTION_REDUCTION_FACTOR

    # geen WIVA-vaten meer nodig met machine?
    barrel_cost_with_machine = 0.0

    annual_cost_with_machine = (
        processing_cost_with_machine
        + barrel_cost_with_machine
        + electricity_cost_annual
        + water_cost_annual
    )


    annual_savings = baseline_annual_cost - annual_cost_with_machine


    # 5. Totale investering
    # -----------------------------
    investment = machine.selling_price
    if waste.steam_generator_needed:
        investment += STEAM_GENERATOR_COST


    # 6. Terugverdientijd (in maanden)
    # -----------------------------
    months = _payback_period_months(investment, annual_savings)

    payback_value_to_store = float(months) if months is not None else None


    # 7. Resultaat wegschrijven naar PAYBACK_PERIOD_CALC2
    # -----------------------------
    existing = PaybackPeriodCalc2.query.filter_by(request_id=request_id).first()
    if existing is None:
        row = PaybackPeriodCalc2(
            request_id=request_id,
            payback_months=payback_value_to_store,
        )
        db.session.add(row)
    else:
        existing.payback_months = payback_value_to_store

    db.session.commit()


    # 8. Resultaat teruggeven (handig voor template / debug) ??????
    # -----------------------------
    return {
        "request_id": str(request_id),
        "baseline_annual_cost": baseline_annual_cost,
        "annual_cost_with_machine": annual_cost_with_machine,
        "annual_savings": annual_savings,
        "investment": investment,
        "payback_months": months,
        "machine_id": machine.size_code,
        "cycles_per_year": cycles_per_year,
    }

