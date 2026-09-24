# controller/controller_usuario.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from model.usuario import Usuario, Pacientes
from model import db
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

# NUEVA RUTA: Interfaz pública (página de inicio)
@auth_bp.route('/informacion', methods=['GET']) # Cambia el nombre de la ruta para ser más descriptivo
@auth_bp.route('/') # Hace que esta sea la ruta por defecto (la página de inicio)
def informacion_publica():
    """
    Muestra la página de información pública (Informacion1.html)
    accesible sin necesidad de autenticación.
    """
    return render_template('usuario/Informacion1.html') # Asegúrate de que Informacion1.html esté en tu carpeta 'templates'

# Ruta principal para el login (ya existente)
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        rol = request.form.get('rol_seleccionado')

        if not email or not password or not rol:
            flash('Por favor, ingresa todos los campos requeridos.', 'danger')
            return render_template('login/login.html')

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.contraseña_hash, password):
            if usuario.rol == rol:
                session['user_id'] = usuario.id_usuario
                session['user_email'] = usuario.email
                session['user_rol'] = usuario.rol

                flash(f'¡Bienvenido, {usuario.email}!', 'success')

                if usuario.rol == 'Profesional':
                    return redirect(url_for('profesional.dashboard_profesional'))
                elif usuario.rol == 'Paciente':
                    return redirect(url_for('paciente.dashboard_paciente'))
                elif usuario.rol == 'Personal':
                    return redirect(url_for('personal.dashboard_personal'))
            else:
                flash('Rol incorrecto para este usuario.', 'danger')
        else:
            flash('Email o contraseña incorrectos.', 'danger')
    return render_template('login/login.html')

# Ruta para el registro de Pacientes
@auth_bp.route('/registro_paciente', methods=['GET', 'POST'])
def registro_paciente():
    # Ya no obtenemos la lista de profesionales aquí para pasarla al formulario.
    # profesionales = Profesional.query.all() # Eliminado

    if request.method == 'POST': 
        # Datos del formulario de Usuario
        email = request.form.get('email')
        password = request.form.get('password')
        telefono_usuario = request.form.get('telefono_usuario')
        id_empresa = request.form.get('id_empresa')

        # Datos del formulario de Paciente
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        cedula = request.form.get('cedula')
        sexo = request.form.get('sexo')
        peso = request.form.get('peso')
        altura = request.form.get('altura')
        edad = request.form.get('edad')
        objetivo = request.form.get('objetivo')
        antecedente_alergia = request.form.get('antecedente_alergia')
        nivel_actividad = request.form.get('nivel_actividad')

        # Asignar un profesional por defecto (por ejemplo, el profesional con ID 1)
        # Esto es temporal para satisfacer la FK NOT NULL si el paciente no lo elige al registrarse.
        # En el futuro, podrías hacer id_profesional NULLABLE o tener una lógica de asignación más compleja.
        id_profesional_defecto = 1 # Asegúrate de que este ID exista en tu tabla 'profesional'

        # Validaciones básicas
        # id_profesional_seleccionado ya no es parte de la validación 'all'
        if Pacientes.query.filter_by(cedula=cedula).first():
            flash('La cédula ingresada ya está registrada. Por favor, verifica.', 'danger')
            return redirect(url_for('auth.registro_paciente'))

        if not all([email, password, nombres, apellidos, cedula]):
            flash('Por favor, completa todos los campos obligatorios.', 'danger')
            return render_template('login/registro_paciente.html') # Ya no pasamos 'profesionales'

        # Verificar si el email ya existe
        if Usuario.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado.', 'danger')
            return render_template('login/registro_paciente.html') # Ya no pasamos 'profesionales'

        try:
            # 1. Crear el Usuario
            hashed_password = generate_password_hash(password)
            nuevo_usuario = Usuario(
                email=email,
                contraseña_hash=hashed_password,
                rol='Paciente',
                telefono=telefono_usuario,
                id_empresa=id_empresa if id_empresa else None
            )
            db.session.add(nuevo_usuario)
            db.session.flush()

            # 2. Crear el Paciente
            nuevo_paciente = Pacientes(
                id_usuario=nuevo_usuario.id_usuario,
                id_profesional=id_profesional_defecto, # Asigna el profesional por defecto
                nombres=nombres,
                apellidos=apellidos,
                cedula=cedula,
                sexo=sexo,
                peso=float(peso) if peso else None,
                altura=float(altura) if altura else None,
                edad=int(edad) if edad else None,
                objetivo=objetivo,
                antecedente_alergia=antecedente_alergia,
                nivel_actividad=nivel_actividad,
            )
            db.session.add(nuevo_paciente)
            db.session.commit()

            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error durante el registro: {e}', 'danger')
            print(f"DEBUG: Error en registro de paciente: {e}")
            return render_template('login/registro_paciente.html') # Ya no pasamos 'profesionales'

    return render_template('login/registro_paciente.html') # Ya no pasamos 'profesionales' en el GET

# Rutas de dashboard genéricas para roles que aún no tienen su propio blueprint
@auth_bp.route('/dashboard_paciente')
def dashboard_paciente():
    if 'user_id' not in session or session.get('user_rol') != 'Paciente':
        flash('Acceso denegado. Por favor, inicia sesión como paciente.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    profesional_del_paciente = None
    if paciente and paciente.id_profesional:
        profesional_del_paciente = paciente.profesional

    return render_template('paciente/menu.html', paciente=paciente, profesional_del_paciente=profesional_del_paciente)

@auth_bp.route('/dashboard_personal')
def dashboard_personal():
    if 'user_id' not in session or session.get('user_rol') != 'Personal':
        flash('Acceso denegado. Por favor, inicia sesión como personal.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('personal/dashboard_personal.html')

@auth_bp.route('/recuperar_contraseña')
def recuperar_contraseña():
    return "Página de recuperación de contraseña"

@auth_bp.route('/registro')
def registro():
    return redirect(url_for('auth.registro_paciente'))

@auth_bp.route('/logout', methods=['POST']) # <--- ¡Asegúrate de que methods=['POST'] esté aquí!
def logout():
    # Eliminar el ID de usuario de la sesión, si existe
    session.pop('user_id', None)
    session.pop('user_rol', None) # También elimina el rol si lo guardas
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login')) # Redirigir a la página de login