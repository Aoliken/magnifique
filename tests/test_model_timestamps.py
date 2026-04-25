"""Regression tests for model timestamp defaults."""

from decimal import Decimal
import warnings

from app import db
from app.models import Ajuste, Dia, Partida, Usuario


def _utcnow_warnings(records):
    return [
        warning
        for warning in records
        if issubclass(warning.category, DeprecationWarning)
        and "utcnow" in str(warning.message)
    ]


def test_model_default_timestamps_do_not_emit_utcnow_deprecation(app):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")

        usuario = Usuario(email="timestamps@test.com", nombre="Timestamps", rol="usuario")
        usuario.set_password("password123")
        db.session.add(usuario)
        db.session.commit()

        partida = Partida(
            usuario_id=usuario.id,
            dia_actual=1,
            capital=Decimal("5000.00"),
            reputacion=Decimal("3.0"),
            activa=True,
        )
        db.session.add(partida)
        db.session.commit()

        dia = Dia(
            partida_id=partida.id,
            numero=1,
            temporada="Primavera 🌸",
            evento="Día Normal ☁️",
            factor_temporada=Decimal("0.62"),
            factor_evento=Decimal("1.00"),
        )
        db.session.add(dia)
        db.session.commit()

        ajuste = Ajuste(
            partida_id=partida.id,
            parametro="inflacion",
            valor_base=Decimal("1.0000"),
            valor_actual=Decimal("1.0500"),
            motivo="manual",
        )
        db.session.add(ajuste)
        db.session.commit()

    assert _utcnow_warnings(caught) == []


def test_model_timestamp_updates_do_not_emit_utcnow_deprecation(app):
    usuario = Usuario(email="updates@test.com", nombre="Updates", rol="usuario")
    usuario.set_password("password123")
    db.session.add(usuario)
    db.session.commit()

    partida = Partida(
        usuario_id=usuario.id,
        dia_actual=1,
        capital=Decimal("5000.00"),
        reputacion=Decimal("3.0"),
        activa=True,
    )
    db.session.add(partida)
    db.session.commit()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        partida.dia_actual = 2
        db.session.commit()

    assert _utcnow_warnings(caught) == []
