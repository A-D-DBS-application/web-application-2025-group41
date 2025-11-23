#All the assumptions/constants used in the algorithm are to be found and edited here.
from dataclasses import dataclass

@dataclass(frozen=True)#frozen so no-one changes anything on accident
class Constants:
    rma_avg_density: float = 0.12 #1,2kg/10L => 0,12kg/1L
    cycle_duration: float = 30.0 #in minutes: the time it takes the machine to cleanse a batch of rma
    handling_duration: float = 7.5 #in minutes: the time it takes to load and empty the machine
    max_daily_running_time_hrs: float = 5 #in hours: max amount of time (handling included) the machine should be operational daily to take in account possible failures
    yearly_interest: float = 0.04 #this is the yearly interest to pay when lending from a bank or other financial institution

    @property
    def cycle_total_duration_min(self): 
        return self.cycle_duration + self.handling_duration #amount of time needed to load, sterilize and unload a batch of rma

    @property
    def max_daily_running_time_min(self):
        return self.max_daily_running_time_hrs * 60 #in minutes: max amount of time (handling incl) the machine should be operational daily

    @property
    def max_daily_cycles(self):
        total = self.cycle_total_duration_min
        if total > 0: #watch out for dividing by 0
            return int(self.max_daily_running_time_min // total)
        else: 
            return 0

@dataclass(frozen=True) #frozen so no-one changes anything accidently
class Machine:
    name: str
    capacity_l_per_cycle: float
    price: int

    def __str__(self):
        return f"Machine: {self.name} heeft een capaciteit van {self.capacity_l_per_cycle} liter/cyclus en kost €{self.price}."

@dataclass(frozen=True) #frozen so no-one changes anything accidently
class Machines:
    T100= Machine("T100", 100, 122_000)
    T150= Machine("T150", 150, 195_000)
    T300= Machine("T300", 300, 269_000)
    T700= Machine("T700", 700, 450_000)

    @property
    def machine_list(self):
        return [self.T100, self.T150, self.T300, self.T700]

values= Constants()
models= Machines()