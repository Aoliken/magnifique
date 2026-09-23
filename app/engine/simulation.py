"""
Hotel Magnifique — Simulation Engine
Puerto completo de simulate() (hotel-magnifique.html líneas 617-687)
"""
import random
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple

from app.engine.constants import (
    ROOMS_TOTAL, OVERHEAD, STAFF_COST,
    POOL_COST, SPA_COST, BKF_COST,
)
from app.engine.seasons import get_season, Season
from app.engine.events import pick_event, GameEvent


def _d(value: float) -> Decimal:
    """Convierte a Decimal con 2 decimales."""
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


@dataclass
class Decisions:
    price: int
    staff: int
    marketing: int
    breakfast: bool
    pool: bool
    spa: bool


class SimulationResult(NamedTuple):
    rooms_occupied: int
    occupancy: Decimal
    revenue: Decimal
    expenses: Decimal
    profit: Decimal
    new_reputation: Decimal
    rep_change: Decimal
    opt_price: Decimal


def simulate(
    decisions: Decisions,
    current_reputation: Decimal,
    season: Season,
    event: GameEvent,
    add_noise: bool = True,
    dificultad: str = 'media',
) -> SimulationResult:
    """
    Función core del juego.
    
    1. Calcula demanda base (temporada × evento × reputación)
    2. Calcula precio óptimo
    3. Ajusta por ratio precio/precio_óptimo
    4. Ajusta por marketing y amenities
    5. Calcula ocupación con ruido opcional
    6. Calcula ingresos, gastos y reputación

    `dificultad` ('facil' | 'media' | 'dificil') altera la demanda:
      - facil:   demanda alta casi todos los días (multiplicador fijo) y menos ruido.
      - media:   comportamiento por defecto (sin cambios).
      - dificil: cambios de demanda abruptos (multiplicador aleatorio amplio y más ruido).
    """
    rep = float(current_reputation)

    # 1. Demanda base
    demand = float(season.factor) * float(event.mod) * (0.74 + rep * 0.085)

    # Dificultad — ajusta la demanda antes del resto del cálculo
    noise_amp = 0.08
    if dificultad == 'facil':
        demand *= 1.25
        noise_amp = 0.04
    elif dificultad == 'dificil':
        demand *= random.uniform(0.70, 1.40)
        noise_amp = 0.16

    # 2. Precio óptimo (varía con reputación y temporada)
    opt_price = (55 + rep * 22) * (0.55 + float(season.factor) * 0.88)
    opt_price_d = _d(opt_price)

    # 3. Factor de precio (función escalonada)
    ratio = decisions.price / opt_price
    if      ratio < 0.60: pf = 1.14
    elif ratio < 0.85: pf = 1.06
    elif ratio < 1.10: pf = 1.00
    elif ratio < 1.35: pf = 0.87
    elif ratio < 1.65: pf = 0.68
    elif ratio < 2.00: pf = 0.48
    else:               pf = 0.28

    # 4. Factor de marketing
    mf = 1.0 + (decisions.marketing / 500) * 0.28

    # 5. Factor de amenities
    af = 1.0
    if decisions.breakfast: af += 0.08
    if decisions.pool:      af += 0.11
    if decisions.spa:      af += 0.13

    # 6. Ocupación
    occupancy = demand * pf * mf * af
    if add_noise:
        occupancy += (random.random() - 0.5) * noise_amp
    occupancy = max(0.02, min(1.0, occupancy))

    rooms_occupied = round(occupancy * ROOMS_TOTAL)

    # 7. Ingresos
    rpr = decisions.price
    if decisions.breakfast: rpr += 22
    if decisions.pool:      rpr += 18
    if decisions.spa:       rpr += 35
    revenue = _d(rooms_occupied * rpr)

    # 8. Gastos
    expenses = _d(float(OVERHEAD) + decisions.staff * float(STAFF_COST) + decisions.marketing)
    if decisions.breakfast: expenses += rooms_occupied * BKF_COST
    if decisions.pool:      expenses += POOL_COST
    if decisions.spa:      expenses += SPA_COST

    # 9. Balance
    profit = revenue - expenses

    # 10. Cambio de reputación
    sr = decisions.staff / rooms_occupied if rooms_occupied > 0 else 2
    if      sr >= 0.35: rc = 0.08
    elif sr >= 0.20: rc = 0.02
    elif sr < 0.15:  rc = -0.15
    else:            rc = 0.00

    if decisions.price > 200 and not decisions.spa and not decisions.pool and rep < 3.5:
        rc -= 0.07
    if decisions.price > 150 and decisions.breakfast and decisions.pool:
        rc += 0.04
    if occupancy > 0.90 and sr < 0.18:
        rc -= 0.12

    if add_noise:
        rc += (random.random() - 0.5) * 0.08

    new_rep = max(1.0, min(5.0, rep + rc))

    return SimulationResult(
        rooms_occupied=rooms_occupied,
        occupancy=_d(occupancy),
        revenue=revenue,
        expenses=expenses,
        profit=profit,
        new_reputation=_d(new_rep),
        rep_change=_d(rc),
        opt_price=opt_price_d,
    )