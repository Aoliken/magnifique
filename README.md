## Hotel Magnifique
Bienvenido a Hotel Magnifique, un simulador de gestión hotelera diseñado para enseñar conceptos fundamentales de economía empresarial a través de la toma de decisiones cotidianas en un hotel de lujo. 

Objetivo del Juego: Administra el Hotel Magnifique durante 30 días consecutivos tomando decisiones diarias sobre precios, personal, marketing y servicios. Tu misión es maximizar las ganancias al tiempo que construyes la reputación del hotel hasta alcanzar las 5 estrellas. 

Este juego simula los desafíos reales de la gestión hotelera. A lo largo de los 30 días practicarás conceptos como: Yield Management, Costos Fijos vs Variables, Punto de Equilibrio y Gestión de Reputación.

Creado por Cristian von Matuschka (Aoliken) backend con colaboración de Sergio Alonso (pankutan).

## Despliegue local

Clonar el repositorio que está en <https://github.com/Aoliken/magnifique>

Ir a la carpeta donde estan los archivos del proyecto:

Ejemplo

```shell
cd H:\\magnifique

conda activate py3.12
pip install -r requirements.txt
```

Poner los valores en .env

Correr las migraciones

```bash
alembic upgrade head
```

## Correr el proyecto

```shell
conda activate py3.12
flask --app app run --debug
```

## Antes de hacer `git push` del proyecto

```bash
engram sync
```
