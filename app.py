from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'clave_secreta_panel_admin'

# Cargar datos desde archivos JSON o crearlos si no existen
def load_data(filename):
    file_path = os.path.join('data', filename)
    os.makedirs('data', exist_ok=True)
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return []

def save_data(data, filename):
    file_path = os.path.join('data', filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Generar datos de ejemplo si no existen
def generate_sample_data():
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Productos de ejemplo
    if not os.path.exists('data/productos.json'):
        productos = [
            {"id": 1, "nombre": "Laptop Pro", "categoria": "Electrónica", "precio": 1200, "stock": 15},
            {"id": 2, "nombre": "Monitor 24\"", "categoria": "Periféricos", "precio": 250, "stock": 30},
            {"id": 3, "nombre": "Teclado Mecánico", "categoria": "Periféricos", "precio": 80, "stock": 45},
            {"id": 4, "nombre": "Mouse Inalámbrico", "categoria": "Periféricos", "precio": 35, "stock": 50},
            {"id": 5, "nombre": "Disco Duro SSD 1TB", "categoria": "Almacenamiento", "precio": 120, "stock": 25}
        ]
        save_data(productos, 'productos.json')
    
    # Clientes de ejemplo
    if not os.path.exists('data/clientes.json'):
        clientes = [
            {"id": 1, "nombre": "Juan Pérez", "email": "juan@ejemplo.com", "telefono": "555-1234", "direccion": "Calle Principal 123"},
            {"id": 2, "nombre": "María López", "email": "maria@ejemplo.com", "telefono": "555-5678", "direccion": "Avenida Central 456"},
            {"id": 3, "nombre": "Carlos Rodríguez", "email": "carlos@ejemplo.com", "telefono": "555-9012", "direccion": "Plaza Mayor 789"},
            {"id": 4, "nombre": "Ana Martínez", "email": "ana@ejemplo.com", "telefono": "555-3456", "direccion": "Calle Segunda 234"},
            {"id": 5, "nombre": "Pedro Sánchez", "email": "pedro@ejemplo.com", "telefono": "555-7890", "direccion": "Avenida Norte 567"}
        ]
        save_data(clientes, 'clientes.json')
    
    # Ventas de ejemplo
    if not os.path.exists('data/ventas.json'):
        # Generar datos de los últimos 30 días
        ventas = []
        venta_id = 1
        hoy = datetime.now()
        
        for i in range(30):
            fecha = hoy - timedelta(days=i)
            fecha_str = fecha.strftime("%Y-%m-%d")
            
            # Generar de 1 a 3 ventas por día
            num_ventas = random.randint(1, 3)
            for _ in range(num_ventas):
                cliente_id = random.randint(1, 5)
                items = []
                total = 0
                
                # Añadir de 1 a 3 productos por venta
                num_productos = random.randint(1, 3)
                for _ in range(num_productos):
                    producto_id = random.randint(1, 5)
                    cantidad = random.randint(1, 3)
                    precio_unitario = [p["precio"] for p in load_data('productos.json') if p["id"] == producto_id][0]
                    subtotal = precio_unitario * cantidad
                    total += subtotal
                    
                    items.append({
                        "producto_id": producto_id,
                        "cantidad": cantidad,
                        "precio_unitario": precio_unitario,
                        "subtotal": subtotal
                    })
                
                ventas.append({
                    "id": venta_id,
                    "cliente_id": cliente_id,
                    "fecha": fecha_str,
                    "items": items,
                    "total": total,
                    "notas": f"Venta de ejemplo #{venta_id}"
                })
                
                venta_id += 1
        
        save_data(ventas, 'ventas.json')

# Generar datos iniciales
generate_sample_data()

# Rutas principales
@app.route('/')
def index():
    # Carga datos para estadísticas del dashboard
    productos = load_data('productos.json')
    clientes = load_data('clientes.json')
    ventas = load_data('ventas.json')
    
    # Datos para el gráfico de ventas diarias (últimos 7 días)
    now = datetime.now()
    datos_ventas = []
    for i in range(7):
        fecha = now - timedelta(days=i)
        fecha_str = fecha.strftime("%Y-%m-%d")
        ventas_dia = [v for v in ventas if v["fecha"] == fecha_str]
        total_dia = sum(v["total"] for v in ventas_dia)
        datos_ventas.append({
            "fecha": fecha.strftime("%d/%m"),
            "total": total_dia
        })
    
    # Invertir para que aparezcan en orden cronológico
    datos_ventas.reverse()
    
    # Productos top (por cantidad vendida)
    productos_vendidos = {}
    for venta in ventas:
        for item in venta["items"]:
            prod_id = item["producto_id"]
            if prod_id in productos_vendidos:
                productos_vendidos[prod_id] += item["cantidad"]
            else:
                productos_vendidos[prod_id] = item["cantidad"]
    
    productos_top = []
    for prod_id, cantidad in productos_vendidos.items():
        producto = next((p for p in productos if p["id"] == prod_id), None)
        if producto:
            productos_top.append({
                "nombre": producto["nombre"],
                "cantidad": cantidad
            })
    
    productos_top.sort(key=lambda x: x["cantidad"], reverse=True)
    productos_top = productos_top[:5]  # Top 5
    
    return render_template('index.html',
                          now=now,  
                          total_productos=len(productos),
                          total_clientes=len(clientes),
                          total_ventas=len(ventas),
                          datos_ventas=datos_ventas,
                          productos_top=productos_top)

@app.route('/productos')
def productos():
    busqueda = request.args.get('busqueda', '').lower()
    productos = load_data('productos.json')
    
    if busqueda:
        productos = [p for p in productos if busqueda in p["nombre"].lower() or busqueda in p["categoria"].lower()]
    
    return render_template('productos.html', productos=productos)

@app.route('/productos/nuevo', methods=['GET', 'POST'])
def nuevo_producto():
    if request.method == 'POST':
        productos = load_data('productos.json')
        
        # Validar formulario
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        precio = request.form.get('precio', '')
        stock = request.form.get('stock', '')
        
        errores = []
        if not nombre:
            errores.append('El nombre del producto es obligatorio')
        if not categoria:
            errores.append('La categoría es obligatoria')
        try:
            precio = float(precio)
            if precio <= 0:
                errores.append('El precio debe ser mayor que cero')
        except:
            errores.append('El precio debe ser un número válido')
        try:
            stock = int(stock)
            if stock < 0:
                errores.append('El stock no puede ser negativo')
        except:
            errores.append('El stock debe ser un número entero')
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('producto_form.html')
        
        # Crear nuevo producto
        nuevo_id = max([p["id"] for p in productos], default=0) + 1
        nuevo_producto = {
            "id": nuevo_id,
            "nombre": nombre,
            "categoria": categoria,
            "precio": precio,
            "stock": stock
        }
        
        productos.append(nuevo_producto)
        save_data(productos, 'productos.json')
        flash('Producto agregado correctamente', 'success')
        return redirect(url_for('productos'))
    
    return render_template('producto_form.html')

@app.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    productos = load_data('productos.json')
    producto = next((p for p in productos if p["id"] == id), None)
    
    if not producto:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('productos'))
    
    if request.method == 'POST':
        # Validar formulario
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        precio = request.form.get('precio', '')
        stock = request.form.get('stock', '')
        
        errores = []
        if not nombre:
            errores.append('El nombre del producto es obligatorio')
        if not categoria:
            errores.append('La categoría es obligatoria')
        try:
            precio = float(precio)
            if precio <= 0:
                errores.append('El precio debe ser mayor que cero')
        except:
            errores.append('El precio debe ser un número válido')
        try:
            stock = int(stock)
            if stock < 0:
                errores.append('El stock no puede ser negativo')
        except:
            errores.append('El stock debe ser un número entero')
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('producto_form.html', producto=producto)
        
        # Actualizar producto
        producto["nombre"] = nombre
        producto["categoria"] = categoria
        producto["precio"] = precio
        producto["stock"] = stock
        
        save_data(productos, 'productos.json')
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('productos'))
    
    return render_template('producto_form.html', producto=producto)

@app.route('/productos/eliminar/<int:id>')
def eliminar_producto(id):
    productos = load_data('productos.json')
    productos = [p for p in productos if p["id"] != id]
    save_data(productos, 'productos.json')
    flash('Producto eliminado correctamente', 'success')
    return redirect(url_for('productos'))

@app.route('/clientes')
def clientes():
    busqueda = request.args.get('busqueda', '').lower()
    clientes = load_data('clientes.json')
    
    if busqueda:
        clientes = [c for c in clientes if busqueda in c["nombre"].lower() or busqueda in c["email"].lower()]
    
    return render_template('clientes.html', clientes=clientes)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
def nuevo_cliente():
    if request.method == 'POST':
        clientes = load_data('clientes.json')
        
        # Validar formulario
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        
        errores = []
        if not nombre:
            errores.append('El nombre del cliente es obligatorio')
        if not email:
            errores.append('El email es obligatorio')
        if '@' not in email:
            errores.append('El email no es válido')
        if not telefono:
            errores.append('El teléfono es obligatorio')
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('cliente_form.html')
        
        # Crear nuevo cliente
        nuevo_id = max([c["id"] for c in clientes], default=0) + 1
        nuevo_cliente = {
            "id": nuevo_id,
            "nombre": nombre,
            "email": email,
            "telefono": telefono,
            "direccion": direccion
        }
        
        clientes.append(nuevo_cliente)
        save_data(clientes, 'clientes.json')
        flash('Cliente agregado correctamente', 'success')
        return redirect(url_for('clientes'))
    
    return render_template('cliente_form.html')

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    clientes = load_data('clientes.json')
    cliente = next((c for c in clientes if c["id"] == id), None)
    
    if not cliente:
        flash('Cliente no encontrado', 'error')
        return redirect(url_for('clientes'))
    
    if request.method == 'POST':
        # Validar formulario
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        
        errores = []
        if not nombre:
            errores.append('El nombre del cliente es obligatorio')
        if not email:
            errores.append('El email es obligatorio')
        if '@' not in email:
            errores.append('El email no es válido')
        if not telefono:
            errores.append('El teléfono es obligatorio')
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('cliente_form.html', cliente=cliente)
        
        # Actualizar cliente
        cliente["nombre"] = nombre
        cliente["email"] = email
        cliente["telefono"] = telefono
        cliente["direccion"] = direccion
        
        save_data(clientes, 'clientes.json')
        flash('Cliente actualizado correctamente', 'success')
        return redirect(url_for('clientes'))
    
    return render_template('cliente_form.html', cliente=cliente)

@app.route('/clientes/eliminar/<int:id>')
def eliminar_cliente(id):
    clientes = load_data('clientes.json')
    clientes = [c for c in clientes if c["id"] != id]
    save_data(clientes, 'clientes.json')
    flash('Cliente eliminado correctamente', 'success')
    return redirect(url_for('clientes'))

@app.route('/ventas')
def ventas():
    busqueda = request.args.get('busqueda', '').lower()
    ventas = load_data('ventas.json')
    clientes = load_data('clientes.json')
    
    # Enriquecer datos de ventas con nombre del cliente
    for venta in ventas:
        cliente = next((c for c in clientes if c["id"] == venta["cliente_id"]), None)
        venta["cliente_nombre"] = cliente["nombre"] if cliente else "Cliente desconocido"
    
    if busqueda:
        ventas = [v for v in ventas if busqueda in v["cliente_nombre"].lower() or busqueda in v["fecha"]]
    
    # Ordenar ventas por fecha descendente
    ventas.sort(key=lambda x: x["fecha"], reverse=True)
    
    return render_template('ventas.html', ventas=ventas)

@app.route('/ventas/detalle/<int:id>')
def detalle_venta(id):
    ventas = load_data('ventas.json')
    productos = load_data('productos.json')
    clientes = load_data('clientes.json')
    
    venta = next((v for v in ventas if v["id"] == id), None)
    
    if not venta:
        flash('Venta no encontrada', 'error')
        return redirect(url_for('ventas'))
    
    # Enriquecer con datos de productos y cliente
    cliente = next((c for c in clientes if c["id"] == venta["cliente_id"]), None)
    venta["cliente"] = cliente
    
    for item in venta["items"]:
        producto = next((p for p in productos if p["id"] == item["producto_id"]), None)
        item["producto"] = producto
    
    return render_template('venta_detalle.html', venta=venta)

@app.route('/ventas/nueva', methods=['GET', 'POST'])
def nueva_venta():
    now = datetime.now()
    clientes = load_data('clientes.json')
    productos = load_data('productos.json')
    
    if request.method == 'POST':
        # Procesar formulario de venta
        cliente_id = int(request.form.get('cliente_id'))
        fecha = request.form.get('fecha')
        
        # Validar fecha
        try:
            datetime.strptime(fecha, '%Y-%m-%d')
        except:
            flash('La fecha no es válida', 'error')
            return render_template('venta_form.html', clientes=clientes, productos=productos)
        
        # Obtener items seleccionados
        items = []
        total_venta = 0
        
        for key in request.form:
            if key.startswith('cantidad_'):
                producto_id = int(key.replace('cantidad_', ''))
                cantidad = int(request.form[key])
                
                if cantidad > 0:
                    producto = next((p for p in productos if p["id"] == producto_id), None)
                    if producto:
                        subtotal = producto["precio"] * cantidad
                        items.append({
                            "producto_id": producto_id,
                            "cantidad": cantidad,
                            "precio_unitario": producto["precio"],
                            "subtotal": subtotal
                        })
                        total_venta += subtotal
        
        if not items:
            flash('Debe seleccionar al menos un producto', 'error')
            return render_template('venta_form.html', clientes=clientes, productos=productos)
        
        # Crear nueva venta
        ventas = load_data('ventas.json')
        nuevo_id = max([v["id"] for v in ventas], default=0) + 1
        
        nueva_venta = {
            "id": nuevo_id,
            "cliente_id": cliente_id,
            "fecha": fecha,
            "items": items,
            "total": total_venta,
            "notas": request.form.get('notas', '') 
        }
        
        ventas.append(nueva_venta)
        save_data(ventas, 'ventas.json')
        
        # Actualizar stock
        for item in items:
            producto = next((p for p in productos if p["id"] == item["producto_id"]), None)
            if producto:
                producto["stock"] -= item["cantidad"]
        
        save_data(productos, 'productos.json')
        
        flash('Venta registrada correctamente', 'success')
        return redirect(url_for('ventas'))
    
    return render_template('venta_form.html',now=now, clientes=clientes, productos=productos)

@app.route('/ventas/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_venta(id):
    if request.method == 'POST':
        motivo = request.form.get('motivo', 'Sin motivo especificado')
        if eliminar_venta_a_papelera(id, motivo):
            flash('Venta movida a la papelera correctamente', 'success')
        else:
            flash('Error al mover la venta a la papelera', 'error')
        return redirect(url_for('ventas'))
    
    return render_template('eliminar_venta_form.html', venta_id=id)

@app.route('/ventas/eliminar_todas')
def eliminar_todas_ventas():
    ventas = load_data('ventas.json')
    papelera = load_data('papelera_ventas.json')
    
    # Añadir motivo y fecha de eliminación a todas las ventas
    for venta in ventas:
        venta["motivo_eliminacion"] = "Eliminación masiva de ventas"
        venta["fecha_eliminacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Mover todas las ventas a la papelera
    papelera.extend(ventas)
    save_data(papelera, 'papelera_ventas.json')
    
    # Vaciar las ventas activas
    save_data([], 'ventas.json')
    
    flash('Todas las ventas han sido movidas a la papelera', 'success')
    return redirect(url_for('ventas'))

@app.route('/api/productos')
def api_productos():
    productos = load_data('productos.json')
    return jsonify(productos)

@app.route('/ventas/eliminar_producto/<int:venta_id>/<int:producto_id>')
def eliminar_producto_venta(venta_id, producto_id):
    ventas = load_data('ventas.json')
    productos = load_data('productos.json')
    
    # Encontrar la venta
    venta = next((v for v in ventas if v["id"] == venta_id), None)
    if not venta:
        flash('Venta no encontrada', 'error')
        return redirect(url_for('ventas'))
    
    # Encontrar el ítem del producto en la venta
    item_index = None
    item_eliminado = None
    for i, item in enumerate(venta["items"]):
        if item["producto_id"] == producto_id:
            item_index = i
            item_eliminado = item
            break
    
    if item_index is None:
        flash('Producto no encontrado en la venta', 'error')
        return redirect(url_for('detalle_venta', id=venta_id))
    
    # Restar el subtotal del total de la venta
    subtotal_eliminado = venta["items"][item_index]["subtotal"]
    venta["total"] -= subtotal_eliminado
    
    # Eliminar el ítem
    venta["items"].pop(item_index)
    
    # Si no quedan productos, eliminar toda la venta
    if not venta["items"]:
        ventas = [v for v in ventas if v["id"] != venta_id]
        save_data(ventas, 'ventas.json')
        flash('La venta ha sido eliminada ya que no contiene productos', 'success')
        return redirect(url_for('ventas'))
    
    # Restaurar el stock del producto
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if producto:
        producto["stock"] += item_eliminado["cantidad"]
        save_data(productos, 'productos.json')
    
    # Guardar los cambios
    save_data(ventas, 'ventas.json')
    
    flash('Producto eliminado de la venta y stock restaurado', 'success')
    return redirect(url_for('detalle_venta', id=venta_id))

# Añadir estas líneas después de las otras funciones de carga/guardado
def eliminar_venta_a_papelera(venta_id, motivo):
    ventas = load_data('ventas.json')
    papelera = load_data('papelera_ventas.json')
    
    # Buscar la venta a eliminar
    venta = next((v for v in ventas if v["id"] == venta_id), None)
    if not venta:
        return False
    
    # Añadir motivo de eliminación y fecha
    venta["motivo_eliminacion"] = motivo
    venta["fecha_eliminacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Mover a la papelera
    papelera.append(venta)
    save_data(papelera, 'papelera_ventas.json')
    
    # Eliminar de ventas activas
    ventas = [v for v in ventas if v["id"] != venta_id]
    save_data(ventas, 'ventas.json')
    
    return True

# Añadir esta nueva ruta después de eliminar_producto_venta

@app.route('/ventas/eliminar_unidades/<int:venta_id>/<int:producto_id>', methods=['POST'])
def eliminar_unidades_producto_venta(venta_id, producto_id):
    ventas = load_data('ventas.json')
    productos = load_data('productos.json')
    
    # Encontrar la venta
    venta = next((v for v in ventas if v["id"] == venta_id), None)
    if not venta:
        flash('Venta no encontrada', 'error')
        return redirect(url_for('ventas'))
    
    # Encontrar el ítem del producto en la venta
    item = next((item for item in venta["items"] if item["producto_id"] == producto_id), None)
    if not item:
        flash('Producto no encontrado en la venta', 'error')
        return redirect(url_for('detalle_venta', id=venta_id))
    
    # Obtener cantidad a eliminar
    cantidad_eliminar = int(request.form.get('cantidad_eliminar', 1))
    
    # Validar que la cantidad a eliminar sea válida
    if cantidad_eliminar <= 0 or cantidad_eliminar > item["cantidad"]:
        flash('Cantidad a eliminar no válida', 'error')
        return redirect(url_for('detalle_venta', id=venta_id))
    
    # Calcular nuevo subtotal y reducir cantidad
    precio_unitario = item["precio_unitario"]
    subtotal_eliminar = precio_unitario * cantidad_eliminar
    
    # Actualizar el ítem
    if cantidad_eliminar == item["cantidad"]:
        # Si eliminamos todas las unidades, eliminar el ítem completo
        venta["items"].remove(item)
        if not venta["items"]:
            # Si no quedan productos, eliminar toda la venta
            ventas = [v for v in ventas if v["id"] != venta_id]
            save_data(ventas, 'ventas.json')
            flash('La venta ha sido eliminada ya que no contiene productos', 'success')
            return redirect(url_for('ventas'))
    else:
        # Reducir cantidad y subtotal
        item["cantidad"] -= cantidad_eliminar
        item["subtotal"] = item["precio_unitario"] * item["cantidad"]
    
    # Actualizar el total de la venta
    venta["total"] -= subtotal_eliminar
    
    # Restaurar el stock del producto
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if producto:
        producto["stock"] += cantidad_eliminar
        save_data(productos, 'productos.json')
    
    # Guardar los cambios
    save_data(ventas, 'ventas.json')
    
    flash(f'{cantidad_eliminar} unidad(es) eliminada(s) de la venta y stock restaurado', 'success')
    return redirect(url_for('detalle_venta', id=venta_id))

# Añadir rutas para la papelera de ventas
@app.route('/ventas/papelera')
def papelera_ventas():
    busqueda = request.args.get('busqueda', '').lower()
    papelera = load_data('papelera_ventas.json')
    clientes = load_data('clientes.json')
    
    # Enriquecer datos de ventas con nombre del cliente
    for venta in papelera:
        cliente = next((c for c in clientes if c["id"] == venta["cliente_id"]), None)
        venta["cliente_nombre"] = cliente["nombre"] if cliente else "Cliente desconocido"
    
    if busqueda:
        papelera = [v for v in papelera if 
                   busqueda in v["cliente_nombre"].lower() or 
                   busqueda in v["fecha"] or 
                   busqueda in v.get("motivo_eliminacion", "").lower()]
    
    # Ordenar ventas por fecha de eliminación descendente
    papelera.sort(key=lambda x: x.get("fecha_eliminacion", ""), reverse=True)
    
    return render_template('papelera_ventas.html', ventas=papelera)

@app.route('/ventas/papelera/restaurar/<int:id>')
def restaurar_venta(id):
    papelera = load_data('papelera_ventas.json')
    ventas = load_data('ventas.json')
    
    # Buscar la venta a restaurar
    venta = next((v for v in papelera if v["id"] == id), None)
    if not venta:
        flash('Venta no encontrada en la papelera', 'error')
        return redirect(url_for('papelera_ventas'))
    
    # Eliminar campos adicionales de la papelera
    if "motivo_eliminacion" in venta:
        del venta["motivo_eliminacion"]
    if "fecha_eliminacion" in venta:
        del venta["fecha_eliminacion"]
    
    # Mover de vuelta a ventas activas
    ventas.append(venta)
    save_data(ventas, 'ventas.json')
    
    # Eliminar de la papelera
    papelera = [v for v in papelera if v["id"] != id]
    save_data(papelera, 'papelera_ventas.json')
    
    flash('Venta restaurada correctamente', 'success')
    return redirect(url_for('papelera_ventas'))

@app.route('/ventas/papelera/eliminar/<int:id>')
def eliminar_venta_permanente(id):
    papelera = load_data('papelera_ventas.json')
    
    # Eliminar de la papelera
    papelera = [v for v in papelera if v["id"] != id]
    save_data(papelera, 'papelera_ventas.json')
    
    flash('Venta eliminada permanentemente', 'success')
    return redirect(url_for('papelera_ventas'))

@app.route('/ventas/papelera/vaciar')
def vaciar_papelera():
    # Guardar un array vacío en el archivo de la papelera
    save_data([], 'papelera_ventas.json')
    flash('Papelera de ventas vaciada correctamente', 'success')
    return redirect(url_for('papelera_ventas'))

@app.route('/api/ventas-por-dia')
def api_ventas_por_dia():
    ventas = load_data('ventas.json')
    
    # Agrupar ventas por fecha
    ventas_por_dia = {}
    for venta in ventas:
        fecha = venta["fecha"]
        if fecha in ventas_por_dia:
            ventas_por_dia[fecha] += venta["total"]
        else:
            ventas_por_dia[fecha] = venta["total"]
    
    # Convertir a lista para la API
    resultado = [{"fecha": fecha, "total": total} for fecha, total in ventas_por_dia.items()]
    
    # Ordenar por fecha
    resultado.sort(key=lambda x: x["fecha"])
    
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(debug=True)