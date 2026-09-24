from flask_sqlalchemy import SQLAlchemy

# Inicializa la instancia de SQLAlchemy.
# Esta instancia 'db' será utilizada por todos tus modelos.
db = SQLAlchemy()

# Importa tus modelos aquí para que sean accesibles directamente
# desde el paquete 'model'.
# Esto es crucial para que SQLAlchemy los descubra y para evitar importaciones circulares.
from .professional import Profesional, Producto, Recetas, RecetaAsignada, ProductoAsignada
from .usuario import Usuario, Pacientes, Consulta, Progreso
from .personal import Empresa, Personal