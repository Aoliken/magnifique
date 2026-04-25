"""
Hotel Magnifique — Admin Routes
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Usuario, Partida


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Panel de control admin — métricas globales."""
    if not current_user.is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403

    total_users = Usuario.query.count()
    total_partidas = Partida.query.count()
    activas = Partida.query.filter_by(activa=True).count()
    from sqlalchemy import func
    avg_capital = db.session.query(
        func.avg(Partida.capital)
    ).scalar() or 0
    avg_rep = db.session.query(
        func.avg(Partida.reputacion)
    ).scalar() or 0

    return jsonify({
        'total_users': total_users,
        'total_partidas': total_partidas,
        'active_games': activas,
        'avg_capital': float(avg_capital),
        'avg_reputation': float(avg_rep),
    })


@admin_bp.route('/params', methods=['POST'])
@login_required
def adjust_params():
    """Ajustar parámetros base de la simulación."""
    if not current_user.is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403

    param = request.json.get('param')
    value = request.json.get('value')
    # Registrar ajuste en tabla Ajuste (futuro)
    return jsonify({'status': 'ok', 'param': param, 'value': value})