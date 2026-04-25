"""
Hotel Magnifique — Tests: Simulation Engine
Verifica que el motor de simulación funciona correctamente.
"""
import pytest
from decimal import Decimal
from app.engine import simulation, seasons, events
from app.engine.simulation import Decisions


class TestSeasons:
    def test_get_season_primavera(self):
        s = seasons.get_season(3)
        assert s.name == 'Primavera 🌸'
        assert s.factor == Decimal('0.62')

    def test_get_season_verano(self):
        s = seasons.get_season(10)
        assert s.name == 'Verano ☀️'
        assert s.factor == Decimal('0.88')

    def test_get_season_otonno(self):
        s = seasons.get_season(18)
        assert s.name == 'Otoño 🍂'
        assert s.factor == Decimal('0.65')

    def test_get_season_invierno(self):
        s = seasons.get_season(25)
        assert s.name == 'Invierno ❄️'
        assert s.factor == Decimal('0.43')


class TestEvents:
    def test_pick_event_returns_valid(self):
        for _ in range(100):
            e = events.pick_event()
            assert e.mod > 0
            assert e.prob > 0


class TestSimulation:
    def test_simulate_basic(self):
        """Teste simulación básica con decisiones normales."""
        decisions = Decisions(
            price=120,
            staff=4,
            marketing=100,
            breakfast=False,
            pool=False,
            spa=False,
        )
        season = seasons.get_season(5)
        event = events.GameEvent(
            name='Día Normal ☁️',
            desc='Normal',
            mod=Decimal('1.00'),
            prob=Decimal('0.33'),
            tip='Normal',
        )

        result = simulation.simulate(
            decisions=decisions,
            current_reputation=Decimal('3.0'),
            season=season,
            event=event,
            add_noise=False,
        )

        assert 0 <= result.rooms_occupied <= 20
        assert result.occupancy > 0
        assert result.opt_price > 0
        assert result.new_reputation >= Decimal('1.0')
        assert result.new_reputation <= Decimal('5.0')

    def test_simulate_low_price_increases_occupancy(self):
        """Precio bajo debería aumentar ocupación."""
        season = seasons.get_season(5)
        event = events.GameEvent(
            name='Día Normal ☁️', desc='Normal',
            mod=Decimal('1.00'), prob=Decimal('0.33'), tip='Normal',
        )

        high_price = simulation.simulate(
            Decisions(price=400, staff=4, marketing=100, breakfast=False, pool=False, spa=False),
            Decimal('3.0'), season, event, add_noise=False,
        )
        low_price = simulation.simulate(
            Decisions(price=60, staff=4, marketing=100, breakfast=False, pool=False, spa=False),
            Decimal('3.0'), season, event, add_noise=False,
        )

        assert low_price.occupancy >= high_price.occupancy

    def test_simulate_spa_amenity_bonus(self):
        """Spa debería aumentar ligeramente la ocupación."""
        season = seasons.get_season(5)
        event = events.GameEvent(
            name='Día Normal ☁️', desc='Normal',
            mod=Decimal('1.00'), prob=Decimal('0.33'), tip='Normal',
        )

        no_spa = simulation.simulate(
            Decisions(price=120, staff=4, marketing=100, breakfast=False, pool=False, spa=False),
            Decimal('3.0'), season, event, add_noise=False,
        )
        with_spa = simulation.simulate(
            Decisions(price=120, staff=4, marketing=100, breakfast=False, pool=False, spa=True),
            Decimal('3.0'), season, event, add_noise=False,
        )

        assert with_spa.occupancy >= no_spa.occupancy

    def test_simulate_congreso_increases_demand(self):
        """Congreso debería aumentar demanda vs día normal."""
        season = seasons.get_season(5)
        normal = events.GameEvent(
            name='Día Normal ☁️', desc='Normal',
            mod=Decimal('1.00'), prob=Decimal('0.33'), tip='Normal',
        )
        congreso = events.GameEvent(
            name='Congreso 🎤', desc='Congreso',
            mod=Decimal('1.50'), prob=Decimal('0.11'), tip='Subir precio',
        )

        r_normal = simulation.simulate(
            Decisions(price=120, staff=4, marketing=100, breakfast=False, pool=False, spa=False),
            Decimal('3.0'), season, normal, add_noise=False,
        )
        r_congreso = simulation.simulate(
            Decisions(price=120, staff=4, marketing=100, breakfast=False, pool=False, spa=False),
            Decimal('3.0'), season, congreso, add_noise=False,
        )

        assert r_congreso.occupancy > r_normal.occupancy

    def test_simulate_profit_calculation(self):
        """El profit debe ser revenue - expenses."""
        decisions = Decisions(
            price=100, staff=2, marketing=0,
            breakfast=False, pool=False, spa=False,
        )
        season = seasons.get_season(5)
        event = events.GameEvent(
            name='Día Normal ☁️', desc='Normal',
            mod=Decimal('1.00'), prob=Decimal('0.33'), tip='Normal',
        )

        result = simulation.simulate(
            decisions, Decimal('3.0'), season, event, add_noise=False
        )

        expected_profit = result.revenue - result.expenses
        assert result.profit == expected_profit