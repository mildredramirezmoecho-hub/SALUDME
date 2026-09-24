import os

from dotenv import load_dotenv

# Carga las variables de entorno del fichero .env (local, no versionado).
# Si no existe .env, copia .env.example a .env y rellena tus valores.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def requerida(nombre: str) -> str:
    """Devuelve una variable de entorno obligatoria o lanza un error claro."""
    valor = os.environ.get(nombre, "").strip()
    if not valor:
        raise RuntimeError(
            f"Falta la variable de entorno '{nombre}'. "
            "Copia '.env.example' a '.env' y rellena tus credenciales."
        )
    return valor


class config:
    SQLALCHEMY_DATABASE_URI = requerida("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = requerida("SECRET_KEY")
