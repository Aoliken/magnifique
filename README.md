## Hotel Magnifique
Bienvenido a Hotel Magnifique, un simulador de gestión hotelera diseñado para enseñar conceptos fundamentales de economía empresarial a través de la toma de decisiones cotidianas en un hotel de lujo. 

Objetivo del Juego: Administra el Hotel Magnifique durante 30 días consecutivos tomando decisiones diarias sobre precios, personal, marketing y servicios. Tu misión es maximizar las ganancias al tiempo que construyes la reputación del hotel hasta alcanzar las 5 estrellas. 

Este juego simula los desafíos reales de la gestión hotelera. A lo largo de los 30 días practicarás conceptos como: Yield Management, Costos Fijos vs Variables, Punto de Equilibrio y Gestión de Reputación.

Creado por Cristian von Matuschka (Aoliken) backend con colaboración de Sergio Alonso (pankutan).

## Despliegue local

### Prerrequisitos

Tener Docker con el complemento Docker Compose instalado y un archivo `.env` configurado en la raíz del proyecto. El archivo debe incluir la configuración de base de datos que utiliza Compose (`DB_NAME`, `DB_USER` y `DB_PASSWORD`).

Antes de ejecutar herramientas de Python, activar el entorno de Conda requerido:

```shell
conda activate py3.12
```

Clonar el repositorio que está en <https://github.com/Aoliken/magnifique>

Ir a la carpeta donde estan los archivos del proyecto:

Ejemplo

```shell
cd H:\\magnifique

conda activate py3.12
pip install -r requirements.txt
```

### Iniciar el stack

Desde la raíz del proyecto, iniciar el stack con la compuerta de migraciones:

```shell
conda activate py3.12
./scripts/start-stack.sh -d
```

El comando verifica que el servicio `flask-app` exista en la configuración de Compose, ejecuta `alembic upgrade head` en ese servicio y, solo si la migración finaliza correctamente, ejecuta `docker compose up -d`.

Si la migración falla, el comando termina con el mismo código de error y no inicia el stack de la aplicación. Corregir la migración o la configuración de la base de datos antes de volver a ejecutarlo.

Para iniciar en primer plano, omitir `-d`:

```shell
./scripts/start-stack.sh
```

### Detener el stack

```shell
docker compose down
```

## Antes de hacer `git push` del proyecto

```bash
engram sync
```
