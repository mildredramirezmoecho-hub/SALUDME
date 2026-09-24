"""
Genera hashes de contraseñas (werkzeug) listos para usar en un INSERT de SQL.

Las contraseñas NO se escriben en este fichero: se pasan por línea de comandos.

Uso:
    python generar_hashes.py <contraseña> [<contraseña> ...]

Ejemplo:
    python generar_hashes.py mipassword123
"""
import sys

from werkzeug.security import generate_password_hash


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    for clave in sys.argv[1:]:
        print(f"'{generate_password_hash(clave)}'")


if __name__ == "__main__":
    main()
