"""Constants/Assumptions used in the calculations:"""
rma_avg_density = 0.12 #1,2kg/10L => 0,12kg/1L

cycle_duration = 30 #in minutes: sterilising one batch of rma
handling_duration = 7.5 #in minutes: manually loading and emptying machine
cycle_total_duration = cycle_duration + handling_duration #in minutes: total duration for one cycle, handling included

max_daily_running_time_hrs = 5 #in hours: max daily time the machine is operational, handling included
max_daily_running_time_min = max_daily_running_time_hrs * 60 #in minutes: max daily time the machine is operational, handling included

max_daily_cycles = max_daily_running_time_min // cycle_total_duration #in amount of cycles: rounded down max amount of daily cycles

def recommend_machine(rma_kg, inhoud_vat, werkdagen):

    rma_volume = rma_kg / rma_avg_density #volume in liter
    max_yearly_cycles = max_daily_cycles * werkdagen
    volume_per_cycle = rma_volume / max_yearly_cycles #volume in liter
    
    if volume_per_cycle <= 100:
        return 'T100 machine.'
    elif 100 < volume_per_cycle <= 150:
        return 'T150 machine.'
    elif 150 < volume_per_cycle <= 350:
        return 'T350 machine.'
    elif 350 < volume_per_cycle <= 700:
        return 'T700 machine.'
    else:
        return "Geen machine beschikbaar voor deze behoefte."


def run_user_algorithm(
    rma_kg, rma_vaten, kost_vaten,
    inhoud_vat, kost_ophaling, kost_verwerking,
    paritair, werkdagen
):
    """
    TODO: vul je eigen algoritme hier in.
    Return een dict met: recommended_machine, new_cost, payback, dcf.
    """
    advice_machine = recommend_machine(rma_kg, inhoud_vat, werkdagen)
    return {
        "recommended_machine": advice_machine,
        "new_cost": None,
        "payback": None,
        "dcf": None,
    }
