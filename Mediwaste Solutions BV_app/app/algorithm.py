from app.algorithm_settings import values, models

def recommend_machine(rma_kg, inhoud_vat, werkdagen): #recommends a machine based on the needs of the client
    rma_volume= rma_kg / values.rma_avg_density
    max_yearly_cycles= values.max_daily_cycles*werkdagen

    if max_yearly_cycles<= 0: #watch out for division by zero
        return None

    volume_per_cycle= rma_volume / max_yearly_cycles
    for machine in models.machine_list:
        if volume_per_cycle<= machine.capacity_l_per_cycle:
            return machine
    return None  #no machines found that fit the criteria

def annuity(price, months): #calculates the annuity of the investment
    i = values.yearly_interest / 12
    a =(price * i) / (1 - (1 + i) ** (-months))
    return a

#main algorithm
def run_user_algorithm(
    rma_kg: int|float, rma_vaten: int|float, kost_vaten: int|float,
    inhoud_vat: int|float, kost_ophaling: int|float, kost_verwerking: int|float,
    paritair: int|float, werkdagen: int|float):

    machine = recommend_machine(rma_kg, inhoud_vat, werkdagen)
    if machine is not None:
        advice_machine= machine.name
        machine_price = machine.price
    else:
        advice_machine= None
        machine_price= None

    if machine_price is not None:
        monthly_cost = annuity(machine_price, 120)
    else:
        monthly_cost= None

    return {"recommended_machine": advice_machine,
        "new_cost": monthly_cost,
        "payback": None,
        "dcf": None,}
