# Agentes del Sistema - Backend Hotel Magnifique

Para mantener un código limpio y modular, el backend se divide en los siguientes "agentes" lógicos:

### 1. Agente de Autenticación (Auth Agent)
- **Responsabilidad:** Gestionar el registro, login y sesiones de usuarios.
- **Tecnología:** Flask-Login o JWT.
- **Funciones:** Validar contraseñas (hashing), verificar roles (Admin vs Usuario).

### 2. Agente de Simulación (Simulation Engine)
- **Responsabilidad:** Es el núcleo del juego. Contiene las fórmulas matemáticas.
- **Funciones:** - `calculate_daily_results()`: Recibe las variables del usuario y devuelve el balance de caja, ocupación y reputación.
    - `random_event_generator()`: Determina si ocurre un evento especial en el día actual.

### 3. Agente de Persistencia (Data Agent)
- **Responsabilidad:** Comunicación con PostgreSQL.
- **Tecnología:** SQLAlchemy (ORM).
- **Funciones:** Guardar el estado del día, recuperar la partida activa y almacenar resultados históricos.

### 4. Agente de Interfaz (Template Agent)
- **Responsabilidad:** Servir el frontend dinamizado.
- **Funciones:** Inyectar los datos del backend en las plantillas de Bootstrap para que el usuario vea su progreso en tiempo real.

---

## Modelo de Datos

```mermaid
erDiagram
    USUARIO ||--o{ PARTIDA : crea
    PARTIDA ||--o{ DIA : tiene
    PARTIDA ||--|{ AJUSTE : recibe
    DIA ||--|{ DECISION : contiene
    DIA ||--|{ RESULTADO : genera
    
    USUARIO {
        uuid id PK
        string email UK
        string password_hash
        string nombre
        string rol "usuario|admin"
        timestamp created_at
        timestamp last_login
    }
    
    PARTIDA {
        uuid id PK
        uuid usuario_id FK
        integer dia_actual "1-31"
        decimal capital
        decimal reputacion "1-10"
        decimal ganancia_total
        decimal ingreso_total
        decimal gasto_total
        boolean activa
        timestamp started_at
        timestamp updated_at
        string grado_final "A|B|C|D|F|S|&#128184;"
    }
    
    DIA {
        uuid id PK
        uuid partida_id FK
        integer numero "1-31"
        string temporada "Primavera|Verano|Otoño|Invierno"
        string evento "Normal|Congreso|Feria|..."
        decimal factor_temporada
        decimal factor_evento
        timestamp created_at
        timestamp updated_at
    }
    
    DECISION {
        uuid id PK
        uuid dia_id FK
        integer precio
        integer personal
        integer marketing
        boolean desayuno
        boolean piscina
        boolean spa
    }
    
    RESULTADO {
        uuid id PK
        uuid dia_id FK
        integer habitaciones_ocupadas
        decimal ocupacion_pct
        decimal ingreso
        decimal gasto
        decimal balance
        decimal reputacion
        decimal reputacion_cambio
        decimal demanda_base
        decimal precio_optimo
    }
    
    AJUSTE {
        uuid id PK
        uuid partida_id FK
        string parametro
        decimal valor_base
        decimal valor_actual
        string motivo "inflacion|evento|manual"
        timestamp applied_at
    }
```