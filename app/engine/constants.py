"""
Hotel Magnifique — Constantes del Juego
Puerto de hotel-magnifique.html (líneas 542-548)
"""
from decimal import Decimal

# ── Configuración General ───────────────────────────────
DAYS_TOTAL: int = 30
ROOMS_TOTAL: int = 20

# ── Costos Fijos ───────────────────────────────────────
OVERHEAD: Decimal = Decimal('180')     # Costo fijo diario
STAFF_COST: Decimal = Decimal('130')  # Por empleado/día
POOL_COST: Decimal = Decimal('70')    # Fijo/día
SPA_COST: Decimal = Decimal('100')    # Fijo/día
BKF_COST: Decimal = Decimal('14')    # Por habitación ocupada

# ── Condiciones Iniciales ────────────────────────────
INITIAL_CAPITAL: Decimal = Decimal('5000')
INITIAL_REPUTATION: Decimal = Decimal('3.0')