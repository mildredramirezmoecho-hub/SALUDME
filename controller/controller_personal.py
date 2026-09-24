# controller/controller_personal.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename # Importar secure_filename
from model.professional import Profesional
from model.usuario import Usuario# Importa el modelo Usuario
from model.professional import Recetas, Producto # Importa Recetas y Producto
from model import db # Importa la instancia de la base de datos
from app import mail
from flask_mail import Message


# Crea un Blueprint para las rutas del personal
personal_bp = Blueprint('personal', __name__)

# Configuración para la carga de archivos
# Asegúrate de que esta ruta sea accesible y exista en tu proyecto
UPLOAD_FOLDER_RECIPES = 'static/img/recipes'
UPLOAD_FOLDER_PRODUCTS = 'static/img/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """
    Verifica si la extensión del archivo está permitida.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _contar_ingredientes(ingredientes):
    """
    Cuenta los ingredientes de una receta a partir del texto separado por comas.
    """
    if not ingredientes:
        return 0
    return len([i for i in ingredientes.replace('\n', ',').split(',') if i.strip()])

@personal_bp.before_request
def check_personal_login():
    """
    Este decorador se ejecuta antes de cada solicitud en este Blueprint.
    Verifica si el usuario ha iniciado sesión y tiene el rol de 'Personal'.
    Si no cumple, redirige al usuario a la página de login.
    """
    if 'user_id' not in session or session.get('user_rol') != 'Personal':
        flash('Acceso denegado. Por favor, inicia sesión como personal.', 'danger')
        return redirect(url_for('auth.login'))

@personal_bp.route('/dashboard_personal')
def dashboard_personal():
    """
    Muestra el dashboard principal del personal.
    """
    return render_template('personal/dashboard_personal.html')

# --- Gestión de Recetas ---
@personal_bp.route('/gestion_recetas')
def gestion_recetas():
    """
    Muestra la lista de todas las recetas.
    """
    recetas = Recetas.query.all()
    return render_template('personal/gestion_recetas.html', recetas=recetas)

@personal_bp.route('/agregar_receta', methods=['POST'])
def agregar_receta():
    """
    Añade una nueva receta.
    """
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    ingredientes = request.form.get('ingredientes')
    categoria = request.form.get('categoria') # Categoría de la receta
    instrucciones = request.form.get('instrucciones') # Preparación (pasos) de la receta
    
    foto_filename = 'img/recipes/default_recipe.png' # Valor por defecto

    # Manejo de la subida de archivos para la foto
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER_RECIPES), exist_ok=True)
            file.save(os.path.join(current_app.root_path, UPLOAD_FOLDER_RECIPES, filename))
            foto_filename = f'img/recipes/{filename}' # Guarda la ruta relativa para la DB
        elif file.filename != '':
            flash('Tipo de archivo no permitido para la foto de la receta.', 'danger')
            return redirect(url_for('personal.gestion_recetas'))

    # Asegúrate de que la categoría también se incluya en la validación si es obligatoria
    if not all([nombre, descripcion, ingredientes, categoria]): # Añadir 'categoria' aquí si es obligatoria
        flash('Todos los campos de la receta son obligatorios.', 'danger')
        return redirect(url_for('personal.gestion_recetas'))

    nueva_receta = Recetas(
        nombre=nombre,
        descripcion=descripcion,
        ingredientes=ingredientes,
        categoria=categoria, # Asignar la categoría
        instrucciones=instrucciones, # Preparación de la receta
        cant_ingredientes=_contar_ingredientes(ingredientes),
        foto=foto_filename
    )
    try:
        db.session.add(nueva_receta)
        db.session.commit()
        flash('Receta añadida con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al añadir receta: {e}', 'danger')
    return redirect(url_for('personal.gestion_recetas'))

@personal_bp.route('/editar_receta/<int:id>', methods=['POST'])
def editar_receta(id):
    """
    Edita una receta existente.
    """
    receta = Recetas.query.get_or_404(id)
    
    receta.nombre = request.form.get('nombre')
    receta.descripcion = request.form.get('descripcion')
    receta.ingredientes = request.form.get('ingredientes')
    receta.categoria = request.form.get('categoria') # Actualizar la categoría
    receta.instrucciones = request.form.get('instrucciones') # Actualizar la preparación
    receta.cant_ingredientes = _contar_ingredientes(receta.ingredientes)

    # Manejo de la subida de archivos para la foto (solo si se sube una nueva)
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER_RECIPES), exist_ok=True)
            file.save(os.path.join(current_app.root_path, UPLOAD_FOLDER_RECIPES, filename))
            receta.foto = f'img/recipes/{filename}' # Actualiza la foto en la DB
        elif file.filename != '':
            flash('Tipo de archivo no permitido para la foto de la receta.', 'danger')
            return redirect(url_for('personal.gestion_recetas'))
    # Si no se envió un nuevo archivo, la foto existente en receta.foto se mantiene

    try:
        db.session.commit()
        flash('Receta actualizada con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar receta: {e}', 'danger')
    return redirect(url_for('personal.gestion_recetas'))

@personal_bp.route('/eliminar_receta/<int:id>', methods=['POST'])
def eliminar_receta(id):
    """
    Elimina una receta.
    """
    receta = Recetas.query.get_or_404(id)
    try:
        # Opcional: Eliminar el archivo de la foto del servidor si existe
        if receta.foto and receta.foto != 'img/recipes/default_recipe.png':
            file_path = os.path.join(current_app.root_path, 'static', receta.foto.replace('img/', ''))
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(receta)
        db.session.commit()
        flash('Receta eliminada con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar receta: {e}', 'danger')
    return redirect(url_for('personal.gestion_recetas'))

@personal_bp.route('/api/obtener_receta/<int:id>', methods=['GET'])
def api_obtener_receta(id):
    """
    API para obtener los datos de una receta específica en formato JSON.
    """
    receta = Recetas.query.get(id)
    if not receta:
        return jsonify({'error': 'Receta no encontrada'}), 404
    return jsonify({
        'id_recetas': receta.id_recetas,
        'nombre': receta.nombre,
        'descripcion': receta.descripcion,
        'ingredientes': receta.ingredientes,
        'instrucciones': receta.instrucciones,
        'cant_ingredientes': receta.cant_ingredientes,
        'foto': receta.foto,
        'categoria': receta.categoria # Incluir la categoría en la respuesta API
    })

# --- Gestión de Productos ---
@personal_bp.route('/gestion_productos')
def gestion_productos():
    """
    Muestra la lista de todos los productos.
    """
    productos = Producto.query.all()
    return render_template('personal/gestion_productos.html', productos=productos)

@personal_bp.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    """
    Añade un nuevo producto.
    """
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = request.form.get('precio')
    
    foto_filename = 'img/products/default_product.png' # Valor por defecto

    # Manejo de la subida de archivos para la foto
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER_PRODUCTS), exist_ok=True)
            file.save(os.path.join(current_app.root_path, UPLOAD_FOLDER_PRODUCTS, filename))
            foto_filename = f'img/products/{filename}' # Guarda la ruta relativa para la DB
        elif file.filename != '':
            flash('Tipo de archivo no permitido para la foto del producto.', 'danger')
            return redirect(url_for('personal.gestion_productos'))

    if not all([nombre, descripcion, precio]):
        flash('Todos los campos del producto son obligatorios.', 'danger')
        return redirect(url_for('personal.gestion_productos'))
    
    try:
        precio = float(precio)
    except ValueError:
        flash('El precio debe ser un número válido.', 'danger')
        return redirect(url_for('personal.gestion_productos'))

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        foto=foto_filename
    )
    try:
        db.session.add(nuevo_producto)
        db.session.commit()
        flash('Producto añadido con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al añadir producto: {e}', 'danger')
    return redirect(url_for('personal.gestion_productos'))

@personal_bp.route('/editar_producto/<int:id>', methods=['POST'])
def editar_producto(id):
    """
    Edita un producto existente.
    """
    producto = Producto.query.get_or_404(id)
    
    producto.nombre = request.form.get('nombre')
    producto.descripcion = request.form.get('descripcion')
    
    try:
        producto.precio = float(request.form.get('precio'))
    except ValueError:
        flash('El precio debe ser un número válido.', 'danger')
        db.session.rollback()
        return redirect(url_for('personal.gestion_productos'))

    # Manejo de la subida de archivos para la foto (solo si se sube una nueva)
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER_PRODUCTS), exist_ok=True)
            file.save(os.path.join(current_app.root_path, UPLOAD_FOLDER_PRODUCTS, filename))
            producto.foto = f'img/products/{filename}' # Actualiza la foto en la DB
        elif file.filename != '':
            flash('Tipo de archivo no permitido para la foto del producto.', 'danger')
            return redirect(url_for('personal.gestion_productos'))
    
    try:
        db.session.commit()
        flash('Producto actualizado con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar producto: {e}', 'danger')
    return redirect(url_for('personal.gestion_productos'))

@personal_bp.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    """
    Elimina un producto.
    """
    producto = Producto.query.get_or_404(id)
    try:
        # Opcional: Eliminar el archivo de la foto del servidor si existe
        if producto.foto and producto.foto != 'img/products/default_product.png':
            file_path = os.path.join(current_app.root_path, 'static', producto.foto.replace('img/', ''))
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {e}', 'danger')
    return redirect(url_for('personal.gestion_productos'))

@personal_bp.route('/api/obtener_producto/<int:id>', methods=['GET'])
def api_obtener_producto(id):
    """
    API para obtener los datos de un producto específico en formato JSON.
    """
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    return jsonify({
        'id_producto': producto.id_producto,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': float(producto.precio),
        'foto': producto.foto
    })

# --- Gestión de Usuarios ---
@personal_bp.route('/gestion_usuarios')
def gestion_usuarios():
    """
    Muestra la lista de todos los usuarios.
    """
    usuarios = Usuario.query.all()
    return render_template('personal/gestion_usuarios.html', usuarios=usuarios)

@personal_bp.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    """
    Añade un nuevo usuario. Si es profesional, también crea el registro en la tabla Profesional.
    """
    email = request.form.get('email')
    password = request.form.get('password')
    rol = request.form.get('rol')
    telefono = request.form.get('telefono')

    # --- Validación básica del usuario ---
    if not all([email, password, rol]):
        flash('El email, la contraseña y el rol son obligatorios para el usuario.', 'danger')
        return redirect(url_for('personal.gestion_usuarios'))

    if Usuario.query.filter_by(email=email).first():
        flash('Este email ya está registrado.', 'danger')
        return redirect(url_for('personal.gestion_usuarios'))

    if telefono and not (len(telefono) == 10 and telefono.isdigit()):
        flash('El número de teléfono debe tener 10 dígitos y contener solo números. Por favor, revísalo.', 'danger')
        return redirect(url_for('personal.gestion_usuarios'))

    hashed_password = generate_password_hash(password)
    nuevo_usuario = Usuario(
        email=email,
        contraseña_hash=hashed_password,
        rol=rol,
        telefono=telefono
    )

    try:
        db.session.add(nuevo_usuario)
        db.session.flush()  # Para obtener el ID sin hacer commit aún

        # --- Lógica para usuario profesional ---
        if rol.lower() == "profesional":
            if not _agregar_detalles_profesional(nuevo_usuario.id_usuario, telefono):
                # Si los detalles del profesional fallaron, hacer rollback y redirigir
                db.session.rollback()
                return redirect(url_for('personal.gestion_usuarios'))

        db.session.commit()
        flash('Usuario añadido con éxito.', 'success')

        # --- Notificación por correo electrónico ---
        _enviar_correo_bienvenida(email, password, rol, request.form.get('nombre'), request.form.get('apellido_P'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al añadir usuario: {e}', 'danger')
    
    return redirect(url_for('personal.gestion_usuarios'))


def _agregar_detalles_profesional(user_id, user_phone):
    """Función de ayuda para añadir detalles del profesional."""
    nombre = request.form.get('nombre')
    nombre_segundo = request.form.get('nombre_segundo')
    apellido_P = request.form.get('apellido_P')
    apellido_M = request.form.get('apellido_M')
    cedula = request.form.get('cedula')
    especialidad = request.form.get('especialidad')
    experiencia = request.form.get('experiencia')
    descripcion = request.form.get('descripcion')
    telefono = user_phone  # 

    # Validar campos obligatorios para un profesional
    if not all([nombre, nombre_segundo, apellido_P, apellido_M, cedula]):
        flash('Faltan datos obligatorios para registrar al profesional.', 'danger')
        return False

    if not (len(cedula) == 10 and cedula.isdigit()):
        flash('¡Ups! La cédula debe tener exactamente 10 dígitos y solo números.', 'danger')
        return False
    
    if telefono is None or not (len(telefono) == 10 and telefono.isdigit()):
        flash('El teléfono es obligatorio y debe tener exactamente 10 dígitos.', 'danger')
        return False

    if cedula == telefono:
        flash('El número de cédula no puede ser el mismo que el número de teléfono.', 'danger')
        return False

    nuevo_profesional = Profesional(
        id_usuario=user_id,
        id_empresa=1,
        nombre=nombre,
        nombre_segundo=nombre_segundo,
        apellido_P=apellido_P,
        apellido_M=apellido_M,
        cedula=cedula,
        telefono=telefono,  
        especialidad=especialidad,
        experiencia=int(experiencia) if experiencia else None,
        descripcion=descripcion
    )
    db.session.add(nuevo_profesional)
    return True

def _enviar_correo_bienvenida(email, password , rol,nombre, apellido_P):
    """
    Envía un correo de bienvenida con las credenciales del usuario.
    """
    try:
        nombre_completo = f"{nombre or ''} {apellido_P or ''}".strip()

        # Asunto y contenido del mensaje
        asunto = "Bienvenido a SaludMe"
        cuerpo = f"""

        Hola {nombre_completo},
        Tu cuenta ha sido registrada exitosamente en nuestro sistema SaludMe.
        🔐 CREDENCIALES DE ACCESO:
        Email: {email}
        Contraseña: {password}
        Rol: {rol}


        ⚠️ Por seguridad, te recomendamos cambiar tu contraseña después de ingresar por primera vez.
        Saludos,
        El equipo de SaludMe
        """

        # Crear y enviar el mensaje
        msg = Message(subject=asunto, recipients=[email], body=cuerpo)
        mail.send(msg)
        flash('✅ Correo de bienvenida enviado correctamente.', 'success')

    except Exception as e:
        current_app.logger.error(f"[ERROR ENVÍO CORREO] {e}")
        flash(f'⚠️ No se pudo enviar el correo de bienvenida: {e}', 'warning')
    except Exception as e:
        flash(f'No se pudo enviar el correo de bienvenida: {e}', 'warning')



@personal_bp.route('/editar_usuario/<int:id>', methods=['POST'])
def editar_usuario(id):
    """
    Edita un usuario existente.
    """
    usuario = Usuario.query.get_or_404(id)
    
    new_email = request.form.get('email')
    new_password = request.form.get('password')
    new_rol = request.form.get('rol')
    new_telefono = request.form.get('telefono')

    # Validar si el nuevo email ya existe para otro usuario
    if new_email and new_email != usuario.email and Usuario.query.filter(Usuario.email == new_email).first():
        flash('El nuevo email ya está en uso por otro usuario.', 'danger')
        return redirect(url_for('personal.gestion_usuarios'))

    usuario.email = new_email
    if new_password: # Solo actualizar la contraseña si se proporciona una nueva
        usuario.contraseña_hash = generate_password_hash(new_password)
    usuario.rol = new_rol
    usuario.telefono = new_telefono if new_telefono else None

    try:
        db.session.commit()
        flash('Usuario actualizado con éxito.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar usuario: {e}', 'danger')
    return redirect(url_for('personal.gestion_usuarios'))

@personal_bp.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuario y sus datos relacionados eliminados con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar usuario: {e}', 'danger')
    return redirect(url_for('personal.gestion_usuarios'))

@personal_bp.route('/api/obtener_usuario/<int:id>', methods=['GET'])
def api_obtener_usuario(id):
    """
    API para obtener los datos de un usuario específico en formato JSON.
    """
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    return jsonify({
        'id_usuario': usuario.id_usuario,
        'email': usuario.email,
        'rol': usuario.rol,
        'telefono': usuario.telefono
    })

@personal_bp.route('/api/obtener_profesional/<int:id_usuario>')
def obtener_profesional(id_usuario):
    profesional = Profesional.query.filter_by(id_usuario=id_usuario).first()
    if not profesional:
        return {}, 404

    return {
        "nombre": profesional.nombre,
        "nombre_segundo": profesional.nombre_segundo,
        "apellido_P": profesional.apellido_P,
        "apellido_M": profesional.apellido_M,
        "cedula": profesional.cedula,
        "telefono": profesional.telefono,
        "especialidad": profesional.especialidad,
        "experiencia": profesional.experiencia,
        "descripcion": profesional.descripcion
    }