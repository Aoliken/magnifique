"""
Hotel Magnifique — Eventos Aleatorios
Puerto de EVENTS array (hotel-magnifique.html líneas 557-565)
"""
import random
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class GameEvent:
    name: str
    desc: str
    mod: Decimal  # multiplicador de demanda
    prob: Decimal  # probabilidad (0-1)
    tip: str     # consejo al jugador


EVENTS: tuple[GameEvent, ...] = (
    GameEvent(
        name='Congreso Internacional 🎤',
        desc='Gran congreso en la ciudad. Alta demanda de habitaciones.',
        mod=Decimal('1.50'), prob=Decimal('0.11'),
        tip='Sube el precio: la demanda está disparada hoy.'
    ),
    GameEvent(
        name='Feria de Negocios 💼',
        desc='Ejecutivos de todo el país buscan alojamiento premium.',
        mod=Decimal('1.40'), prob=Decimal('0.09'),
        tip='Los ejecutivos valoran el spa. ¡Actívalo!'
    ),
    GameEvent(
        name='Fin de Semana Largo 🏖️',
        desc='Muchas familias aprovechan el fin de semana extendido.',
        mod=Decimal('1.30'), prob=Decimal('0.17'),
        tip='Las familias valoran la piscina. Considera activarla.'
    ),
    GameEvent(
        name='Festival de la Ciudad 🎡',
        desc='Un festival local atrae turistas de toda la región.',
        mod=Decimal('1.25'), prob=Decimal('0.13'),
        tip='Buen momento para ofrecer el desayuno incluido.'
    ),
    GameEvent(
        name='Tormenta ⛈️',
        desc='El mal tiempo reduce significativamente la afluencia de viajeros.',
        mod=Decimal('0.58'), prob=Decimal('0.08'),
        tip='Baja el precio: los pocos viajeros buscan gangas.'
    ),
    GameEvent(
        name='Obras en la Ciudad 🚧',
        desc='Las obras dificultan el acceso al hotel y ahuyentan clientes.',
        mod=Decimal('0.72'), prob=Decimal('0.09'),
        tip='Invierte en marketing para compensar la baja visibilidad.'
    ),
    GameEvent(
        name='Día Normal ☁️',
        desc='Un día tranquilo sin eventos especiales. Demanda habitual.',
        mod=Decimal('1.00'), prob=Decimal('0.33'),
        tip='Mantén precios acordes a la temporada y tu reputación.'
    ),
)


def pick_event() -> GameEvent:
    """Selecciona un evento aleatorio basado en probabilidades."""
    r = random.random()
    cum = 0.0
    for e in EVENTS:
        cum += float(e.prob)
        if r < cum:
            return e
    return EVENTS[-1]  # Día Normal por defecto