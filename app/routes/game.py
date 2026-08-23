"""
Hotel Magnifique — Game Routes
"""
from decimal import Decimal
from flask import Blueprint, jsonify, redirect, render_template, request, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Partida, Dia, Decision, Resultado
from app.engine import simulation, seasons as season_engine, events as event_engine
from app.utils.feedback import get_feedback
from app.engine.constants import INITIAL_CAPITAL, INITIAL_REPUTATION, ROOMS_TOTAL
from app.routes.auth import _proxy_web_service


game_bp = Blueprint('game', __name__, url_prefix='/game')


@game_bp.route('/no-game', methods=['GET'])
@login_required
def no_game():
    """Estado sin partida activa."""
    proxied = _proxy_web_service('/game/no-game')
    if proxied is not None:
        return proxied

    return render_template('game/no_game.html')


@game_bp.route('/new', methods=['POST'])
@login_required
def new_game():
    """Crear nueva partida de 30 días."""
    # Si ya tiene partida activa, no crear otra
    activa = Partida.query.filter_by(
        usuario_id=current_user.id, activa=True
    ).first()
    if activa:
        return redirect(url_for('game.play'))

    partida = Partida(
        usuario_id=current_user.id,
        dia_actual=1,
        capital=INITIAL_CAPITAL,
        reputacion=INITIAL_REPUTATION,
        activa=True,
    )
    db.session.add(partida)
    db.session.commit()

    flash('¡Nueva partida iniciada! Día 1 de 30.', 'success')
    return redirect(url_for('game.play'))


@game_bp.route('/final-results', methods=['GET'])
@login_required
def final_results():
    """Mostrar resultados finales de la última partida terminada."""
    partida_activa = Partida.query.filter_by(
        usuario_id=current_user.id, activa=True
    ).first()
    if partida_activa:
        return redirect(url_for('game.play'))

    partida = Partida.query.filter_by(
        usuario_id=current_user.id, activa=False
    ).order_by(Partida.updated_at.desc()).first()
    if not partida or not partida.grado_final:
        return redirect(url_for('game.no_game'))

    return render_template('game/end.html', partida=partida)


@game_bp.route('/play', methods=['GET'])
@login_required
def play():
    """Obtener estado de la partida activa."""
    partida = Partida.query.filter_by(
        usuario_id=current_user.id, activa=True
    ).first()

    if not partida:
        return redirect(url_for('game.no_game'))

    dia = Dia.query.filter_by(
        partida_id=partida.id, numero=partida.dia_actual
    ).first()

    if not dia:
        # Generar día si no existe (partida reanudada)
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

    # Último resultado (del día anterior)
    prev_resultado = None
    if partida.dia_actual > 1:
        prev_dia = Dia.query.filter_by(
            partida_id=partida.id, numero=partida.dia_actual - 1
        ).first()
        if prev_dia:
            prev_resultado = Resultado.query.filter_by(dia_id=prev_dia.id).first()

    # Decisiones actuales del día
    decision = Decision.query.filter_by(dia_id=dia.id).first()
    if not decision:
        decision = Decision(
            dia_id=dia.id,
            precio=120,
            personal=4,
            marketing=100,
        )
        db.session.add(decision)
        db.session.commit()

    return render_template('game/play.html',
        partida=partida,
        dia=dia,
        decision=decision,
        prev_resultado=prev_resultado,
        rooms_total=ROOMS_TOTAL,
    )


@game_bp.route('/day', methods=['POST'])
@login_required
def run_day():
    """Recibir decisiones del día → procesar → devolver resultados."""
    partida = Partida.query.filter_by(
        usuario_id=current_user.id, activa=True
    ).first()
    if not partida:
        return jsonify({'error': 'Sin partida activa'}), 400

    dia = Dia.query.filter_by(
        partida_id=partida.id, numero=partida.dia_actual
    ).first()
    if not dia:
        return jsonify({'error': 'Día no encontrado'}), 404

    # Leer decisiones del formulario
    decisions = simulation.Decisions(
        price=int(request.form.get('precio', 120)),
        staff=int(request.form.get('personal', 4)),
        marketing=int(request.form.get('marketing', 100)),
        breakfast=bool(request.form.get('desayuno')),
        pool=bool(request.form.get('piscina')),
        spa=bool(request.form.get('spa')),
    )

    # Guardar decisiones
    decision = Decision.query.filter_by(dia_id=dia.id).first()
    if not decision:
        decision = Decision(dia_id=dia.id)
    decision.precio = decisions.price
    decision.personal = decisions.staff
    decision.marketing = decisions.marketing
    decision.desayuno = decisions.breakfast
    decision.piscina = decisions.pool
    decision.spa = decisions.spa
    db.session.add(decision)

    # Obtener temporada y evento
    season = season_engine.get_season(partida.dia_actual)
    event = event_engine.pick_event()

    # Ejecutar simulación
    result = simulation.simulate(
        decisions=decisions,
        current_reputation=partida.reputacion,
        season=season,
        event=event,
        add_noise=True,
    )

    # Guardar resultado
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

    # Actualizar partida
    partida.capital += result.profit
    partida.reputacion = result.new_reputation
    partida.ganancia_total += result.profit
    partida.ingreso_total += result.revenue
    partida.gasto_total += result.expenses

    # Verificar fin de partida
    game_over = partida.dia_actual >= 30 or partida.capital <= 0
    if game_over:
        partida.activa = False
        partida.grado_final = _calc_grade(partida)
    else:
        partida.dia_actual += 1

    db.session.commit()

    # Generar feedback
    feedback = get_feedback(result, decisions.staff, result.revenue, partida.capital)

    return jsonify({
        'rooms': result.rooms_occupied,
        'occupancy': float(result.occupancy),
        'revenue': float(result.revenue),
        'expenses': float(result.expenses),
        'profit': float(result.profit),
        'reputation': float(result.new_reputation),
        'rep_change': float(result.rep_change),
        'feedback': feedback,
        'game_over': game_over,
        'next_day': partida.dia_actual if not game_over else None,
        'grade': partida.grado_final,
        'final_results_url': url_for('game.final_results') if game_over else None,
    })


def _calc_grade(partida: Partida) -> str:
    """Calcula el grado final (S/A/B/C/D/💸)."""
    if partida.capital <= 0:
        return '💸'
    expense_ratio = 0 if partida.gasto_total <= 0 else float(partida.ingreso_total) / float(partida.gasto_total)
    score = (
        float(partida.ganancia_total) / 1000 * 0.4 +
        float(partida.reputacion) * 12 +
        expense_ratio * 22
    )
    if score >= 85 and float(partida.reputacion) >= 4.5:
        return 'S'
    if score >= 65 and float(partida.reputacion) >= 3.8:
        return 'A'
    if score >= 45:
        return 'B'
    if score >= 25:
        return 'C'
    return 'D'
