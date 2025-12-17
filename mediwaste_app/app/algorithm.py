import math
from .models import db, WasteProfile, MachineSizeCalc1, MachineSpecs, PaybackPeriodCalc2
from decimal import Decimal


# CONSTANTEN – AANNAMES
# -----------------------------
# MACHINE OPERATION CONSTANTS
WORKDAYS_PER_YEAR = 300
MAX_DAILY_CYCLES = 8
EFFECTIVE_CAPACITY_FACTOR = Decimal("0.94")  # machine never filled to 100%
# WASTE REDUCTION / PROCESSING FACTORS
VOLUME_REDUCTION_FACTOR = Decimal("0.20")
COLLECTION_REDUCTION_FACTOR = Decimal("0.40")
# VARIABLE OPERATING COST PRICES
ELECTRICITY_PRICE_PER_KWH = Decimal("0.18") # AZMM
WATER_PRICE_PER_L = Decimal("0.0044") # AZMM
COST_PE_ZAKKEN_MACHINE = Decimal("0.42") # AZMM, zak voor 60L
# MACHINE-DEPENDENT FIXED COSTS
STEAM_GENERATOR_COSTS = {
    "T100": Decimal("10164"),
    "T150": Decimal("10164"),
    "T300": Decimal("27588"),
    "T700": Decimal("35574"),
}
MAINTENANCE_COSTS = {
    "T100": Decimal("14500"),
    "T150": Decimal("19000"),
    "T300": Decimal("30000"),
    "T700": Decimal("42000"),
}
# FINANCIAL MODEL SETTINGS
MAX_PAYBACK_YEARS = 15
YEARLY_INTEREST = Decimal("0.04")  # 4% rente


#gedeelde hulpfunctie voor volume
def compute_annual_volume_l(waste) -> Decimal:
    """
    Berekent het totale jaarlijkse afvalvolume in liters op basis van tonnage.
    """
    if waste.hmw_total_weight is None:
        return Decimal("0")

    # Gewichtsinput (kg) kan als string binnenkomen → cast naar Decimal
    kg = Decimal(str(waste.hmw_total_weight))

    # 1 kg → 10/1.2 liter
    liters_per_kg = Decimal("10") / Decimal("1.2")

    # Jaarvolume in liters
    annual_volume_l = kg * liters_per_kg

    return annual_volume_l


def recommend_machine(request_id):
    waste = WasteProfile.query.filter_by(request_id=request_id).first()
    if waste is None:
        return None

    # Jaarvolume berekenen met gedeelde hulpfunctie
    annual_volume_l = compute_annual_volume_l(waste)

    # Checks met debug prints erin
    if annual_volume_l == 0:
        print("DEBUG: annual_volume_l == 0 → geen machine")
        return None

    max_yearly_cycles = MAX_DAILY_CYCLES * WORKDAYS_PER_YEAR
    if max_yearly_cycles <= 0:
        print("DEBUG: max_yearly_cycles <= 0 → geen machine")
        return None
    
    required_volume_per_cycle = Decimal(annual_volume_l) / Decimal(max_yearly_cycles)

    # DEBUG PRINTS
    print("\n======================")
    print(" RECOMMEND MACHINE DEBUG")
    print("======================")
    print("annual_volume_l:", annual_volume_l)
    print("max_yearly_cycles:", max_yearly_cycles)
    print("required_volume_per_cycle:", required_volume_per_cycle)
    print("----------------------")

    machines = MachineSpecs.query.order_by(MachineSpecs.capacity.asc()).all()

    for machine in machines:
        effective_capacity = Decimal(machine.capacity) * EFFECTIVE_CAPACITY_FACTOR
        print(f"Machine {machine.size_code}: "
            f"capacity={machine.capacity}, "
            f"effective_capacity={effective_capacity}")
        
        if effective_capacity >= Decimal(required_volume_per_cycle):
            print(f"SELECTED MACHINE → {machine.size_code}")
            print("======================\n")
            return machine

    print("NO MACHINE SELECTED")
    print("======================\n")
    return None

#annuiteit berekenen voor aankoop prijs machine
def annuity(price, months):
    i = YEARLY_INTEREST / 12
    if not price or price <= 0 or months <= 0:
        return None
    return (price * i) / (1 - (1 + i) ** (-months))

#hoofdfunctie van het algoritme
def run_user_algorithm(request_id=None):

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

def payback_period_months(investment, annual_savings):
    #Discounted payback in maanden.
    if annual_savings <= 0 or investment <= 0:
        return None

    monthly_savings = annual_savings / Decimal("12.0")
    monthly_rate = Decimal(str(YEARLY_INTEREST)) / Decimal("12")

    cumulative_saved = Decimal("0")
    max_months = MAX_PAYBACK_YEARS * 12

    for month in range(1, max_months + 1):
        discounted_cf = monthly_savings / ((Decimal("1") + monthly_rate) ** month)
        cumulative_saved += discounted_cf
        if cumulative_saved >= investment:
            return month

    return None

def simple_payback_months(investment, annual_savings):
    if annual_savings <= 0 or investment <= 0:
        return None
    return math.ceil((investment / annual_savings) * 12)


# HOOFDFUNCTIE: run payback voor een request
# -----------------------------

def run_payback_for_request(request_id):
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

    barrel_cost_annual = Decimal("0") #zonder dit werd in de loop hieronder bij barrel_c_annual += total_cost ...
    # ... een float opgeteld bij een decimal wat niet werkte
    cost_streams = [
        (waste.number_of_barrels_1, waste.cost_hmw_barrels_1),
        (waste.number_of_barrels_2, waste.cost_hmw_barrels_2),
        (waste.number_of_barrels_3, waste.cost_hmw_barrels_3),
        (waste.number_of_barrels_4, waste.cost_hmw_barrels_4),
        ]

    for n_barrels, total_cost in cost_streams:
        if n_barrels is not None and total_cost is not None:
            barrel_cost_annual += Decimal(total_cost)

    # Verwerking/verbranding en ophaling, excl. WIVA-vaten
    processing_cost_annual = Decimal(str(waste.cost_collection_processing or "0"))

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
    effective_capacity = Decimal(machine.capacity) * EFFECTIVE_CAPACITY_FACTOR
    if machine.capacity <= 0:
        raise ValueError("Machine capacity must be > 0")
    
    annual_volume_l = compute_annual_volume_l(waste)

    cycles_per_year = math.ceil(Decimal(annual_volume_l) / effective_capacity)


    # 4. Kosten mét machine
    # -----------------------------
    electricity_cost_annual = Decimal(cycles_per_year) * Decimal(machine.electricity_consumption) * ELECTRICITY_PRICE_PER_KWH
    water_cost_annual = Decimal(cycles_per_year) * Decimal(machine.water_consumption)  * WATER_PRICE_PER_L

    processing_cost_with_machine = processing_cost_annual * COLLECTION_REDUCTION_FACTOR

    maintenance_cost = MAINTENANCE_COSTS.get(machine.size_code)
    if maintenance_cost is None:
        raise ValueError(f"No maintenance cost configured for machine {machine.size_code}")

    # geen WIVA-vaten meer nodig met machine? wel zakken, prijs?
    barrel_cost_with_machine = 0.0
    reduced_volume = Decimal(annual_volume_l) * VOLUME_REDUCTION_FACTOR 
    bags = (reduced_volume / Decimal("60")).to_integral_value(rounding="ROUND_CEILING")
    cost_bags_for_machine = COST_PE_ZAKKEN_MACHINE * bags

    # Zorg dat alles Decimals worden
    selling_price = Decimal(machine.selling_price)
    monthly_rate = Decimal(str(YEARLY_INTEREST)) / Decimal("12")

    # (1 + r) ** -120  → Decimal power werkt NIET met floats of negatieve exponenten
    # oplossing: gebruik Decimal ** int  (negatieve exponent kan wél)
    discount_factor = (Decimal("1") + monthly_rate) ** Decimal("-120")

    # Annuity interest component
    total_interest = (Decimal("120") * ((selling_price * monthly_rate) / (Decimal("1") - discount_factor))) - selling_price

    annual_interest_cost = total_interest / Decimal("10")

    #Alles naar hetzelfde formaat brengen om de komende som uit te kunnen voeren
    processing_cost_with_machine = Decimal(processing_cost_with_machine)
    maintenance_cost = Decimal(maintenance_cost)
    barrel_cost_with_machine = Decimal(barrel_cost_with_machine)
    cost_bags_for_machine = Decimal(cost_bags_for_machine)
    annual_interest_cost = Decimal(annual_interest_cost)
    electricity_cost_annual = Decimal(electricity_cost_annual)
    water_cost_annual = Decimal(water_cost_annual)

    annual_cost_with_machine = (
        processing_cost_with_machine
        + maintenance_cost
        + barrel_cost_with_machine
        + cost_bags_for_machine
        + annual_interest_cost
        + electricity_cost_annual
        + water_cost_annual
    )

    annual_savings = Decimal(baseline_annual_cost) - Decimal(annual_cost_with_machine)

    # 5. Totale investering
    # -----------------------------
    investment = Decimal(machine.selling_price)

    if not waste.steam_generator_needed:
        extra_steam_cost = STEAM_GENERATOR_COSTS.get(machine.size_code)

        if extra_steam_cost is None:
            # hard fail als we de code niet kennen
            raise ValueError(f"No steam generator cost configured for machine {machine.size_code}")

        investment -= Decimal(extra_steam_cost)


    # 6. Terugverdientijd (in maanden)
    # -----------------------------
    months = payback_period_months(investment, annual_savings)
    simple_months = simple_payback_months(investment, annual_savings)

    if months is None:
        payback_value_to_store = None
    else:
        try:
            payback_value_to_store = float(months)
        except:
            # fallback: forceer conversie via str → float
            payback_value_to_store = float(str(months))
        # werkt voor int, decimal, float en none


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

