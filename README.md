# Mini juego educativo sobre Management de un hotel

## Despliegue local

Ir a la carpeta donde estan los archivos del proyecto:

```powershell
cd H:\\Meine Ablage\\Dokumente\\Academia\\Proyectos de Investigación\\Temas para próximos papers\\Mini juegos educativos sobre Management\\magnifique

conda activate py3.12
pip install -r requirements.txt
```

Poner los valores en .env

Correr las migraciones

```bash
alembic upgrade head
```

## Antes de hacer `git push` del proyecto

```bash
engram sync
python -m scripts.generate_docs
```
