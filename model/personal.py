# model/personal.py
from model import db
from model.professional import Profesional # Importa Profesional para la relación en Empresa, usando una lambda para resolución diferida

class Empresa(db.Model):
    __tablename__ = 'empresa'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(10))
    email = db.Column(db.String(100))

    # Al eliminar una Empresa, también se eliminarán los Profesionales y Usuarios asociados.
    profesionales = db.relationship(lambda: Profesional, backref='empresa', lazy=True, cascade="all, delete-orphan")
    usuarios = db.relationship('Usuario', backref='empresa', lazy=True, cascade="all, delete-orphan")


class Personal(db.Model):
    __tablename__ = 'personal'

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    contraseña = db.Column(db.String(120), nullable=False)
    # Si 'Personal' fuera un tipo de 'Usuario' con id_usuario FK, también necesitaría cascada.



