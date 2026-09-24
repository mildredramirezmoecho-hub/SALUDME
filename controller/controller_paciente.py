import os
import uuid
# controller/controller_paciente.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify,current_app
from model.usuario import Pacientes, Consulta, Progreso, Usuario # Asegúrate de importar Usuario si lo necesitas para relaciones
from model.professional import Recetas, Producto, Profesional, RecetaAsignada, ProductoAsignada # Importa los modelos de asignación
from model import db
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload # Importar joinedload para cargar relaciones
from app import mail
from flask_mail import Message

# Crea un Blueprint para las rutas del paciente
paciente_bp = Blueprint('paciente', __name__)

@paciente_bp.before_request
def check_patient_login():
    """
    Este decorador se ejecuta antes de cada solicitud en este Blueprint.
    Verifica si el usuario ha iniciado sesión y tiene el rol de 'Paciente'.
    Si no cumple, redirige al usuario a la página de login.
    """
    if 'user_id' not in session or session.get('user_rol') != 'Paciente':
        flash('Acceso denegado. Por favor, inicia sesión como paciente.', 'danger')
        return redirect(url_for('auth.login'))

@paciente_bp.route('/dashboard_paciente')
def dashboard_paciente():
    """
    Muestra el dashboard principal del paciente.
    Recupera la información del paciente logueado y su profesional asociado.
    Esta es la ruta a la que apunta el "Inicio" y "Cuenta" en el navbar,
    así como el "SALUDME" brand.
    """
    user_id = session['user_id']
    # Busca el objeto Pacientes asociado al id_usuario de la sesión
    paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    profesional_del_paciente = None
    # Si el paciente existe y tiene un profesional asignado (id_profesional no es None)
    if paciente and paciente.id_profesional:
        # Accede al objeto Profesional a través de la relación definida en el modelo Pacientes
        profesional_del_paciente = paciente.profesional

    # Renderiza la plantilla 'usuario/menu.html' pasando los objetos paciente y profesional
    return render_template('paciente/menu.html', paciente=paciente, profesional_del_paciente=profesional_del_paciente)


@paciente_bp.route('/recetas_productos', methods=['GET'])
def recetas_productos():
    """
    Muestra las recetas y productos asignados al paciente,
    con opciones de filtrado, búsqueda y categoría.
    """
    user_id = session['user_id']
    paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    if not paciente:
        flash('Acceso denegado. Por favor, inicia sesión como paciente.', 'danger')
        return redirect(url_for('auth.login'))

    filter_by = request.args.get('filter', 'all')
    search_query = request.args.get('search_query', '').strip() # Corregido de 'query' a 'search_query'
    category_filter = request.args.get('category', '').strip() # Filtro por categoría de receta

    recetas_query = RecetaAsignada.query.filter_by(id_Pacientes=paciente.id_Pacientes).options(joinedload(RecetaAsignada.receta))
    productos_query = ProductoAsignada.query.filter_by(id_Pacientes=paciente.id_Pacientes).options(joinedload(ProductoAsignada.producto))

    items = []
    page_title = ''

    # === Filtros ===
    # Un ÚNICO join por consulta: si la búsqueda y la categoría se aplican a la
    # vez ya no se produce un join duplicado a la tabla 'recetas'.
    if search_query or category_filter:
        recetas_query = recetas_query.join(Recetas)
    if search_query:
        productos_query = productos_query.join(Producto)

    # Buscador por nombre de receta (y nombre/descripción de producto, como ya existía)
    if search_query:
        recetas_query = recetas_query.filter(Recetas.nombre.ilike(f'%{search_query}%'))
        productos_query = productos_query.filter(
            or_(Producto.nombre.ilike(f'%{search_query}%'),
                Producto.descripcion.ilike(f'%{search_query}%'))
        )

    # Filtro por categoría de receta
    if category_filter:
        recetas_query = recetas_query.filter(Recetas.categoria.ilike(f'%{category_filter}%'))

    if filter_by == 'recetas':
        items = [{'type': 'receta', 'data': ra.receta} for ra in recetas_query.all()]
        page_title = 'Mis Recetas Asignadas'
    elif filter_by == 'productos':
        # Se excluyen asignaciones cuyo producto es NULL (id_producto vacío):
        # así el contador coincide con las tarjetas realmente pintadas.
        items = [{'type': 'producto', 'data': pa.producto}
                 for pa in productos_query.all() if pa.producto is not None]
        page_title = 'Mis Productos Asignados'
    else: # 'all' or no filter
        for ra in recetas_query.all():
            items.append({'type': 'receta', 'data': ra.receta})
        for pa in productos_query.all():
            if pa.producto is None:  # asignación huérfana: no se muestra ni se cuenta
                continue
            items.append({'type': 'producto', 'data': pa.producto})
        page_title = 'Todas las Recetas y Productos'

    # Categorías reales entre las recetas asignadas al paciente (filtro dinámico)
    categorias = [
        c for (c,) in db.session.query(Recetas.categoria)
            .join(RecetaAsignada, RecetaAsignada.id_recetas == Recetas.id_recetas)
            .filter(RecetaAsignada.id_Pacientes == paciente.id_Pacientes,
                    Recetas.categoria.isnot(None),
                    Recetas.categoria != '')
            .distinct()
            .order_by(Recetas.categoria)
            .all()
    ]

    return render_template('paciente/recetas_productos.html',
                           paciente=paciente,
                           items=items,
                           filter_by=filter_by,
                           search_query=search_query,
                           category_filter=category_filter,
                           categorias=categorias,
                           page_title=page_title)

@paciente_bp.route('/ver_producto_detalle/<int:id>')
def ver_producto_detalle(id):
    """
    Muestra los detalles de un producto específico.
    """
    user_id = session['user_id']
    paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    if not paciente:
        flash('Acceso denegado. Por favor, inicia sesión como paciente.', 'danger')
        return redirect(url_for('auth.login'))

    producto = Producto.query.get_or_404(id)
    return render_template('paciente/producto_detalle.html', paciente=paciente, producto=producto )

@paciente_bp.route('/ver_receta_detalle/<int:id>')
def ver_receta_detalle(id):
    """
    Muestra los detalles de una receta específica.
    """
    user_id = session['user_id']
    paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    if not paciente:
        flash('Acceso denegado. Por favor, inicia sesión como paciente.', 'danger')
        return redirect(url_for('auth.login'))

    receta = Recetas.query.get_or_404(id)
    return render_template('paciente/receta_detalle.html', paciente=paciente, receta=receta)



@paciente_bp.route('/mis_consultas')
def mis_consultas():
    """
    Muestra el historial de consultas (citas) del paciente.
    Corresponde al enlace "Consulta" en el navbar.
    """
    user_id = session['user_id']
    paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    if not paciente:
        flash('No se encontró su perfil de paciente.', 'warning')
        return redirect(url_for('paciente.dashboard_paciente'))

    # Obtiene todas las consultas asociadas a este paciente, ordenadas por fecha descendente
    # Asegúrate de que la relación 'profesional' esté definida en tu modelo Consulta
    consultas = Consulta.query.filter_by(id_Pacientes=paciente.id_Pacientes).order_by(Consulta.fecha.desc()).all()

    # CAMBIO IMPORTANTE: Ahora renderiza la nueva plantilla de detalle de consultas
    return render_template('paciente/consultas.html', paciente=paciente, consultas=consultas)

@paciente_bp.route('/responder_consulta/<int:id>', methods=['POST'])
def responder_consulta(id):
    consulta = Consulta.query.get_or_404(id)
    accion = request.form.get('accion')

    if accion == 'aceptar':
        consulta.estado = 'Aceptada'
        flash('Cita aceptada con éxito.', 'success')
    elif accion == 'rechazar':
        consulta.estado = 'Rechazada'
        flash('Cita rechazada.', 'warning')
    else:
        flash('Acción no válida.', 'danger')

    db.session.commit()
    return redirect(url_for('paciente.mi_progreso', id_paciente=consulta.id_Pacientes))


@paciente_bp.route('/editar_datos/<int:id_paciente>', methods=['GET', 'POST'])
def editar_datos(id_paciente):
    user_id = session.get('user_id')
    current_paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    if not current_paciente or current_paciente.id_Pacientes != id_paciente:
        flash('Acceso denegado. No tienes permiso para editar este perfil.', 'danger')
        return redirect(url_for('paciente.dashboard_paciente'))

    paciente_a_editar = Pacientes.query.get_or_404(id_paciente)

    if request.method == 'POST':
        try:
            paciente_a_editar.nombres = request.form['nombres']
            paciente_a_editar.apellidos = request.form['apellidos']
            paciente_a_editar.cedula = request.form['cedula']
            paciente_a_editar.edad = int(request.form['edad'])
            paciente_a_editar.peso = float(request.form['peso'])
            paciente_a_editar.altura = float(request.form['altura'])
            paciente_a_editar.sexo = request.form['sexo']
            paciente_a_editar.objetivo = request.form['objetivo']
            paciente_a_editar.antecedente_alergia = request.form.get('antecedente_alergia', '')

            db.session.commit()
            flash('Perfil actualizado exitosamente.', 'success')
            return redirect(url_for('paciente.mi_progreso'))

        except ValueError:
            flash('Error en el formato de los datos (edad, peso, altura deben ser números).', 'danger')
            db.session.rollback()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el perfil: {e}', 'danger')

    return render_template('paciente/editar_perfil.html', paciente=paciente_a_editar)


@paciente_bp.route('/solicitar_cita', methods=['GET', 'POST'])
def solicitar_cita():
    """
    Permite al paciente solicitar una nueva cita, eligiendo un profesional.
    Corresponde al botón "Agendar" en la tarjeta de 'Agenda tus citas'.
    """
    user_id = session['user_id']
    paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    if not paciente:
        if request.method == 'POST':
            return jsonify({'message': 'No se encontró su perfil de paciente para solicitar una cita.'}), 400
        flash('No se encontró su perfil de paciente para solicitar una cita.', 'danger')
        return redirect(url_for('paciente.dashboard_paciente'))

    profesionales_disponibles = Profesional.query.all()

    if request.method == 'POST':
        fecha_str = request.form.get('fecha')
        hora_str = request.form.get('hora')
        id_profesional_seleccionado = request.form.get('id_profesional')

        if not all([fecha_str, hora_str, id_profesional_seleccionado]):
            return jsonify({'message': 'Por favor, complete todos los campos requeridos (fecha, hora y profesional).'}), 400

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora = datetime.strptime(hora_str, '%H:%M').time()
            id_profesional_para_cita = int(id_profesional_seleccionado)

            profesional_existe = Profesional.query.get(id_profesional_para_cita)
            if not profesional_existe:
                return jsonify({'message': 'El profesional seleccionado no es válido.'}), 400

            nueva_consulta = Consulta(
                id_Pacientes=paciente.id_Pacientes,
                id_profesional=id_profesional_para_cita,
                fecha=fecha,
                hora=hora,
                estado='Pendiente',
                solicitada_por='paciente'
            )

            db.session.add(nueva_consulta)
            
            paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

            paciente = Pacientes.query.filter_by(id_usuario=user_id).first()
            if paciente and paciente.id_profesional is None:
                paciente.id_profesional = id_profesional_para_cita
                db.session.commit()
                flash('Cita agendada correctamente', 'success')
                return redirect(url_for('paciente.ver_citas'))

            nombre_paciente = f"{paciente.nombres} {paciente.apellidos}"
            profesional_email = profesional_existe.usuario.email

            enviar_correo_notificacion_cita(
                profesional_email,
                nombre_paciente,
                fecha.strftime('%d/%m/%Y'),
                hora.strftime('%H:%M')
            )

            return jsonify({'message': 'Su solicitud de cita ha sido recibida con éxito y está pendiente de confirmación.'}), 200

        except ValueError:
            db.session.rollback()
            return jsonify({'message': 'Formato de fecha u hora incorrecto.'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'Error al agendar la cita: {str(e)}'}), 500

    return render_template('paciente/solicitar_cita.html', profesionales=profesionales_disponibles, paciente=paciente)


def enviar_correo_notificacion_cita(profesional_email, nombre_paciente, fecha, hora):
    try:
        msg = Message("Nueva solicitud de cita",
                      recipients=[profesional_email])
        msg.body = f"""
        Estimado Profesional,

        El paciente {nombre_paciente} ha solicitado una nueva cita.

        📅 Fecha: {fecha}
        🕒 Hora: {hora}

        Por favor, revise y confirme la cita en su panel.

        Gracias,
        Sistema SaludMe
        """
        mail.send(msg)
        print("Correo enviado al profesional")
    except Exception as e:
        print(f"Error al enviar correo: {e}")


@paciente_bp.route('/mi_progreso')
def mi_progreso():
    """
    Muestra el progreso del paciente.
    """
    user_id = session['user_id']
    paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    if not paciente:
        flash('No se encontró su perfil de paciente.', 'warning')
        return redirect(url_for('paciente.dashboard_paciente'))

    # Obtener todos los registros de progreso para el paciente, ordenados por fecha descendente
    progresos = Progreso.query.filter_by(id_paciente=paciente.id_Pacientes).order_by(Progreso.fecha.desc()).all()
    consultas = Consulta.query.filter_by(id_Pacientes=paciente.id_Pacientes).order_by(Consulta.fecha.desc()).all()

    return render_template('paciente/mi_progreso.html', paciente=paciente, progresos=progresos, consultas=consultas)


@paciente_bp.route('/editar_cita/<int:id>', methods=['POST'])
def editar_cita(id):
    consulta = Consulta.query.get_or_404(id)

    nueva_fecha = request.form.get('fecha')
    nueva_hora = request.form.get('hora')

    # Validar campos requeridos
    if not nueva_fecha or not nueva_hora:
        flash('Fecha y hora son requeridas.', 'danger')
        return redirect(url_for('paciente.mi_progreso', id_paciente=consulta.id_Pacientes))

    try:
        consulta.fecha = datetime.strptime(nueva_fecha, '%Y-%m-%d').date()
        consulta.hora = datetime.strptime(nueva_hora, '%H:%M').time()
        db.session.commit()
        flash('Consulta actualizada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar la consulta: {e}', 'danger')

    return redirect(url_for('paciente.mi_progreso', id_paciente=consulta.id_Pacientes))

@paciente_bp.route('/eliminar_consulta/<int:id>', methods=['GET', 'POST'])
def eliminar_cita(id):
    consulta = Consulta.query.get_or_404(id)
    db.session.delete(consulta)
    db.session.commit()
    flash('Cita eliminada con éxito', 'success')
    return redirect(url_for('paciente.mi_progreso', id_paciente=consulta.id_Pacientes))

@paciente_bp.route('/guardar_foto', methods=['POST'])
def guardar_foto():
    """
    Maneja la subida de la foto de perfil para el paciente logueado.
    """
    user_id = session.get('user_id')
    current_paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    if not current_paciente:
        flash('Acceso denegado. Por favor, inicia sesión como paciente.', 'danger')
        return redirect(url_for('auth.login'))

    if 'foto' not in request.files:
        flash('No se seleccionó ningún archivo de foto.', 'danger')
        return redirect(request.referrer or url_for('paciente.mi_progreso'))

    file = request.files['foto']


    if file:
        try:
            filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
            upload_folder = os.path.join(os.getcwd(), 'static', 'uploads', 'fotos_perfil')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            current_paciente.foto_perfil = os.path.join('uploads', 'fotos_perfil', filename).replace('\\', '/')
            db.session.commit()

            flash('Foto de perfil actualizada exitosamente.', 'success')
            return redirect(url_for('paciente.mi_progreso'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar la foto: {e}', 'danger')
            return redirect(request.referrer or url_for('paciente.mi_progreso'))

    flash('Error al procesar la subida de la foto.', 'danger')
    return redirect(request.referrer or url_for('paciente.mi_progreso'))


@paciente_bp.route('/eliminar_mi_progreso/<int:progreso_id>', methods=['POST'])
def eliminar_mi_progreso(progreso_id):
    """
    Permite a un paciente eliminar uno de sus propios registros de progreso.
    """
    user_id = session['user_id']
    current_paciente = Pacientes.query.filter_by(id_usuario=user_id).first()

    if not current_paciente:
        flash('No se encontró su perfil de paciente.', 'danger')
        return redirect(url_for('paciente.dashboard_paciente'))

    progreso_a_eliminar = Progreso.query.get_or_404(progreso_id)

    # **CRÍTICO: Asegurarse de que el registro de progreso pertenece al paciente logueado**
    if progreso_a_eliminar.id_paciente != current_paciente.id_Pacientes:
        flash('No tienes permiso para eliminar este registro de progreso.', 'danger')
        return redirect(url_for('paciente.mi_progreso')) # O a su dashboard, dependiendo de la navegación

    try:
        db.session.delete(progreso_a_eliminar)
        db.session.commit()
        flash('Registro de progreso eliminado con éxito.', 'success')
        return redirect(url_for('paciente.mi_progreso')) # Redirige al historial de progreso del paciente
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el registro de progreso: {e}', 'danger')
        return redirect(url_for('paciente.mi_progreso'))
