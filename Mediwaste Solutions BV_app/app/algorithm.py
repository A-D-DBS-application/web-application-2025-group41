from app.algorithm_settings import values, models

#hoeveel vaten passen in een machine -> bruikbaar volume machine = veelvoud van inhoud vaten (=inhoud zakken)
def vaten_per_cycle(inhoud_vat_l, machine_cap_l):
    if inhoud_vat_l<= 0:
        return 0
    return int(machine_cap_l // inhoud_vat_l)

#aanbevolen machine gebaseerd op volume per cyclus en volledige vaten
def recommend_machine(rma_dichtheid, rma_vaten, inhoud_vat, werkdagen): #rma_dichtheid hier eig niet nodig
    total_volume_l= rma_vaten*inhoud_vat #totaal volume rma in liter
    max_yearly_cycles= values.max_daily_cycles * int(werkdagen) #max cycli per jaar

    if max_yearly_cycles<= 0:
        return None

    volume_per_cycle= total_volume_l / max_yearly_cycles #volume dat per cyclus verwerkt moet worden

    #zoek kleinste machine die hieraan voldoet
    for machine in models.machine_list:
        passen = vaten_per_cycle(inhoud_vat, machine.capacity_l_per_cycle)
        if passen <= 0:
            continue
        echte_cap = passen * inhoud_vat #effectieve bruikbare liters
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
def run_user_algorithm(rma_dichtheid, rma_vaten, kost_vaten,
    inhoud_vat, kost_ophaling, kost_verwerking, paritair, werkdagen,):

    #machine aanbevelen
    machine = recommend_machine(rma_dichtheid, rma_vaten, inhoud_vat, werkdagen)
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
    return {"recommended_machine": advice_machine,
        "new_cost": monthly_cost,
        "payback": None,
        "dcf": None,}
