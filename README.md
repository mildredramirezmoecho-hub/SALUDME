# SALUDME

SALUDME (espacio para consulta y control de alimentos, dieta y salud)

Aplicación web Flask + MySQL con tres tipos de usuario:

- **Pacientes**: consultan recetas y productos asignados, su progreso y agenda de citas.
- **Profesionales**: gestionan pacientes, consultas, agenda y el catálogo de recetas (CRUD).
- **Personal (administración)**: gestiona usuarios, profesionales, pacientes y productos.

## Requisitos

- Python 3.13 (probado con 3.13; debe funcionar también en 3.11+)
- MySQL/MariaDB con un esquema llamado `SaludMe`
- Las dependencias están en `requirements.txt`

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/mildredramirezmoecho-hub/SALUDME.git
cd SALUDME

# 2. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno (credenciales: NUNCA se suben a Git)
copy .env.example .env        # Windows
# cp .env.example .env        # Linux/Mac
# Edita .env y pon tu DATABASE_URL, SECRET_KEY y credenciales SMTP

# 5. Importar la base de datos (esquema + datos)
#    Desde MySQL Workbench, phpMyAdmin o la consola:
mysql -u TU_USUARIO -p SaludMe < BASEDEDATOS/saludme_usuario.sql
#    (o importa los .sql de BASEDEDATOS/ en el orden que necesites;
#     migracion_recetas_instrucciones.sql solo se usa si la app no puede
#     crear la columna 'instrucciones' automáticamente)

# 6. Ejecutar
python app.py
# La app queda en http://127.0.0.1:5000
```

## Variables de entorno

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URI de SQLAlchemy, p. ej. `mysql+mysqlconnector://user:pass@localhost:3307/SaludMe` |
| `SECRET_KEY` | Clave secreta de Flask para sesiones (genera una con `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `MAIL_SERVER` / `MAIL_PORT` / `MAIL_USE_TLS` | Servidor SMTP (por defecto Brevo) |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | Credenciales SMTP |
| `MAIL_DEFAULT_SENDER_EMAIL` | Remitente por defecto de los correos |

Si falta alguna variable obligatoria, la aplicación muestra un error claro indicando qué falta.

## Estructura

```
SALUDABLE/
├── app.py                 # Punto de entrada: create_app() + migración ligera
├── appconfig.py           # Configuración (lee .env)
├── generar_hashes.py      # Utilidad: genera hashes de contraseñas por CLI
├── requirements.txt
├── .env.example           # Plantilla de variables de entorno
├── BASEDEDATOS/           # Volcados SQL del esquema SaludMe
├── controller/            # Blueprints: auth, paciente, profesional, personal
├── model/                 # Modelos SQLAlchemy (db, usuarios, recetas, ...)
├── templates/             # Plantillas Jinja2 por rol (paciente/, profesional/, personal/)
└── static/                # CSS, imágenes y assets
```

## Notas

- La columna `recetas.instrucciones` (preparación) se crea automáticamente al arrancar; si no es posible, la app indica el script de respaldo `BASEDEDATOS/migracion_recetas_instrucciones.sql`.
- `.env` está en `.gitignore`: las credenciales de BD y SMTP no se versionan.
