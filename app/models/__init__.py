"""
Hotel Magnifique — Models (package)
"""
from app.models.usuario import Usuario
from app.models.partida import Partida
from app.models.dia import Dia
from app.models.decision import Decision
from app.models.resultado import Resultado
from app.models.ajuste import Ajuste
from app.models.auth_session import AuthSession
from app.models.configuracion import Configuracion

__all__ = ['Usuario', 'Partida', 'Dia', 'Decision', 'Resultado', 'Ajuste', 'AuthSession', 'Configuracion']
