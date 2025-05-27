# Betawave Music Player

## Requisitos Previos
- Python 3.13
- pip (gestión de paquetes)

## Instalación

1. Clonar el repositorio:
```powershell
git clone https://github.com/DanielJimenezZapata/TFG_DAM.git
cd betawave
```


2. Instalar dependencias:
```powershell
pip install -r requirements.txt
```

## Ejecutar la Aplicación

1. Activar el entorno virtual (si no está activado):
```powershell
.\venv\Scripts\activate
```

2. Iniciar la aplicación:
```powershell
python app.py
```

La aplicación estará disponible en `http://localhost:8501`

## Ejecutar Tests

1. Ejecutar todos los tests:
```powershell
python -m pytest tests/test_app.py -v
```

2. Ejecutar tests con detalles y prints:
```powershell
python -m pytest tests/test_app.py -v -s
```

3. Ejecutar un test específico:
```powershell
python -m pytest tests/test_app.py::test_admin_functions -v
```

### Opciones de Tests
- `-v`: modo con más detalles (verboso)
- `-s`: muestra prints durante la ejecución 
- `-k "nombre"`: ejecuta tests que coincidan con el nombre
- `--pdb`: modo debug si un test falla
- `-x`: detiene la ejecución en el primer fallo

## Base de Datos

La aplicación usa SQLite3 como base de datos. La base de datos se inicializa automáticamente al ejecutar la aplicación por primera vez.

Para reiniciar la base de datos:
1. Detener la aplicación
2. Eliminar el archivo `music.db` (Borra TODO lo añadido anteriormente)
3. Reiniciar la aplicación

## Desarrollo

Para el desarrollo, se recomienda:
1. Activar el entorno virtual
2. Ejecutar la aplicación:
```powershell
python app.py
```
