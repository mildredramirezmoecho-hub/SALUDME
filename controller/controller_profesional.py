# controller/controller_profesional.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from model.usuario import Usuario, Pacientes, Progreso, Consulta
from model.professional import Profesional, Producto, Recetas, RecetaAsignada, ProductoAsignada
from model import db
from datetime import date, datetime, timedelta, time
from sqlalchemy import desc
from sqlalchemy.orm import joinedload # Importar joinedload para cargar relaciones
from app import mail
from flask_mail import Message


# Crear el blueprint para las rutas relacionadas con el profesional
profesional_bp = Blueprint('profesional', __name__)

# Configuración para la carga de archivos de profesionales
UPLOAD_FOLDER_PROFESSIONALS = 'static/img/professionals'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profesional_bp.before_request
def check_professional_login():
    """
    Este decorador se ejecuta antes de cada solicitud en este Blueprint.
    Verifica si el usuario ha iniciado sesión y tiene el rol de 'Profesional'.
    Si no cumple, redirige al usuario a la página de login.
    """
    if 'user_id' not in session or session.get('user_rol') != 'Profesional':
        flash('Acceso denegado. Por favor, inicia sesión como profesional.', 'danger')
        return redirect(url_for('auth.login'))

@profesional_bp.route('/dashboard_profesional')
def dashboard_profesional():
    """
    Muestra el dashboard principal del profesional, incluyendo las últimas consultas.
    """
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Perfil de profesional no encontrado.', 'danger')
        return redirect(url_for('auth.login'))

    # Obtener las últimas 5 consultas del profesional, ordenadas por fecha y hora descendente
    # Usamos joinedload para cargar también la información del paciente para evitar N+1 queries
    ultimas_consultas = Consulta.query.options(joinedload(Consulta.paciente)).filter_by(
        id_profesional=profesional_logueado.id_profesional
    ).order_by(
        desc(Consulta.fecha),
        desc(Consulta.hora)
    ).limit(5).all()

    return render_template('profesional/inicio_p.html', ultimas_consultas=ultimas_consultas)

@profesional_bp.route('/cuenta')
def cuenta():
    """
    Muestra el perfil personal del profesional logueado.
    Esta es la ruta a la que debe apuntar el enlace "Mi Cuenta" o "Mi Perfil" del profesional.
    """
    user_id = session['user_id']
    # Carga el profesional y asegura cargar la relación con Usuario
    profesional = Profesional.query.options(joinedload(Profesional.usuario)).filter_by(id_usuario=user_id).first()

    if not profesional:
        flash('Perfil de profesional no encontrado.', 'danger')
        return redirect(url_for('auth.login')) # Redirige al login si no se encuentra el perfil

    return render_template('profesional/cuentapro.html', profesional=profesional)

@profesional_bp.route('/editar_perfil_profesional/<int:id_profesional>', methods=['GET', 'POST'])
def editar_perfil_profesional(id_profesional):
    """
    Permite al profesional editar sus propios datos de perfil.
    """
    user_id = session['user_id']
    profesional = Profesional.query.filter_by(id_profesional=id_profesional, id_usuario=user_id).first()

    if not profesional:
        flash('Perfil de profesional no encontrado o no autorizado para editar.', 'danger')
        return redirect(url_for('profesional.cuenta'))

    if request.method == 'POST':
        profesional.nombre = request.form.get('nombre')
        profesional.apellido_P = request.form.get('apellido_P')
        profesional.apellido_M = request.form.get('apellido_M')
        profesional.especialidad = request.form.get('especialidad')
        profesional.cedula = request.form.get('cedula') # <--- Cédula del profesional
        profesional.telefono = request.form.get('telefono')
        profesional.experiencia = int(request.form.get('experiencia'))
        profesional.descripcion = request.form.get('descripcion')

        # Manejo de la subida de archivos para la foto de perfil
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Asegúrate de que la carpeta de subida exista
                os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER_PROFESSIONALS), exist_ok=True)
                file.save(os.path.join(current_app.root_path, UPLOAD_FOLDER_PROFESSIONALS, filename))
                profesional.foto = f'img/professionals/{filename}' # Guarda la ruta relativa para la DB
            elif file.filename != '': # Si se envió un archivo pero no es permitido
                flash('Tipo de archivo no permitido para la foto de perfil.', 'danger')
                return redirect(url_for('profesional.editar_perfil_profesional', id_profesional=id_profesional))
        # Si no se envió un nuevo archivo, la foto existente en profesional.foto se mantiene

        try:
            db.session.commit()
            flash('Perfil actualizado con éxito.', 'success')
            return redirect(url_for('profesional.cuenta'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el perfil: {e}', 'danger')
            return redirect(url_for('profesional.editar_perfil_profesional', id_profesional=id_profesional))

    return render_template('profesional/editar_perfil_profesional.html', profesional=profesional)


@profesional_bp.route('/ver_paciente/<int:id_paciente>')
def ver_paciente(id_paciente):
    """
    Muestra los detalles de un paciente específico, incluyendo su progreso, citas, recetas y productos asignados.
    """
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Acceso denegado. Por favor, inicia sesión como profesional.', 'danger')
        return redirect(url_for('auth.login'))

    paciente = Pacientes.query.options(joinedload(Pacientes.usuario)).get_or_404(id_paciente)
    # Nueva verificación de relación entre paciente y profesional a través de Consulta
    consulta_existente = Consulta.query.filter_by(
        id_Pacientes=id_paciente,
        id_profesional=profesional_logueado.id_profesional).first()
    
    if not consulta_existente:
        flash('No tienes permiso para ver los detalles de este paciente.', 'danger')
        return redirect(url_for('profesional.gestion_pacientes'))

    # Historial de progresos
    progresos = Progreso.query.filter_by(id_paciente=id_paciente).order_by(desc(Progreso.fecha)).all()

    # CONSULTAS: solo las que estén relacionadas con ese paciente Y ese profesional
    consultas = Consulta.query.filter_by(
        id_Pacientes=id_paciente,
        id_profesional=profesional_logueado.id_profesional
    ).order_by(desc(Consulta.fecha)).all()

    # Recetas y productos asignados
    recetas_asignadas = RecetaAsignada.query.options(joinedload(RecetaAsignada.receta))\
        .filter_by(id_Pacientes=id_paciente).order_by(desc(RecetaAsignada.fecha_asignacion)).all()

    productos_asignados = ProductoAsignada.query.options(joinedload(ProductoAsignada.producto))\
        .filter_by(id_Pacientes=id_paciente).order_by(desc(ProductoAsignada.fecha_asignacion)).all()

    today_date = date.today().isoformat()
    recetas_disponibles = Recetas.query.all()
    productos_disponibles = Producto.query.all()

    return render_template('profesional/paciente.html', 
                           paciente=paciente, 
                           progresos=progresos,
                           consultas=consultas, 
                           recetas_asignadas=recetas_asignadas,
                           productos_asignados=productos_asignados,
                           today_date=today_date,
                           recetas_disponibles=recetas_disponibles,
                           productos_disponibles=productos_disponibles)


# Asegúrate de tener el método correcto
@profesional_bp.route('/eliminar_progreso/<int:id>', methods=['GET'])
def eliminar_progreso(id):
    progreso = Progreso.query.get_or_404(id)
    db.session.delete(progreso)
    db.session.commit()
    flash('Registro de progreso eliminado exitosamente.', 'success')
    return redirect(request.referrer or url_for('profesional.ver_paciente', id_paciente=progreso.id_paciente))

@profesional_bp.route('/citas_agendadas_paciente/<int:paciente_id>')
def citas_agendadas_paciente(paciente_id):
    """
    Muestra todas las citas del paciente (ya sea creadas por el profesional o el paciente).
    """
    user_id = session.get('user_id')
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Acceso denegado. Por favor, inicia sesión como profesional.', 'danger')
        return redirect(url_for('auth.login'))

    # Verificar que el paciente existe y pertenece al profesional
    paciente = Pacientes.query.get_or_404(paciente_id)
    if paciente.id_profesional != profesional_logueado.id_profesional:
        flash('No tienes permiso para ver las citas de este paciente.', 'danger')
        return redirect(url_for('profesional.gestion_pacientes'))

    # Obtener todas las citas del paciente
    consultas = Consulta.query.filter_by(id_Pacientes=paciente_id).order_by(desc(Consulta.fecha)).all()

    return render_template('profesional/paciente.html', consultas=consultas, paciente=paciente)

@profesional_bp.route('/responder_consulta/<int:id>', methods=['POST'])
def responder_consulta(id):
    if 'user_id' not in session:
        flash("Debes iniciar sesión.", "danger")
        return redirect(url_for('auth.login'))

    consulta = Consulta.query.get_or_404(id)
    accion = request.form.get('accion')

    if accion == 'aceptar':
        consulta.estado = 'Confirmada'
        flash("Consulta confirmada.", "success")
    elif accion == 'rechazar':
        consulta.estado = 'Rechazada'
        flash("Consulta rechazada.", "warning")
    else:
        flash("Acción inválida.", "danger")

    db.session.commit()
    return redirect(url_for('profesional.ver_paciente', id_paciente=consulta.id_Pacientes))  # O donde quieras regresar



# Asegúrate de tener el método correcto
@profesional_bp.route('/eliminar_consulta/<int:id>', methods=['GET', 'POST'])
def eliminar_consulta(id):
    consulta = Consulta.query.get_or_404(id)
    db.session.delete(consulta)
    db.session.commit()
    flash('Cita eliminada con éxito', 'success')
    return redirect(url_for('profesional.ver_paciente', id_paciente=consulta.id_Pacientes))


@profesional_bp.route('/editar_consulta/<int:id>', methods=['POST'])
def editar_consulta(id):
    consulta = Consulta.query.get_or_404(id)
    nueva_fecha = request.form.get('fecha')
    nueva_hora = request.form.get('hora')

    # Validar la nueva fecha y hora
    if not nueva_fecha or not nueva_hora:
        flash('Fecha y hora son requeridas.', 'danger')
        return redirect(url_for('profesional.ver_paciente', id_paciente=consulta.id_Pacientes))

    try:
        consulta.fecha = datetime.strptime(nueva_fecha, '%Y-%m-%d').date()
        consulta.hora = datetime.strptime(nueva_hora, '%H:%M').time()
        db.session.commit()
        flash('Consulta actualizada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar la consulta: {e}', 'danger')

    return redirect(url_for('profesional.ver_paciente', id_paciente=consulta.id_Pacientes))

@profesional_bp.route('/editar_receta_asignada/<int:id>', methods=['POST'])
def editar_receta_asignada(id):
    asignacion = RecetaAsignada.query.get_or_404(id)
    nueva_receta = request.form.get('id_receta')
    nueva_fecha = request.form.get('fecha_asignacion')

    try:
        if nueva_receta:
            asignacion.id_recetas = int(nueva_receta)
        if nueva_fecha:
            asignacion.fecha_asignacion = datetime.strptime(nueva_fecha, '%Y-%m-%d')
        db.session.commit()
        flash('Receta asignada actualizada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar la receta asignada: {e}', 'danger')

    return redirect(url_for('profesional.ver_paciente', id_paciente=asignacion.id_Pacientes))



@profesional_bp.route('/eliminar_receta_asignada/<int:id>')
def eliminar_receta_asignada(id):
    asignacion = RecetaAsignada.query.get_or_404(id)
    id_paciente = asignacion.id_Pacientes
    db.session.delete(asignacion)
    db.session.commit()
    flash('Receta eliminada correctamente.', 'success')
    return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente))


@profesional_bp.route('/api/obtener_receta/<int:id>', methods=['GET'])
def api_obtener_receta(id):
    receta = Recetas.query.get(id)
    if not receta:
        return jsonify({'error': 'Receta no encontrada'}), 404
    return jsonify({'id_recetas': receta.id_recetas, 'nombre': receta.nombre, 'descripcion': receta.descripcion, 'ingredientes': receta.ingredientes, 'instrucciones': receta.instrucciones, 'categoria': receta.categoria, 'foto': receta.foto})

# --- Gestión de Recetas (catálogo) — Iteración 2 ---
# El profesional puede crear, editar y eliminar recetas del catálogo.
# (El módulo de administración / Personal no se modifica.)
UPLOAD_FOLDER_RECIPES = 'static/img/recipes'


def _contar_ingredientes(ingredientes):
    """
    Cuenta los ingredientes de una receta a partir del texto separado por comas.
    Misma lógica que utiliza el módulo de Personal.
    """
    if not ingredientes:
        return 0
    return len([i for i in ingredientes.replace('\n', ',').split(',') if i.strip()])


@profesional_bp.route('/recetas')
def gestion_recetas():
    """
    Muestra el listado de todas las recetas del catálogo
    (visualización + opciones de crear/editar/eliminar).
    """
    recetas = Recetas.query.order_by(Recetas.nombre).all()
    return render_template('profesional/recetas.html', recetas=recetas)


@profesional_bp.route('/recetas/nueva', methods=['POST'])
def agregar_receta():
    """
    Crea una nueva receta registrando nombre, descripción,
    ingredientes, categoría y preparación.
    """
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    ingredientes = request.form.get('ingredientes')
    categoria = request.form.get('categoria')
    instrucciones = request.form.get('instrucciones')  # Preparación

    foto_filename = 'img/recipes/default_recipe.png'

    # Manejo de la subida de la foto
    if 'foto' in request.files:
        file = request.files['foto']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER_RECIPES), exist_ok=True)
            file.save(os.path.join(current_app.root_path, UPLOAD_FOLDER_RECIPES, filename))
            foto_filename = f'img/recipes/{filename}'
        elif file.filename != '':
            flash('Tipo de archivo no permitido para la foto de la receta.', 'danger')
            return redirect(url_for('profesional.gestion_recetas'))

    if not all([nombre, descripcion, ingredientes, categoria]):
        flash('Nombre, descripción, ingredientes y categoría son obligatorios.', 'danger')
        return redirect(url_for('profesional.gestion_recetas'))

    nueva_receta = Recetas(
        nombre=nombre,
        descripcion=descripcion,
        ingredientes=ingredientes,
        categoria=categoria,
        instrucciones=instrucciones,          # Preparación
        cant_ingredientes=_contar_ingredientes(ingredientes),
        foto=foto_filename
    )
    try:
        db.session.add(nueva_receta)
        db.session.commit()
        flash('Receta creada con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la receta: {e}', 'danger')
    return redirect(url_for('profesional.gestion_recetas'))


@profesional_bp.route('/recetas/editar/<int:id>', methods=['POST'])
def editar_receta(id):
    """
    Edita una receta existente (nombre, descripción, ingredientes,
    categoría y preparación).
    """
    receta = Recetas.query.get_or_404(id)

    receta.nombre = request.form.get('nombre')
    receta.descripcion = request.form.get('descripcion')
    receta.ingredientes = request.form.get('ingredientes')
    receta.categoria = request.form.get('categoria')
    receta.instrucciones = request.form.get('instrucciones')  # Preparación
    receta.cant_ingredientes = _contar_ingredientes(receta.ingredientes)

    # Foto: solo se reemplaza si se sube una nueva
    if 'foto' in request.files:
        file = request.files['foto']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER_RECIPES), exist_ok=True)
            file.save(os.path.join(current_app.root_path, UPLOAD_FOLDER_RECIPES, filename))
            receta.foto = f'img/recipes/{filename}'
        elif file.filename != '':
            flash('Tipo de archivo no permitido para la foto de la receta.', 'danger')
            return redirect(url_for('profesional.gestion_recetas'))

    try:
        db.session.commit()
        flash('Receta actualizada con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar la receta: {e}', 'danger')
    return redirect(url_for('profesional.gestion_recetas'))


@profesional_bp.route('/recetas/eliminar/<int:id>', methods=['POST'])
def eliminar_receta(id):
    """
    Elimina una receta. Si está asignada a pacientes, sus asignaciones
    se eliminan primero en la misma transacción para no violar la
    clave foránea receta_asignada.id_recetas (y así evitar recetas
    huérfanas en la vista del paciente).
    """
    receta = Recetas.query.get_or_404(id)
    try:
        RecetaAsignada.query.filter_by(id_recetas=receta.id_recetas)\
                            .delete(synchronize_session=False)

        if receta.foto and receta.foto != 'img/recipes/default_recipe.png':
            file_path = os.path.join(current_app.root_path, 'static', receta.foto.replace('img/', ''))
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(receta)
        db.session.commit()
        flash('Receta eliminada con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la receta: {e}', 'danger')
    return redirect(url_for('profesional.gestion_recetas'))


@profesional_bp.route('/asignar_receta/<int:id_paciente>', methods=['GET', 'POST'])
def asignar_receta(id_paciente):
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.login'))

    paciente = Pacientes.query.get_or_404(id_paciente)
    recetas_disponibles = Recetas.query.all()

    if request.method == 'POST':
        id_receta = request.form.get('id_receta')
        if not id_receta:
            flash('Debes seleccionar una receta.', 'danger')
            return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente)) # Redirige a la misma página del paciente
        
        nueva_asignacion = RecetaAsignada(
            id_Pacientes=paciente.id_Pacientes,
            id_recetas=id_receta, 
            id_profesional=profesional_logueado.id_profesional,
            fecha_asignacion=datetime.utcnow().date()
        )
        try:
            db.session.add(nueva_asignacion)
            db.session.commit()
            flash('Receta asignada con éxito al paciente.', 'success')
            return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al asignar receta: {e}', 'danger')
            return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente)) # Redirige a la misma página del paciente

    return render_template('profesional/paciente.html', paciente=paciente, recetas_disponibles=recetas_disponibles)

@profesional_bp.route('/editar_producto_asignado/<int:id>', methods=['POST'])
def editar_producto_asignado(id):
    asignacion = ProductoAsignada.query.get_or_404(id)
    nueva_producto = request.form.get('id_producto')
    nueva_fecha = request.form.get('fecha_asignacion')

    asignacion.id_Producto = nueva_producto
    asignacion.fecha_asignacion = nueva_fecha

    db.session.commit()
    flash('Producto asignado actualizado correctamente.', 'success')
    return redirect(url_for('profesional.ver_paciente', id_paciente=asignacion.id_Pacientes))



@profesional_bp.route('/eliminar_producto_asignado/<int:id>')
def eliminar_producto_asignado(id):
    asignacion = ProductoAsignada.query.get_or_404(id)
    id_paciente = asignacion.id_Pacientes
    db.session.delete(asignacion)
    db.session.commit()
    flash('Producto eliminado correctamente.', 'success')
    return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente))


@profesional_bp.route('/api/obtener_producto/<int:id>', methods=['GET'])
def api_obtener_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    return jsonify({'id_producto': producto.id_producto, 'nombre': producto.nombre, 'descripcion': producto.descripcion, 'precio': float(producto.precio), 'foto': producto.foto})
@profesional_bp.route('/asignar_producto/<int:id_paciente>', methods=['GET', 'POST'])
def asignar_producto(id_paciente):
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.login'))

    paciente = Pacientes.query.get_or_404(id_paciente)
    productos_disponibles = Producto.query.all()

    if request.method == 'POST':
        id_producto = request.form.get('id_producto')
        if not id_producto:
            flash('Debes seleccionar un producto.', 'danger')
            return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente)) # Redirige a la misma página del paciente
        
        
        nueva_asignacion = ProductoAsignada(
            id_Pacientes=paciente.id_Pacientes,
            id_producto=id_producto,
            id_profesional=profesional_logueado.id_profesional, 
            fecha_asignacion=datetime.utcnow().date()
        )
        try:
            db.session.add(nueva_asignacion)
            db.session.commit()
            flash('Producto asignado con éxito al paciente.', 'success')
            return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al asignar producto: {e}', 'danger')
            return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente)) # Redirige a la misma página del paciente

    return render_template('profesional/asignar_producto.html', paciente=paciente, productos_disponibles=productos_disponibles)

# --- Rutas de Pacientes (Asignación de Recetas/Productos) ---
@profesional_bp.route('/gestion_pacientes')
def gestion_pacientes():
    """
    Muestra la lista de pacientes que han agendado citas con este profesional.
    """
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Perfil de profesional no encontrado.', 'danger')
        return redirect(url_for('auth.login'))

    # Buscar pacientes que han agendado una cita con este profesional
    subquery_ids = db.session.query(Consulta.id_Pacientes).filter(
        Consulta.id_profesional == profesional_logueado.id_profesional
    ).distinct()

    pacientes = Pacientes.query.filter(Pacientes.id_Pacientes.in_(subquery_ids)).all()

    return render_template('profesional/gestion_pacientes.html', pacientes=pacientes)


@profesional_bp.route('/editar_paciente', methods=['POST'])
def editar_paciente():
    """
    Permite al profesional editar los datos de un paciente existente.
    """
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Acceso denegado. Por favor, inicia sesión como profesional.', 'danger')
        return redirect(url_for('auth.login'))

    id_paciente = request.form.get('id_paciente')
    paciente = Pacientes.query.options(joinedload(Pacientes.usuario)).get_or_404(id_paciente)

    # Verificar que el profesional logueado es el dueño del paciente
    tiene_cita = Consulta.query.filter_by(
        id_Pacientes=id_paciente,
        id_profesional=profesional_logueado.id_profesional
        ).first()
    if not tiene_cita:
        flash('No tienes permiso para ver los detalles de este paciente.', 'danger')
        return redirect(url_for('profesional.gestion_pacientes'))

    # Actualizar datos del paciente
    paciente.nombres = request.form.get('nombres')
    paciente.apellidos = request.form.get('apellidos')
    
    new_cedula = request.form.get('cedula')
    if new_cedula and new_cedula != paciente.cedula:
        # Verificar si la nueva cédula ya está en uso por otro paciente
        if Pacientes.query.filter(Pacientes.cedula == new_cedula, Pacientes.id_Pacientes != paciente.id_Pacientes).first():
            flash('La nueva cédula ya está en uso por otro paciente.', 'danger')
            return redirect(url_for('profesional.gestion_pacientes')) # O a la página de edición del paciente
        paciente.cedula = new_cedula # <--- Actualizar la cédula
    
    paciente.edad = int(request.form.get('edad'))
    paciente.nivel_actividad = request.form.get('nivel_actividad')
    paciente.objetivo = request.form.get('objetivo')
    
    # Asegúrate de que estos campos se conviertan a float si son números
    try:
        paciente.peso = float(request.form.get('peso'))
    except (ValueError, TypeError):
        paciente.peso = None # O maneja el error como prefieras
    
    try:
        paciente.altura = float(request.form.get('altura'))
    except (ValueError, TypeError):
        paciente.altura = None # O maneja el error como prefieras

    paciente.sexo = request.form.get('sexo')
    paciente.antecedente_alergia = request.form.get('antecedente_alergia')


    # Actualizar email del usuario asociado si se proporciona
    new_email = request.form.get('email')
    if paciente.usuario and new_email and new_email != paciente.usuario.email:
        # Verificar si el nuevo email ya está en uso por otro usuario (que no sea el actual paciente)
        if Usuario.query.filter(Usuario.email == new_email, Usuario.id_usuario != paciente.usuario.id_usuario).first():
            flash('El nuevo email ya está en uso por otro usuario.', 'danger')
            return redirect(url_for('profesional.gestion_pacientes')) # O a la página de edición del paciente
        paciente.usuario.email = new_email
    elif not paciente.usuario and new_email:
        # Si el paciente no tiene usuario asociado pero se proporciona un email, crear uno (caso poco probable)
        # Esto podría ser una lógica más compleja de manejar, aquí se asume que siempre hay un usuario.
        pass # Manejar este caso según la lógica de tu aplicación

    # Actualizar teléfono del usuario asociado si se proporciona
    new_telefono = request.form.get('telefono')
    if paciente.usuario:
        paciente.usuario.telefono = new_telefono # <--- Actualizar el teléfono del usuario asociado

    try:
        db.session.commit()
        flash('Datos del paciente actualizados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar paciente: {e}', 'danger')
    
    return redirect(url_for('profesional.gestion_pacientes'))


@profesional_bp.route('/eliminar_paciente/<int:id>', methods=['POST'])
def eliminar_paciente(id):
    """
    Permite al profesional eliminar un paciente.
    """
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Acceso denegado. Por favor, inicia sesión como profesional.', 'danger')
        return redirect(url_for('auth.login'))

    paciente = Pacientes.query.get_or_404(id)

    # Verificar que el profesional logueado es el dueño del paciente
    if paciente.id_profesional != profesional_logueado.id_profesional:
        flash('No tienes permiso para eliminar este paciente.', 'danger')
        return redirect(url_for('profesional.gestion_pacientes'))

    try:
        # Opcional: Eliminar el usuario asociado si no se usa en otro lugar
        if paciente.id_usuario:
            usuario_asociado = Usuario.query.get(paciente.id_usuario)
            if usuario_asociado:
                db.session.delete(usuario_asociado)
        
        db.session.delete(paciente)
        db.session.commit()
        flash('Paciente eliminado con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar paciente: {e}', 'danger')
    return redirect(url_for('profesional.gestion_pacientes'))


@profesional_bp.route('/api/obtener_datos_paciente/<int:id>', methods=['GET'])
def api_obtener_datos_paciente(id):
    """
    API para obtener los datos de un paciente en formato JSON para el modal de edición.
    """
    print(f"DEBUG: Solicitud para obtener datos del paciente con ID: {id}")
    paciente = Pacientes.query.options(joinedload(Pacientes.usuario)).get(id)
    
    if not paciente:
        print(f"DEBUG: Paciente con ID {id} NO encontrado.")
        return jsonify({'error': 'Paciente no encontrado'}), 404
    
    print(f"DEBUG: Paciente encontrado: {paciente.nombres} {paciente.apellidos}")

    # Asegúrate de incluir todos los campos que necesitas en el modal de edición
    # Incluyendo los que estaban comentados en gestion_paciente.html por si acaso.
    return jsonify({
        'id_Pacientes': paciente.id_Pacientes,
        'nombres': paciente.nombres,
        'apellidos': paciente.apellidos,
        'edad': paciente.edad,
        'email': paciente.usuario.email if paciente.usuario else '', # Accede al email del usuario
        'nivel_actividad': paciente.nivel_actividad,
        'objetivo': paciente.objetivo,
        'cedula': paciente.cedula, # <--- Incluir la cédula
        'telefono': paciente.usuario.telefono if paciente.usuario else '', # <--- Incluir el teléfono del usuario
        'sexo': paciente.sexo, # <--- Incluir el sexo
        'peso': paciente.peso,
        'altura': paciente.altura,
        'alergias': paciente.antecedente_alergia, 
    })


@profesional_bp.route('/agenda')
def agenda():
    """
    Muestra la agenda de citas del profesional.
    """
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Perfil de profesional no encontrado.', 'danger')
        return redirect(url_for('auth.login'))

    # Obtener todas las citas del profesional
    citas = Consulta.query.filter_by(id_profesional=profesional_logueado.id_profesional).all()

    # Pasar las citas a la plantilla
    return render_template('profesional/agenda.html', citas=citas)


@profesional_bp.route('/api/citas_profesional', methods=['GET'])
def api_citas_profesional():
    """
    API para obtener las citas de un profesional en formato JSON.
    """
    user_id = session['user_id']
    profesional = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional:
        return jsonify({'error': 'Profesional no encontrado'}), 404

    # Obtener las fechas de inicio y fin de la semana desde los parámetros de la URL
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    citas_query = Consulta.query.filter_by(id_profesional=profesional.id_profesional)
    citas_query = citas_query.filter(Consulta.id_Pacientes.isnot(None))
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            citas_query = citas_query.filter(Consulta.fecha >= start_date, Consulta.fecha <= end_date)
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use AAAA-MM-DD.'}), 400

    citas = citas_query.all()
    
    citas_data = []
    for cita in citas:
        paciente_nombre = f"{cita.paciente.nombres} {cita.paciente.apellidos}" if cita.paciente else "Paciente Desconocido"
        citas_data.append({
            'id': cita.id_consulta,
            'fecha': cita.fecha.strftime('%Y-%m-%d'),
            'hora': cita.hora.strftime('%H:%M'),
            'estado': cita.estado,
            'paciente_id': cita.id_Pacientes,
            'paciente_nombre': paciente_nombre,
            'solicitada_por': cita.solicitada_por,  # Añadido para mostrar quién solicitó la cita
            
        })
    return jsonify(citas_data)

@profesional_bp.route('/api/buscar_paciente_por_cedula/<string:cedula>', methods=['GET'])
def api_buscar_paciente_por_cedula(cedula):
    """
    API para buscar un paciente por cédula y devolver sus nombres y apellidos.
    Esta ruta es utilizada por el JavaScript en agenda.html para autocompletar el nombre del paciente.
    """
    paciente = Pacientes.query.filter_by(cedula=cedula).first()
    if paciente:
        return jsonify({'nombres': paciente.nombres, 'apellidos': paciente.apellidos, 'id_Pacientes': paciente.id_Pacientes}) # <--- Añadido id_Pacientes
    return jsonify({'error': 'Paciente no encontrado'}), 404


@profesional_bp.route('/agendar_consulta', methods=['POST'])
def agendar_consulta():
    """
    Permite al profesional agendar una nueva consulta.
    Utiliza la cédula del paciente para identificarlo.
    """
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Acceso denegado. Por favor, inicia sesión como profesional.', 'danger')
        return redirect(url_for('auth.login'))

    paciente_cedula = request.form.get('patient_identifier')  # Usar 'patient_identifier' del formulario de agenda.html
    fecha_consulta_str = request.form.get('appointment_date')
    hora_consulta_str = request.form.get('appointment_time')
    appointment_type = request.form.get('appointment_type')

    if not all([paciente_cedula, fecha_consulta_str, hora_consulta_str, appointment_type]):
        flash('Todos los campos de la cita son obligatorios.', 'danger')
        return redirect(url_for('profesional.agenda'))

    # Buscar al paciente por cédula
    paciente = Pacientes.query.filter_by(cedula=paciente_cedula).first()
    if not paciente:
        flash('Paciente no encontrado con la cédula proporcionada.', 'danger')
        return redirect(url_for('profesional.agenda'))

    # Asociar profesional al paciente si aún no tiene uno asignado
    if not paciente.id_profesional:
        paciente.id_profesional = profesional_logueado.id_profesional

    try:
        fecha_consulta = datetime.strptime(fecha_consulta_str, '%Y-%m-%d').date()
        hora_consulta = datetime.strptime(hora_consulta_str, '%H:%M').time()
    except ValueError:
        flash('Formato de fecha u hora inválido.', 'danger')
        return redirect(url_for('profesional.agenda'))

    nueva_consulta = Consulta(
        id_Pacientes=paciente.id_Pacientes,
        id_profesional=profesional_logueado.id_profesional,
        fecha=fecha_consulta,
        hora=hora_consulta,
        solicitada_por='profesional',
        estado=appointment_type
    )

    try:
        db.session.add(nueva_consulta)
        db.session.commit()
        flash('Cita agendada correctamente.', 'success')

        nombre_profesional = f"{profesional_logueado.nombre} {profesional_logueado.apellido_P}"
        paciente_email = f"{paciente.usuario.email}"

        enviar_correo_notificacion_cita(
            paciente_email,
            nombre_profesional,
            fecha_consulta.strftime('%d/%m/%Y'),
            hora_consulta.strftime('%H:%M')
        )

    except Exception as e:
        db.session.rollback()
        flash(f'Error al agendar la cita: {e}', 'danger')

    return redirect(url_for('profesional.agenda'))


def enviar_correo_notificacion_cita(paciente_email, nombre_profesional, fecha_consulta, hora_consulta):
    try:
        msg = Message("Nueva solicitud de cita",
                      recipients=[paciente_email])
        msg.body = f"""
        Estimado Paciente,

        El Nutricionista {nombre_profesional} ha solicitado una nueva cita.

        📅 Fecha: {fecha_consulta}
        🕒 Hora: {hora_consulta}

        Por favor, revise y confirme la cita en su panel.

        Gracias,
        Sistema SaludMe
        """
        mail.send(msg)
        print("Correo enviado al Paciente")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

@profesional_bp.route('/api/eliminar_cita/<int:id>', methods=['DELETE'])
def eliminar_cita(id):
    cita = Consulta.query.get(id)
    if not cita:
        return jsonify({'error': 'Cita no encontrada'}), 404
    try:
        db.session.delete(cita)
        db.session.commit()
        return jsonify({'message': 'Cita eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@profesional_bp.route('/guardar_progreso/<int:id_paciente>', methods=['GET', 'POST'])
def guardar_progreso(id_paciente):
    user_id = session['user_id']
    profesional_logueado = Profesional.query.filter_by(id_usuario=user_id).first()

    if not profesional_logueado:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.login'))

    paciente = Pacientes.query.get_or_404(id_paciente)

    if paciente.id_profesional != profesional_logueado.id_profesional:
        flash('No tienes permiso para registrar el progreso de este paciente.', 'danger')
        return redirect(url_for('profesional.gestion_pacientes'))

    if request.method == 'POST':
        peso_actual_str = request.form.get('peso_actual')
        altura_str = request.form.get('altura_en_metros_float')
        circunferencia_cintura_str = request.form.get('circunferencia_cintura')
        comentarios = request.form.get('comentarios', '').strip()
        recomendaciones = request.form.get('recomendaciones', '').strip()

        if not all([peso_actual_str, altura_str, comentarios, recomendaciones]):
            flash('Peso, altura, comentarios y recomendaciones son obligatorios.', 'danger')
            return redirect(url_for('profesional.guardar_progreso', id_paciente=id_paciente))

        try:
            peso_actual_float = float(peso_actual_str)
            altura_en_metros_float = float(altura_str)
            circunferencia_cintura_float = float(circunferencia_cintura_str) if circunferencia_cintura_str else None

            if peso_actual_float <= 0 or altura_en_metros_float <= 0:
                flash('El peso y la altura deben ser mayores a cero.', 'danger')
                return redirect(url_for('profesional.guardar_progreso', id_paciente=id_paciente))

            imc = peso_actual_float / (altura_en_metros_float ** 2)

            # Verificar duplicado diario (opcional)
            existe_progreso = Progreso.query.filter_by(
                id_paciente=paciente.id_Pacientes,
                fecha=datetime.utcnow().date()
            ).first()
            if existe_progreso:
                flash('Ya se ha registrado el progreso para el día de hoy.', 'warning')
                return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente))

            nuevo_progreso = Progreso(
                id_paciente=paciente.id_Pacientes,
                fecha=datetime.utcnow().date(),
                peso_actual=peso_actual_float,
                circunferencia_cintura=circunferencia_cintura_float,
                imc=imc,
                comentarios=comentarios,
                recomendaciones=recomendaciones
            )

            db.session.add(nuevo_progreso)
            db.session.commit()

            flash(f"Progreso guardado correctamente. IMC: {imc:.2f}", "success")
            return redirect(url_for('profesional.ver_paciente', id_paciente=id_paciente))

        except ValueError:
            db.session.rollback()
            flash('Los valores numéricos son inválidos.', 'danger')
            return redirect(url_for('profesional.guardar_progreso', id_paciente=id_paciente))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar el progreso: {e}', 'danger')
            print(f"DEBUG: Error al guardar el progreso: {e}")
            return redirect(url_for('profesional.guardar_progreso', id_paciente=id_paciente))

    progresos = Progreso.query.filter_by(id_paciente=id_paciente).order_by(Progreso.fecha.desc()).all()
    return render_template('profesional/paciente.html', paciente=paciente, progresos=progresos)
