# model/professional.py

from datetime import datetime
from model import db
from werkzeug.security import generate_password_hash, check_password_hash

class Profesional(db.Model):
    __tablename__ = 'profesional'

    id_profesional = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario', ondelete='CASCADE'), nullable=False, unique=True)



    nombre = db.Column(db.String(50), nullable=False)
    nombre_segundo = db.Column(db.String(50), nullable=False)
    apellido_P = db.Column(db.String(50), nullable=False)
    apellido_M = db.Column(db.String(50), nullable=False)

    cedula = db.Column(db.String(10), nullable=False, unique=True)
    telefono = db.Column(db.String(10), nullable=False)
    especialidad = db.Column(db.String(100))
    experiencia = db.Column(db.Integer)
    descripcion = db.Column(db.Text)
    foto = db.Column(db.String(200), nullable=True)

    
    usuario = db.relationship(
    'Usuario',
    back_populates='profesional')
    consultas = db.relationship('Consulta', backref='profesional', lazy=True, cascade="all, delete-orphan")
    recetas_asignadas = db.relationship('RecetaAsignada', backref='profesional', lazy=True, cascade="all, delete-orphan")
    productos_asignados = db.relationship('ProductoAsignada', backref='profesional', lazy=True, cascade="all, delete-orphan")


class Producto(db.Model):
    __tablename__ = 'producto'

    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text)
    foto = db.Column(db.String(255))     # Si un Producto no puede existir sin sus asignaciones, podrías añadir cascade aquí,
    # pero usualmente los productos existen independientemente de las asignaciones.
    # Si eliminas un Producto, las ProductoAsignada que lo referencian pueden dar error
    # a menos que manejes la eliminación de esas asignaciones primero, o uses ondelete="SET NULL"
    # en la FK de ProductoAsignada si id_producto puede ser nulo.
    # Por ahora, asumimos que los productos se eliminan solo si no están asignados.


class Recetas(db.Model):
    __tablename__ = 'recetas'

    id_recetas = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cant_ingredientes = db.Column(db.Integer)
    ingredientes = db.Column(db.Text)
    instrucciones = db.Column(db.Text)  # Preparación: pasos de la receta (se crea con la migración en app.py)
    descripcion = db.Column(db.Text)
    foto = db.Column(db.String(255)) 
    categoria = db.Column(db.String(50))  # Por ejemplo, "Desayuno", "Almuerzo", etc.
    # Similar a Producto, si una Receta no puede existir sin sus asignaciones,
    # podrías añadir cascade aquí. Por ahora, asumimos que las recetas se eliminan
    # solo si no están asignadas.


class RecetaAsignada(db.Model):
    __tablename__ = 'receta_asignada'

    id_asignar_r = db.Column(db.Integer, primary_key=True)
    id_recetas = db.Column(db.Integer, db.ForeignKey('recetas.id_recetas'), nullable=False)
    id_Pacientes = db.Column(db.Integer, db.ForeignKey('pacientes.id_Pacientes'), nullable=False)
    id_profesional = db.Column(db.Integer, db.ForeignKey('profesional.id_profesional'), nullable=False)
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)

    receta = db.relationship('Recetas', backref='asignaciones', lazy=True)


class ProductoAsignada(db.Model):
    __tablename__ = 'producto_asignada'

    id_asignar_p = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    id_Pacientes = db.Column(db.Integer, db.ForeignKey('pacientes.id_Pacientes'), nullable=False)
    id_profesional = db.Column(db.Integer, db.ForeignKey('profesional.id_profesional'), nullable=False)
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)

    producto = db.relationship('Producto', backref='asignaciones', lazy=True)
