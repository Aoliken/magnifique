"""
Hotel Magnifique — Game Routes
"""
from decimal import Decimal
from pathlib import Path

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from app import db
from app.models import Configuracion, Partida, Dia, Decision, Resultado, Usuario
from app.engine import simulation, seasons as season_engine, events as event_engine
from app.utils.feedback import get_feedback
from app.engine.constants import INITIAL_CAPITAL, INITIAL_REPUTATION, ROOMS_TOTAL
from app.routes.auth import _proxy_web_service
from app.utils.preferences import (
    CURRENCY_CODES,
    CURRENCY_SYMBOLS,
    DIFFICULTY_CODES,
    LANGUAGE_CODES,
    translate,
)


game_bp = Blueprint('game', __name__, url_prefix='/game')


def _get_or_create_config(usuario_id: str) -> Configuracion:
    """Returns the player's saved preferences, creating defaults on first access."""
    config = Configuracion.query.filter_by(usuario_id=usuario_id).first()
    if config is None:
        config = Configuracion(usuario_id=usuario_id)
        db.session.add(config)
        db.session.commit()
    return config


@game_bp.route('/no-game', methods=['GET'])
@login_required
def no_game():
    """Estado sin partida activa."""
    proxied = _proxy_web_service('/game/no-game')
    if proxied is not None:
        return proxied

    return render_template('game/no_game.html')


@game_bp.route('/menu', methods=['GET'])
@login_required
def menu():
    """Menú principal tras iniciar sesión."""
    partida_activa = Partida.query.filter_by(
        usuario_id=current_user.id, activa=True
    ).first()
    config = _get_or_create_config(current_user.id)
    tr = translate(config.idioma)
    return render_template(
        'game/menu.html',
        partida=partida_activa,
        config=config,
        tr=tr,
        moneda=config.moneda,
    )


@game_bp.route('/options', methods=['GET'])
@login_required
def options():
    """Pantalla de opciones (idioma, moneda, dificultad)."""
    config = _get_or_create_config(current_user.id)
    tr = translate(config.idioma)
    return render_template(
        'game/options.html',
        config=config,
        tr=tr,
    )


@game_bp.route('/options', methods=['POST'])
@login_required
def save_options():
    """Guardar opciones de idioma, moneda y dificultad."""
    config = _get_or_create_config(current_user.id)

    idioma = request.form.get('idioma', '')
    moneda = request.form.get('moneda', '')
    dificultad = request.form.get('dificultad', '')

    if (
        idioma not in LANGUAGE_CODES
        or moneda not in CURRENCY_CODES
        or dificultad not in DIFFICULTY_CODES
    ):
        flash(translate(config.idioma)['invalid_options'], 'error')
        return redirect(url_for('game.options'))

    config.idioma = idioma
    config.moneda = moneda
    config.dificultad = dificultad
    db.session.commit()

    flash(translate(idioma)['saved'], 'success')
    return redirect(url_for('game.options'))


@game_bp.route('/tutorial', methods=['GET'])
@login_required
def tutorial():
    """Tutorial del juego (manual del jugador)."""
    config = _get_or_create_config(current_user.id)
    tr = translate(config.idioma)
    return render_template('game/tutorial.html', tr=tr)


@game_bp.route('/manual', methods=['GET'])
@login_required
def manual():
    """Sirve el manual del jugador (manual-hotel-magnifique.html)."""
    manual_path = Path(current_app.root_path).parent / 'manual-hotel-magnifique.html'
    if not manual_path.is_file():
        abort(404)
    return send_file(manual_path)


@game_bp.route('/ranking', methods=['GET'])
@login_required
def ranking():
    """Ranking de los mejores jugadores (partidas terminadas)."""
    config = _get_or_create_config(current_user.id)
    tr = translate(config.idioma)

    finished = (
        Partida.query
        .join(Usuario, Usuario.id == Partida.usuario_id)
        .filter(Partida.activa.is_(False), Partida.grado_final.isnot(None))
        .order_by(
            Partida.ganancia_total.desc(),
            Partida.reputacion.desc(),
            Partida.updated_at.asc(),
        )
        .all()
    )

    # Mejor partida por jugador (hasta 10 jugadores distintos)
    top: list[Partida] = []
    seen: set[str] = set()
    for partida in finished:
        if partida.usuario_id in seen:
            continue
        seen.add(partida.usuario_id)
        top.append(partida)
        if len(top) >= 10:
            break

    return render_template(
        'game/ranking.html',
        top=top,
        tr=tr,
        moneda=config.moneda,
    )


@game_bp.route('/new', methods=['POST'])
@login_required
def new_game():
    """Crear nueva partida de 30 días.

    - Sin partida activa: crea una nueva (día 1).
    - Con partida activa sin `force`: reutiliza la existente (no se pierde progreso).
    - Con partida activa y `force=1`: archiva la actual y crea una partida fresca.
    """
    partida_activa = Partida.query.filter_by(
        usuario_id=current_user.id, activa=True
    ).first()
    if partida_activa:
        if request.form.get('force') != '1':
            return redirect(url_for('game.play'))
        partida_activa.activa = False
        db.session.commit()

    config = _get_or_create_config(current_user.id)
    partida = Partida(
        usuario_id=current_user.id,
        dia_actual=1,
        capital=INITIAL_CAPITAL,
        reputacion=INITIAL_REPUTATION,
        activa=True,
        dificultad=config.dificultad,
    )
    db.session.add(partida)
    db.session.commit()

    flash(translate(config.idioma)['new_ok'], 'success')
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

    return render_template('game/end.html', partida=partida,
        moneda=_get_or_create_config(current_user.id).moneda)


@game_bp.route('/play', methods=['GET'])
@login_required
def play():
    """Obtener estado de la partida activa."""
    partida = Partida.query.filter_by(
        usuario_id=current_user.id, activa=True
    ).first()

    if not partida:
        return redirect(url_for('game.menu'))

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
        moneda=_get_or_create_config(current_user.id).moneda,
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
        dificultad=partida.dificultad or 'media',
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
