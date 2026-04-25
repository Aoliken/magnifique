# PRD: Hotel Magnifique - Sistema de Gestión Dinámica

## 1. Visión General
Transformar el simulador estático "Hotel Magnifique" en una aplicación web robusta donde la lógica de negocio, los cálculos de ocupación y la persistencia de datos ocurran en el backend.

## 2. Stack Tecnológico
- **Lenguaje:** Python 3.12
- **Entorno:** Miniconda
- **Framework Backend:** Flask
- **Base de Datos:** PostgreSQL
- **Frontend:** HTML/JS existente migrado a plantillas de Flask con Bootstrap para el diseño responsivo.

## 3. Roles y Permisos
- **Usuario (Jugador):** - Registrarse e iniciar sesión. La sesion debe durar 30 minutos maximo. En celulares puede durar 2 horas, trata de detectar por user agent si el cliente es un celular o una pc.
    - Iniciar nuevas partidas de 30 días.
    - Tomar decisiones diarias (precios, personal, servicios).
    - Ver historial de sus propias partidas.
- **Administrador:**
    - Acceso a panel de control.
    - Visualización de métricas globales de usuarios.
    - Capacidad para ajustar parámetros base de la simulación (inflación, demanda base).

## 4. Lógica de Simulación (Backend-Only)
El cliente (Frontend) enviará las decisiones del día al servidor. El servidor procesará:
- **Cálculo de Ocupación:** Basado en precio, reputación y eventos aleatorios.
- **Gestión de Finanzas:** Deducción de costos fijos, salarios y costos de marketing.
- **Evolución de Reputación:** Basada en la calidad del servicio vs. ocupación.
- **Fin del Juego:** Validación del día 30 y cálculo del grado final (A-F).

## 5. Requisitos de Datos
- **Persistencia:** Todos los estados intermedios del día deben guardarse en PostgreSQL para permitir reanudar la partida.
- **Seguridad:** Las credenciales de DB se manejarán mediante variables de entorno en un archivo .env