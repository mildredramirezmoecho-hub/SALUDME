# model/usuario.py
from werkzeug.security import generate_password_hash, check_password_hash
from model import db

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contraseña_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(15), nullable=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=True)

    # Relación: Un Usuario tiene un Paciente asociado (uno a uno)
    # Al eliminar un Usuario, también se eliminará el Paciente asociado.
    paciente_asociado = db.relationship('Pacientes', backref='usuario', uselist=False, lazy=True, cascade="all, delete-orphan")
    profesional = db.relationship(
    'Profesional',
    back_populates='usuario',
    cascade='all, delete-orphan',
    uselist=False
)

    # La relación con Profesional se define en professional.py con un backref a Usuario,
    # por lo que la cascada para Profesional se manejará desde allí.


class Pacientes(db.Model):
    __tablename__ = 'pacientes'
    id_Pacientes = db.Column(db.Integer, primary_key=True)
    # Si un Paciente no puede existir sin un Usuario, la cascada se define en Usuario.
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), unique=True, nullable=False)
    id_profesional = db.Column(db.Integer, db.ForeignKey('profesional.id_profesional'), nullable=False)

    nombres = db.Column(db.String(50), nullable=False)
    apellidos = db.Column(db.String(50), nullable=False)
    cedula = db.Column(db.String(10), nullable=False, unique=True)
    sexo = db.Column(db.String(10))
    peso = db.Column(db.Numeric(5, 2))
    altura = db.Column(db.Numeric(4, 2))
    edad = db.Column(db.Integer)
    objetivo = db.Column(db.Text)
    antecedente_alergia = db.Column(db.String(100))
    nivel_actividad = db.Column(db.String(50))
    foto= db.Column(db.String(200), nullable=True)

    profesional = db.relationship('Profesional', backref='pacientes_asignados', lazy=True)

    # Al eliminar un Paciente, también se eliminarán sus Consultas, Progresos,
    # Asignaciones de Productos y Asignaciones de Recetas.
    consultas = db.relationship('Consulta', backref='paciente', lazy=True, cascade="all, delete-orphan")
    progresos = db.relationship('Progreso', backref='paciente', lazy=True, cascade="all, delete-orphan")
    productos_asignados = db.relationship('ProductoAsignada', backref='pacientes', lazy=True, cascade="all, delete-orphan")
    recetas_asignadas = db.relationship('RecetaAsignada', backref='pacientes', lazy=True, cascade="all, delete-orphan")


class Consulta(db.Model):
    __tablename__ = 'consulta'
    id_consulta = db.Column(db.Integer, primary_key=True)
    id_Pacientes = db.Column(db.Integer, db.ForeignKey('pacientes.id_Pacientes'), nullable=False)
    id_profesional = db.Column(db.Integer, db.ForeignKey('profesional.id_profesional'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    estado = db.Column(db.String(50), default='Pendiente' ) 
    # --- ADD THIS NEW LINE ---
    solicitada_por = db.Column(db.String(20), nullable=False) # Example: 'paciente' or 'profesional'



class Progreso(db.Model):
    __tablename__ = 'progreso'
    id = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_Pacientes'), nullable=False)

    fecha = db.Column(db.Date, nullable=False)
    peso_actual = db.Column(db.Numeric(5, 2), nullable=False)
    circunferencia_cintura = db.Column(db.Numeric(5, 2), nullable=True)
    imc = db.Column(db.Numeric(5, 2), nullable=True)
    comentarios = db.Column(db.Text, nullable=True)
    recomendaciones = db.Column(db.Text, nullable=True)
