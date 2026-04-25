"""
Hotel Magnifique — Feedback al Jugador
Puerto de getFeedback() (hotel-magnifique.html líneas 872-883)
"""
from app.engine.simulation import SimulationResult
from decimal import Decimal


STAFF_COST = Decimal('130')


def get_feedback(
    result: SimulationResult,
    staff: int,
    revenue: Decimal,
    money: Decimal,
) -> str:
    """Genera un mensaje de retroalimentación contextual."""
    occ = float(result.occupancy)
    sr = staff / result.rooms_occupied if result.rooms_occupied > 0 else 1

    if money <= 0:
        return (
            '💸 El hotel se ha quedado sin capital. Los gastos fijos se pagan '
            'aunque no haya huéspedes. ¡Controla siempre tus costos!'
        )
    if result.profit < -600:
        return (
            '⚠️ Pérdidas importantes. El personal y los servicios cuestan '
            'aunque las habitaciones estén vacías. Reduce gastos cuando la demanda es baja.'
        )
    if occ < 0.20:
        return (
            '📊 Muy poca ocupación hoy. Prueba a bajar el precio o invertir '
            'más en marketing para atraer huéspedes.'
        )
    if occ > 0.88 and sr < 0.15:
        return (
            '⚠️ Hotel lleno pero poco personal. Los huéspedes insatisfechos '
            'dañan la reputación. En alta ocupación: contrata más staff.'
        )
    if occ > 0.80 and float(result.profit) > 600:
        return (
            '🌟 ¡Día brillante! Alta ocupación y gran beneficio. '
            'Tus decisiones fueron excelentes.'
        )
    if staff * float(STAFF_COST) > float(revenue) * 0.45:
        return (
            '💡 El costo de personal es muy elevado respecto a los ingresos. '
            'Ajusta el número de empleados según la ocupación esperada.'
        )
    if float(result.profit) > 0 and occ > 0.55:
        return '✅ Buen equilibrio entre precio, ocupación y gastos. ¡Sigue así!'
    return '💼 Sigue ajustando tus decisiones. Observa la temporada y los eventos.'