# Mini juego educativo sobre Management de un hotel

## Despliegue local

Clonar el repositorio que está en <https://github.com/Aoliken/magnifique>

Ir a la carpeta donde estan los archivos del proyecto:

Ejemplo

```shell
cd H:\\Meine Ablage\\Dokumente\\Academia\\Proyectos de Investigación\\Temas para próximos papers\\Mini juegos educativos sobre Management\\magnifique

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
