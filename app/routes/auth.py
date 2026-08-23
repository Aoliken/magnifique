"""
Hotel Magnifique — Auth Routes
"""
from urllib import error, request as urllib_request

from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


class _NoRedirect(urllib_request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _proxy_web_service(path: str):
    base_url = current_app.config.get('WEB_SERVICE_BASE_URL')
    if not base_url:
        return None

    opener = urllib_request.build_opener(_NoRedirect)
    upstream = f"{base_url.rstrip('/')}{path}"
    try:
        response = opener.open(upstream, timeout=5)
    except error.HTTPError as exc:
        response = exc

    body = response.read()
    proxied = Response(body, status=response.status)
    for header_name in ('Content-Type', 'Location', 'X-Magnifique-Web-Service'):
        header_value = response.headers.get(header_name)
        if header_value:
            proxied.headers[header_name] = header_value
    return proxied


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        proxied = _proxy_web_service('/auth/register')
        if proxied is not None:
            return proxied

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        nombre = request.form.get('nombre', '').strip()

        if not email or not password or not nombre:
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('auth/register.html')

        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'error')
            return render_template('auth/register.html')

        usuario = Usuario(email=email, nombre=nombre, rol='usuario')
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()

        login_user(usuario)
        return redirect(url_for('game.play'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        proxied = _proxy_web_service('/auth/login')
        if proxied is not None:
            return proxied

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_password(password):
            login_user(usuario)
            _set_session_duration(usuario)
            return redirect(url_for('game.play'))

        flash('Email o contraseña incorrectos.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


def _set_session_duration(usuario):
    """Ajusta duración de sesión según User-Agent (PC=30min, móvil=2h)."""
    ua = request.headers.get('User-Agent', '').lower()
    is_mobile = any(x in ua for x in ['mobile', 'android', 'iphone', 'tablet'])
    duration = 7200 if is_mobile else 1800
    # Flask-Login guarda sesión 30min por defecto; ajustar cookie duration
    from flask import current_app
    current_app.config['REMEMBER_COOKIE_DURATION'] = duration
