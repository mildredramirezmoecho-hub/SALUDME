# app.py
import os

from flask import Flask
from model import db
from appconfig import config, requerida
from flask_mail import Mail


mail=Mail()

def _asegurar_columna_instrucciones(app):
    """
    Migración ligera: si la tabla 'recetas' no tiene la columna 'instrucciones'
    (preparación de la receta), la crea. Si no es posible, muestra un mensaje
    claro indicando el script SQL de respaldo.
    """
    from sqlalchemy import text

    with app.app_context():
        try:
            existe = db.session.execute(text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME = 'recetas' "
                "AND COLUMN_NAME = 'instrucciones'"
            )).scalar()

            if not existe:
                db.session.execute(text(
                    "ALTER TABLE recetas ADD COLUMN instrucciones TEXT NULL AFTER ingredientes"
                ))
                db.session.commit()
                app.logger.info("Columna 'instrucciones' añadida a la tabla 'recetas'.")
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(
                "No se pudo crear la columna 'instrucciones' en la tabla 'recetas'. "
                "Ejecuta manualmente el script: BASEDEDATOS/migracion_recetas_instrucciones.sql "
                f"(Error original: {e})"
            )

def create_app():

    app = Flask(__name__)

    # Carga la configuración de la aplicación desde el objeto config
    # (incluye SECRET_KEY, que se lee de las variables de entorno en .env)
    app.config.from_object(config)

    # Configuración de correo SMTP: también desde .env (nunca en el código)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp-relay.brevo.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = requerida('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = requerida('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = ('SaludMe App', requerida('MAIL_DEFAULT_SENDER_EMAIL'))


    # Inicializa la extensión SQLAlchemy con la aplicación Flask.
    db.init_app(app)
    mail.init_app(app)

    # Asegura que la tabla 'recetas' tenga la columna 'instrucciones' (preparación).
    _asegurar_columna_instrucciones(app)

    # Importa los blueprints DENTRO de la función create_app para evitar importaciones circulares.
    from controller.controller_usuario import auth_bp
    from controller.controller_profesional import profesional_bp
    from controller.controller_paciente import paciente_bp
    from controller.controller_personal import personal_bp

    # Registra el blueprint de autenticación sin prefijo de URL.
    app.register_blueprint(auth_bp)

    # Registra el blueprint del profesional con el prefijo '/profesional'.
    app.register_blueprint(profesional_bp, url_prefix='/profesional')

    app.register_blueprint(paciente_bp, url_prefix='/paciente')

    app.register_blueprint(personal_bp, url_prefix='/personal')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)