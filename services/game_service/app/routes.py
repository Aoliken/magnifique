"""HTTP routes for the extracted game service."""

from decimal import Decimal

from flask import Blueprint, current_app, g, jsonify, request

from app import db
from app.engine import events as event_engine
from app.engine import seasons as season_engine
from app.engine import simulation
from app.engine.constants import INITIAL_CAPITAL, INITIAL_REPUTATION
from app.models import Decision, Dia, Partida, Resultado
from app.utils.feedback import get_feedback
from services.game_service.app.auth_client import AuthServiceUnavailable, validate_session_token

game_api_bp = Blueprint("game_api", __name__)


@game_api_bp.before_request
def require_valid_session():
    token = request.cookies.get(current_app.config["SESSION_COOKIE_NAME"])

    try:
        session = validate_session_token(token)
    except AuthServiceUnavailable:
        return jsonify({"error": "auth_service_unavailable"}), 503

    if session is None:
        return jsonify({"error": "authentication_required"}), 401

    g.authenticated_user_id = session.user_id
    g.authenticated_user_role = session.rol
    return None


def _active_game() -> Partida | None:
    return Partida.query.filter_by(usuario_id=g.authenticated_user_id, activa=True).first()


def _get_or_create_day(partida: Partida) -> Dia:
    dia = Dia.query.filter_by(partida_id=partida.id, numero=partida.dia_actual).first()
    if dia:
        return dia

    event = event_engine.pick_event()
    season = season_engine.get_season(partida.dia_actual)
    dia = Dia(
        partida_id=partida.id,
        numero=partida.dia_actual,
        temporada=season.name,
        evento=event.name,
        factor_temporada=season.factor,
        factor_evento=event.mod,
    )
    db.session.add(dia)
    db.session.commit()
    return dia


def _get_or_create_decision(dia: Dia) -> Decision:
    decision = Decision.query.filter_by(dia_id=dia.id).first()
    if decision:
        return decision

    decision = Decision(dia_id=dia.id, precio=120, personal=4, marketing=100)
    db.session.add(decision)
    db.session.commit()
    return decision


def _serialize_previous_result(partida: Partida):
    if partida.dia_actual <= 1:
        return None

    prev_dia = Dia.query.filter_by(partida_id=partida.id, numero=partida.dia_actual - 1).first()
    if not prev_dia:
        return None

    resultado = Resultado.query.filter_by(dia_id=prev_dia.id).first()
    if not resultado:
        return None

    return {
        "balance": float(resultado.balance),
        "reputacion": float(resultado.reputacion),
        "ocupacion_pct": float(resultado.ocupacion_pct),
    }


@game_api_bp.post("/api/v1/games")
def create_game():
    partida = _active_game()
    if partida is None:
        partida = Partida(
            usuario_id=g.authenticated_user_id,
            dia_actual=1,
            capital=INITIAL_CAPITAL,
            reputacion=INITIAL_REPUTATION,
            activa=True,
        )
        db.session.add(partida)
        db.session.commit()

    return jsonify({"game_id": partida.id, "current_day": partida.dia_actual}), 201


@game_api_bp.get("/api/v1/games/current")
def get_current_game():
    partida = _active_game()
    if partida is None:
        return jsonify({"error": "no_active_game"}), 404

    dia = _get_or_create_day(partida)
    decision = _get_or_create_decision(dia)

    return jsonify(
        {
            "game": {"active": partida.activa, "current_day": partida.dia_actual},
            "day": {
                "numero": dia.numero,
                "temporada": dia.temporada,
                "evento": dia.evento,
            },
            "decision": {
                "precio": decision.precio,
                "personal": decision.personal,
                "marketing": decision.marketing,
                "desayuno": decision.desayuno,
                "piscina": decision.piscina,
                "spa": decision.spa,
            },
            "previous_result": _serialize_previous_result(partida),
        }
    )


@game_api_bp.post("/api/v1/days/current/run")
def run_current_day():
    partida = _active_game()
    if partida is None:
        return jsonify({"error": "no_active_game"}), 404

    dia = _get_or_create_day(partida)
    payload = request.get_json(silent=True) or request.form
    decisions = simulation.Decisions(
        price=int(payload.get("precio", 120)),
        staff=int(payload.get("personal", 4)),
        marketing=int(payload.get("marketing", 100)),
        breakfast=bool(payload.get("desayuno")),
        pool=bool(payload.get("piscina")),
        spa=bool(payload.get("spa")),
    )

    decision = Decision.query.filter_by(dia_id=dia.id).first() or Decision(dia_id=dia.id)
    decision.precio = decisions.price
    decision.personal = decisions.staff
    decision.marketing = decisions.marketing
    decision.desayuno = decisions.breakfast
    decision.piscina = decisions.pool
    decision.spa = decisions.spa
    db.session.add(decision)

    season = season_engine.get_season(partida.dia_actual)
    event = event_engine.pick_event()
    result = simulation.simulate(
        decisions=decisions,
        current_reputation=partida.reputacion,
        season=season,
        event=event,
        add_noise=True,
    )

    resultado = Resultado(
        dia_id=dia.id,
        habitaciones_ocupadas=result.rooms_occupied,
        ocupacion_pct=result.occupancy,
        ingreso=result.revenue,
        gasto=result.expenses,
        balance=result.profit,
        reputacion=result.new_reputation,
        reputacion_cambio=result.rep_change,
        demanda_base=Decimal(str(season.factor * event.mod)),
        precio_optimo=result.opt_price,
    )
    db.session.add(resultado)

    partida.capital += result.profit
    partida.reputacion = result.new_reputation
    partida.ganancia_total += result.profit
    partida.ingreso_total += result.revenue
    partida.gasto_total += result.expenses

    game_over = partida.dia_actual >= 30 or partida.capital <= 0
    if game_over:
        partida.activa = False
        partida.grado_final = _calc_grade(partida)
    else:
        partida.dia_actual += 1

    db.session.commit()

    feedback = get_feedback(result, decisions.staff, result.revenue, partida.capital)
    return jsonify(
        {
            "rooms": result.rooms_occupied,
            "occupancy": float(result.occupancy),
            "revenue": float(result.revenue),
            "expenses": float(result.expenses),
            "profit": float(result.profit),
            "reputation": float(result.new_reputation),
            "rep_change": float(result.rep_change),
            "feedback": feedback,
            "game_over": game_over,
            "next_day": partida.dia_actual if not game_over else None,
            "grade": partida.grado_final,
        }
    )


def _calc_grade(partida: Partida) -> str:
    if partida.capital <= 0:
        return "💸"

    expense_ratio = 0 if partida.gasto_total <= 0 else float(partida.ingreso_total) / float(partida.gasto_total)
    score = (
        float(partida.ganancia_total) / 1000 * 0.4
        + float(partida.reputacion) * 12
        + expense_ratio * 22
    )
    if score >= 85 and float(partida.reputacion) >= 4.5:
        return "S"
    if score >= 65 and float(partida.reputacion) >= 3.8:
        return "A"
    if score >= 45:
        return "B"
    if score >= 25:
        return "C"
    return "D"
