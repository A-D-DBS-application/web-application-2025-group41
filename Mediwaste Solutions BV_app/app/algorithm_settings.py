from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)  # frozen so no-one changes anything on accident
class Constants:
    rma_avg_density: Decimal = Decimal("0.12")   # 1.2kg/10L => 0.12kg/L
    cycle_duration: Decimal = Decimal("30.0")   # minutes
    handling_duration: Decimal = Decimal("7.5") # minutes
    max_daily_running_time_hrs: Decimal = Decimal("5")  # hours
    yearly_interest: Decimal = Decimal("0.04")  # 4% rente

    @property
    def cycle_total_duration_min(self):
        return self.cycle_duration + self.handling_duration

    @property
    def max_daily_running_time_min(self):
        return self.max_daily_running_time_hrs * Decimal("60")

    @property
    def max_daily_cycles(self):
        total = self.cycle_total_duration_min
        if total > 0:
            return int(self.max_daily_running_time_min // total)
        else:
            return 0

@dataclass(frozen=True)
class Machine:
    name: str
    capacity_l_per_cycle: Decimal
    price: Decimal

    def __str__(self):
        return f"Machine: {self.name} heeft een capaciteit van {self.capacity_l_per_cycle} liter/cyclus en kost €{self.price}."

@dataclass(frozen=True)
class Machines:
    T100 = Machine("T100", Decimal("100"), Decimal("122000"))
    T150 = Machine("T150", Decimal("150"), Decimal("195000"))
    T300 = Machine("T300", Decimal("300"), Decimal("269000"))
    T700 = Machine("T700", Decimal("700"), Decimal("450000"))

    @property
    def machine_list(self):
        return [self.T100, self.T150, self.T300, self.T700]

values = Constants()
models = Machines()
