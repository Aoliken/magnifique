"""
Hotel Magnifique — Temporadas
Puerto de SEASONS array (hotel-magnifique.html líneas 550-555)
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Season:
    name: str
    from_day: int
    to_day: int
    factor: Decimal


SEASONS: tuple[Season, ...] = (
    Season(name='Primavera 🌸', from_day=1,  to_day=7,  factor=Decimal('0.62')),
    Season(name='Verano ☀️',    from_day=8,  to_day=15, factor=Decimal('0.88')),
    Season(name='Otoño 🍂',     from_day=16, to_day=22, factor=Decimal('0.65')),
    Season(name='Invierno ❄️',  from_day=23, to_day=30, factor=Decimal('0.43')),
)


def get_season(day: int) -> Season:
    """Retorna la temporada para un día dado."""
    for s in SEASONS:
        if s.from_day <= day <= s.to_day:
            return s
    return SEASONS[-1]  # Invierno por defecto