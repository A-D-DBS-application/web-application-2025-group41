from app.algorithm_settings import values, models

#hoeveel vaten passen in een machine -> bruikbaar volume machine = veelvoud van inhoud vaten (=inhoud zakken)
def vaten_per_cycle(inhoud_vat_l, machine_cap_l):
    if inhoud_vat_l<= 0:
        return 0
    return int(machine_cap_l // inhoud_vat_l)

#aanbevolen machine gebaseerd op volume per cyclus en volledige vaten
def recommend_machine(hmw_density , number_of_barrels, volume_barrel , workdays): #rma_dichtheid hier eig niet nodig
    total_volume_l= hmw_density*volume_barrel #totaal volume rma in liter
    max_yearly_cycles= values.max_daily_cycles * int(workdays) #max cycli per jaar

    if max_yearly_cycles<= 0:
        return None

    volume_per_cycle= total_volume_l / max_yearly_cycles #volume dat per cyclus verwerkt moet worden

    #zoek kleinste machine die hieraan voldoet
    for machine in models.machine_list:
        passen = vaten_per_cycle(volume_barrel, machine.capacity_l_per_cycle)
        if passen <= 0:
            continue
        echte_cap = passen * volume_barrel #effectieve bruikbare liters
        if volume_per_cycle <= echte_cap:
            return machine
    return None


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
