from app.algorithm_settings import values, models
import math
from .models import db, WasteProfile, MachineSizeCalc1, MachineSpecs, PaybackPeriodCalc2

# CONSTANTEN – AANNAMES
# -----------------------------
# MACHINE OPERATION CONSTANTS
WORKDAYS_PER_YEAR = 300
MAX_DAILY_CYCLES = 8
EFFECTIVE_CAPACITY_FACTOR = 0.94  # machine never filled to 100%
# WASTE REDUCTION / PROCESSING FACTORS
VOLUME_REDUCTION_FACTOR = 0.20
COLLECTION_REDUCTION_FACTOR = 0.40
# VARIABLE OPERATING COST PRICES
ELECTRICITY_PRICE_PER_KWH = 0.18 # AZMM
WATER_PRICE_PER_L = 0.0044 # AZMM
COST_PE_ZAKKEN_MACHINE = 0.42 # AZMM, zak voor 60L
# MACHINE-DEPENDENT FIXED COSTS
STEAM_GENERATOR_COSTS = {
    "T100": 10164,
    "T150": 10164,
    "T300": 27588,
    "T700": 35574,
}
MAINTENANCE_COSTS = {
    "T100": 14500,
    "T150": 19000,
    "T300": 30000,
    "T700": 42000,
}
# FINANCIAL MODEL SETTINGS
MAX_PAYBACK_YEARS = 15


#gedeelde hulpfunctie voor volume
def compute_annual_volume_l(waste) -> float:
    """
    Berekent het totale jaarlijkse afvalvolume in liter,
    op basis van de aantallen vaten en hun volumes.
    """
    annual_volume_l = 0.0

    barrel_streams = [
        (waste.number_of_barrels_1, waste.volume_barrels_1),
        (waste.number_of_barrels_2, waste.volume_barrels_2),
        (waste.number_of_barrels_3, waste.volume_barrels_3),
        (waste.number_of_barrels_4, waste.volume_barrels_4),
    ]

    for n_barrels, vol_per_barrel in barrel_streams:
        # expliciet op None testen, zodat 0 ook geldig is
        if n_barrels is not None and vol_per_barrel is not None:
            annual_volume_l += float(n_barrels) * float(vol_per_barrel) #de variabelen komen binnen als string, zonder conversie geen vermenigvuldiging mogelijk.

    return annual_volume_l


def recommend_machine(request_id):
    waste = WasteProfile.query.filter_by(request_id=request_id).first()
    if waste is None:
        return None

    # Jaarvolume berekenen met gedeelde hulpfunctie
    annual_volume_l = compute_annual_volume_l(waste)

    # ❗ BELANGRIJKE CHECK — deze was verdwenen
    if annual_volume_l == 0:
        return None

    max_yearly_cycles = MAX_DAILY_CYCLES * WORKDAYS_PER_YEAR
    if max_yearly_cycles <= 0:
        return None
    
    required_volume_per_cycle = annual_volume_l / max_yearly_cycles

    machines = MachineSpecs.query.order_by(MachineSpecs.capacity.asc()).all()

    for machine in machines:
        effective_capacity = machine.capacity * EFFECTIVE_CAPACITY_FACTOR

        if effective_capacity >= required_volume_per_cycle:
            return machine

    return None

#annuiteit berekenen voor aankoop prijs machine
def annuity(price, months):
    i = values.yearly_interest / 12
    if not price or price <= 0 or months <= 0:
        return None
    return (price * i) / (1 - (1 + i) ** (-months))

#hoofdfunctie van het algoritme
def run_user_algorithm(
    hmw_density=None,
    number_of_barrels=None,
    cost_hmw_barrels=None,
    volume_barrel=None,
    cost_collection_processing=None,
    cost_hmw=None,
    joint_committee=None,
    workdays=None,
    request_id=None):

    """
    Backwards-compatible machine recommendation function.

    - Routes.py blijft werken omdat alle oude parameters behouden blijven.
    - Nieuwe logica werkt correct omdat we WASTE_PROFILE uit de database gebruiken.
    - request_id kan optioneel worden meegegeven, maar als dat niet gebeurt,
      halen we het automatisch op via de laatst aangemaakte WasteProfile.
    """
    

    # 1. request_id bepalen
    if request_id is None:
        # routes.py geeft request_id niet door; we pakken de meest recente WasteProfile
        waste = WasteProfile.query.order_by(WasteProfile.id.desc()).first()
        if waste is None:
            raise ValueError("Geen WASTE_PROFILE gevonden voor run_user_algorithm() zonder request_id.")
        request_id = waste.request_id

    # 2. Machine aanbevelen
    machine = recommend_machine(request_id)

    if machine is None:
        recommended_machine_id = None
    else:
        recommended_machine_id = machine.id

    # 3. Machine opslaan in MACHINE_SIZE_CALC1
    existing = MachineSizeCalc1.query.filter_by(request_id=request_id).first()

    if existing is None:
        new_calc = MachineSizeCalc1(
            request_id=request_id,
            recommended_machine_id=recommended_machine_id
        )
        db.session.add(new_calc)
    else:
        existing.recommended_machine_id = recommended_machine_id

    db.session.commit()

    # 4. Outputstructuur blijft identiek voor routes + templates
    return {
        "machine_id": recommended_machine_id,
        "selling_price": None,
        "payback_period": None,
        "dcf": None,}


#CALC2
# HULPFUNCTIE: payback in maanden (discounted)
# -----------------------------

def payback_period_months(investment: float, annual_savings: float) -> int | None:
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

def simple_payback_months(investment: float, annual_savings: float) -> int | None:
    if annual_savings <= 0 or investment <= 0:
        return None
    return math.ceil((investment / annual_savings) * 12)


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

    barrel_cost_annual = 0.0
    cost_streams = [
        (waste.number_of_barrels_1, waste.cost_hmw_barrels_1),
        (waste.number_of_barrels_2, waste.cost_hmw_barrels_2),
        (waste.number_of_barrels_3, waste.cost_hmw_barrels_3),
        (waste.number_of_barrels_4, waste.cost_hmw_barrels_4),
        ]

    for n_barrels, total_cost in cost_streams:
        if n_barrels is not None and total_cost is not None:
            barrel_cost_annual += total_cost

    # Verwerking/verbranding en ophaling, excl. WIVA-vaten
    processing_cost_annual = waste.cost_collection_processing or 0.0

    # Totale huidige kost zonder machine
    baseline_annual_cost = barrel_cost_annual + processing_cost_annual


    # 2. Machinekeuze ophalen
    # -----------------------------
    msize = MachineSizeCalc1.query.filter_by(request_id=request_id).first()
    if msize is None:
        raise ValueError(f"MACHINE_SIZE_CALC not found for request_id={request_id}")

    machine = MachineSpecs.query.filter_by(id=msize.recommended_machine_id).first()
    if machine is None:
        raise ValueError(
            f"MACHINE_SPECS not found for id={msize.recommended_machine_id}"
        )


    # 3. Cycli per jaar + gebruikskosten
    # -----------------------------
    effective_capacity = machine.capacity * EFFECTIVE_CAPACITY_FACTOR
    if machine.capacity <= 0:
        raise ValueError("Machine capacity must be > 0")
    
    annual_volume_l = compute_annual_volume_l(waste)

    cycles_per_year = math.ceil(annual_volume_l / effective_capacity) 


    # 4. Kosten mét machine
    # -----------------------------
    electricity_cost_annual = cycles_per_year * machine.electricity_consumption * ELECTRICITY_PRICE_PER_KWH
    water_cost_annual = cycles_per_year * machine.water_consumption  * WATER_PRICE_PER_L

    processing_cost_with_machine = processing_cost_annual * COLLECTION_REDUCTION_FACTOR

    maintenance_cost = MAINTENANCE_COSTS.get(machine.size_code)
    if maintenance_cost is None:
        raise ValueError(f"No maintenance cost configured for machine {machine.size_code}")

    # geen WIVA-vaten meer nodig met machine? wel zakken, prijs?
    barrel_cost_with_machine = 0.0
    reduced_volume = annual_volume_l * VOLUME_REDUCTION_FACTOR 
    cost_bags_for_machine =  COST_PE_ZAKKEN_MACHINE * math.ceil(reduced_volume / 60)

    total_interest = (
        120 * (
           (machine.selling_price * (values.yearly_interest / 12)) /
           (1 - (1 + values.yearly_interest / 12) ** -120)
        )
    ) - machine.selling_price

    annual_interest_cost = total_interest / 10

    annual_cost_with_machine = (
        processing_cost_with_machine
        + maintenance_cost
        + barrel_cost_with_machine
        + cost_bags_for_machine
        + annual_interest_cost
        + electricity_cost_annual
        + water_cost_annual
    )


    annual_savings = baseline_annual_cost - annual_cost_with_machine


    # 5. Totale investering
    # -----------------------------
    investment = machine.selling_price

    if not waste.steam_generator_needed:
        extra_steam_cost = STEAM_GENERATOR_COSTS.get(machine.size_code)

        if extra_steam_cost is None:
            # hard fail als we de code niet kennen
            raise ValueError(f"No steam generator cost configured for machine {machine.size_code}")

        investment -= extra_steam_cost


    # 6. Terugverdientijd (in maanden)
    # -----------------------------
    months = payback_period_months(investment, annual_savings)
    simple_months = simple_payback_months(investment, annual_savings)

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
        "simple_payback_months": simple_months,
        "machine_id": machine.size_code,
        "cycles_per_year": cycles_per_year,
    }

