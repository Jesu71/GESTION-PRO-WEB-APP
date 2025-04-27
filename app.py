# Importación de librerías necesarias
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
import random
from datetime import datetime, timedelta

# Inicialización de la app Flask
app = Flask(__name__)
app.secret_key = 'clave_secreta_panel_admin'

# Carga datos desde un archivo JSON
def load_data(filename):
    file_path = os.path.join('data', filename)
    os.makedirs('data', exist_ok=True)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return []

# Guarda datos en un archivo JSON
def save_data(data, filename):
    file_path = os.path.join('data', filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Genera datos de ejemplo si no existen
def generate_sample_data():
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data/productos.json'):
        productos = [
            {"id": 1, "nombre": "Laptop Pro", "categoria": "Electrónica", "precio": 1200, "stock": 15},
            {"id": 2, "nombre": "Monitor 24\"", "categoria": "Periféricos", "precio": 250, "stock": 30},
            {"id": 3, "nombre": "Teclado Mecánico", "categoria": "Periféricos", "precio": 80, "stock": 45},
            {"id": 4, "nombre": "Mouse Inalámbrico", "categoria": "Periféricos", "precio": 35, "stock": 50},
            {"id": 5, "nombre": "Disco Duro SSD 1TB", "categoria": "Almacenamiento", "precio": 120, "stock": 25}
        ]
        save_data(productos, 'productos.json')
    if not os.path.exists('data/clientes.json'):
        clientes = [
            {"id": 1, "nombre": "Juan Pérez", "email": "juan@ejemplo.com", "telefono": "555-1234", "direccion": "Calle Principal 123"},
            {"id": 2, "nombre": "María López", "email": "maria@ejemplo.com", "telefono": "555-5678", "direccion": "Avenida Central 456"},
            {"id": 3, "nombre": "Carlos Rodríguez", "email": "carlos@ejemplo.com", "telefono": "555-9012", "direccion": "Plaza Mayor 789"},
            {"id": 4, "nombre": "Ana Martínez", "email": "ana@ejemplo.com", "telefono": "555-3456", "direccion": "Calle Segunda 234"},
            {"id": 5, "nombre": "Pedro Sánchez", "email": "pedro@ejemplo.com", "telefono": "555-7890", "direccion": "Avenida Norte 567"}
        ]
        save_data(clientes, 'clientes.json')
    if not os.path.exists('data/ventas.json'):
        ventas = []
        venta_id = 1
        hoy = datetime.now()
        for i in range(30):
            fecha = hoy - timedelta(days=i)
            fecha_str = fecha.strftime("%Y-%m-%d")
            num_ventas = random.randint(1, 3)
            for _ in range(num_ventas):
                cliente_id = random.randint(1, 5)
                items = []
                total = 0
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

# Genera datos de ejemplo al iniciar
generate_sample_data()

# Ruta principal, muestra dashboard
@app.route('/')
def index():
    productos = load_data('productos.json')
    clientes = load_data('clientes.json')
    ventas = load_data('ventas.json')
    now = datetime.now()
    datos_ventas = []
    # Calcula ventas de los últimos 7 días
    for i in range(7):
        fecha = now - timedelta(days=i)
        fecha_str = fecha.strftime("%Y-%m-%d")
        ventas_dia = [v for v in ventas if v["fecha"] == fecha_str]
        total_dia = sum(v["total"] for v in ventas_dia)
        datos_ventas.append({
            "fecha": fecha.strftime("%d/%m"),
            "total": total_dia
        })
    datos_ventas.reverse()
    # Calcula productos más vendidos
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
    productos_top = productos_top[:5]
    return render_template('index.html',
                          now=now,
                          total_productos=len(productos),
                          total_clientes=len(clientes),
                          total_ventas=len(ventas),
                          datos_ventas=datos_ventas,
                          productos_top=productos_top)

# Listado y búsqueda de productos
@app.route('/productos')
def productos():
    busqueda = request.args.get('busqueda', '').lower()
    productos = load_data('productos.json')
    if busqueda:
        productos = [p for p in productos if busqueda in p["nombre"].lower() or busqueda in p["categoria"].lower()]
    return render_template('productos.html', productos=productos)

# Alta de nuevo producto
@app.route('/productos/nuevo', methods=['GET', 'POST'])
def nuevo_producto():
    if request.method == 'POST':
        productos = load_data('productos.json')
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        precio = request.form.get('precio', '')
        stock = request.form.get('stock', '')
        errores = []
        # Validaciones de campos
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

# Edición de producto existente
@app.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    productos = load_data('productos.json')
    producto = next((p for p in productos if p["id"] == id), None)
    if not producto:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('productos'))
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        precio = request.form.get('precio', '')
        stock = request.form.get('stock', '')
        errores = []
        # Validaciones de campos
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
        producto["nombre"] = nombre
        producto["categoria"] = categoria
        producto["precio"] = precio
        producto["stock"] = stock
        save_data(productos, 'productos.json')
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('productos'))
    return render_template('producto_form.html', producto=producto)

# Elimina un producto por ID
@app.route('/productos/eliminar/<int:id>')
def eliminar_producto(id):
    productos = load_data('productos.json')
    productos = [p for p in productos if p["id"] != id]
    save_data(productos, 'productos.json')
    flash('Producto eliminado correctamente', 'success')
    return redirect(url_for('productos'))

# Listado y búsqueda de clientes
@app.route('/clientes')
def clientes():
    busqueda = request.args.get('busqueda', '').lower()
    clientes = load_data('clientes.json')
    if busqueda:
        clientes = [c for c in clientes if busqueda in c["nombre"].lower() or busqueda in c["email"].lower()]
    return render_template('clientes.html', clientes=clientes)

# Alta de nuevo cliente
@app.route('/clientes/nuevo', methods=['GET', 'POST'])
def nuevo_cliente():
    if request.method == 'POST':
        clientes = load_data('clientes.json')
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        errores = []
        # Validaciones de campos
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

# Edición de cliente existente
@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    clientes = load_data('clientes.json')
    cliente = next((c for c in clientes if c["id"] == id), None)
    if not cliente:
        flash('Cliente no encontrado', 'error')
        return redirect(url_for('clientes'))
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        errores = []
        # Validaciones de campos
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
        cliente["nombre"] = nombre
        cliente["email"] = email
        cliente["telefono"] = telefono
        cliente["direccion"] = direccion
        save_data(clientes, 'clientes.json')
        flash('Cliente actualizado correctamente', 'success')
        return redirect(url_for('clientes'))
    return render_template('cliente_form.html', cliente=cliente)

# Elimina un cliente por ID
@app.route('/clientes/eliminar/<int:id>')
def eliminar_cliente(id):
    clientes = load_data('clientes.json')
    clientes = [c for c in clientes if c["id"] != id]
    save_data(clientes, 'clientes.json')
    flash('Cliente eliminado correctamente', 'success')
    return redirect(url_for('clientes'))

# Listado y búsqueda de ventas
@app.route('/ventas')
def ventas():
    busqueda = request.args.get('busqueda', '').lower()
    ventas = load_data('ventas.json')
    clientes = load_data('clientes.json')
    # Asocia nombre de cliente a cada venta
    for venta in ventas:
        cliente = next((c for c in clientes if c["id"] == venta["cliente_id"]), None)
        venta["cliente_nombre"] = cliente["nombre"] if cliente else "Cliente desconocido"
    if busqueda:
        ventas = [v for v in ventas if busqueda in v["cliente_nombre"].lower() or busqueda in v["fecha"]]
    ventas.sort(key=lambda x: x["fecha"], reverse=True)
    return render_template('ventas.html', ventas=ventas)

# Detalle de una venta específica
@app.route('/ventas/detalle/<int:id>')
def detalle_venta(id):
    ventas = load_data('ventas.json')
    productos = load_data('productos.json')
    clientes = load_data('clientes.json')
    venta = next((v for v in ventas if v["id"] == id), None)
    if not venta:
        flash('Venta no encontrada', 'error')
        return redirect(url_for('ventas'))
    cliente = next((c for c in clientes if c["id"] == venta["cliente_id"]), None)
    venta["cliente"] = cliente
    # Asocia producto a cada item de la venta
    for item in venta["items"]:
        producto = next((p for p in productos if p["id"] == item["producto_id"]), None)
        item["producto"] = producto
    return render_template('venta_detalle.html', venta=venta)

# Alta de nueva venta
@app.route('/ventas/nueva', methods=['GET', 'POST'])
def nueva_venta():
    now = datetime.now()
    clientes = load_data('clientes.json')
    productos = load_data('productos.json')
    if request.method == 'POST':
        cliente_id = int(request.form.get('cliente_id'))
        fecha = request.form.get('fecha')
        try:
            datetime.strptime(fecha, '%Y-%m-%d')
        except:
            flash('La fecha no es válida', 'error')
            return render_template('venta_form.html', clientes=clientes, productos=productos)
        items = []
        total_venta = 0
        # Procesa productos seleccionados en la venta
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
        # Actualiza stock de productos vendidos
        for item in items:
            producto = next((p for p in productos if p["id"] == item["producto_id"]), None)
            if producto:
                producto["stock"] -= item["cantidad"]
        save_data(productos, 'productos.json')
        flash('Venta registrada correctamente', 'success')
        return redirect(url_for('ventas'))
    return render_template('venta_form.html', now=now, clientes=clientes, productos=productos)

# Elimina una venta (la mueve a la papelera)
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

# Elimina todas las ventas (las mueve a la papelera)
@app.route('/ventas/eliminar_todas')
def eliminar_todas_ventas():
    ventas = load_data('ventas.json')
    papelera = load_data('papelera_ventas.json')
    for venta in ventas:
        venta["motivo_eliminacion"] = "Eliminación masiva de ventas"
        venta["fecha_eliminacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    papelera.extend(ventas)
    save_data(papelera, 'papelera_ventas.json')
    save_data([], 'ventas.json')
    flash('Todas las ventas han sido movidas a la papelera', 'success')
    return redirect(url_for('ventas'))

# API para obtener productos en formato JSON
@app.route('/api/productos')
def api_productos():
    productos = load_data('productos.json')
    return jsonify(productos)

# Elimina un producto específico de una venta
@app.route('/ventas/eliminar_producto/<int:venta_id>/<int:producto_id>')
def eliminar_producto_venta(venta_id, producto_id):
    ventas = load_data('ventas.json')
    productos = load_data('productos.json')
    venta = next((v for v in ventas if v["id"] == venta_id), None)
    if not venta:
        flash('Venta no encontrada', 'error')
        return redirect(url_for('ventas'))
    item_index = None
    item_eliminado = None
    # Busca el producto en los items de la venta
    for i, item in enumerate(venta["items"]):
        if item["producto_id"] == producto_id:
            item_index = i
            item_eliminado = item
            break
    if item_index is None:
        flash('Producto no encontrado en la venta', 'error')
        return redirect(url_for('detalle_venta', id=venta_id))
    subtotal_eliminado = venta["items"][item_index]["subtotal"]
    venta["total"] -= subtotal_eliminado
    venta["items"].pop(item_index)
    # Si no quedan productos, elimina la venta
    if not venta["items"]:
        ventas = [v for v in ventas if v["id"] != venta_id]
        save_data(ventas, 'ventas.json')
        flash('La venta ha sido eliminada ya que no contiene productos', 'success')
        return redirect(url_for('ventas'))
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if producto:
        producto["stock"] += item_eliminado["cantidad"]
        save_data(productos, 'productos.json')
    save_data(ventas, 'ventas.json')
    flash('Producto eliminado de la venta y stock restaurado', 'success')
    return redirect(url_for('detalle_venta', id=venta_id))

# Mueve una venta a la papelera con motivo
def eliminar_venta_a_papelera(venta_id, motivo):
    ventas = load_data('ventas.json')
    papelera = load_data('papelera_ventas.json')
    venta = next((v for v in ventas if v["id"] == venta_id), None)
    if not venta:
        return False
    venta["motivo_eliminacion"] = motivo
    venta["fecha_eliminacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    papelera.append(venta)
    save_data(papelera, 'papelera_ventas.json')
    ventas = [v for v in ventas if v["id"] != venta_id]
    save_data(ventas, 'ventas.json')
    return True

# Elimina unidades específicas de un producto en una venta
@app.route('/ventas/eliminar_unidades/<int:venta_id>/<int:producto_id>', methods=['POST'])
def eliminar_unidades_producto_venta(venta_id, producto_id):
    ventas = load_data('ventas.json')
    productos = load_data('productos.json')
    venta = next((v for v in ventas if v["id"] == venta_id), None)
    if not venta:
        flash('Venta no encontrada', 'error')
        return redirect(url_for('ventas'))
    item = next((item for item in venta["items"] if item["producto_id"] == producto_id), None)
    if not item:
        flash('Producto no encontrado en la venta', 'error')
        return redirect(url_for('detalle_venta', id=venta_id))
    cantidad_eliminar = int(request.form.get('cantidad_eliminar', 1))
    if cantidad_eliminar <= 0 or cantidad_eliminar > item["cantidad"]:
        flash('Cantidad a eliminar no válida', 'error')
        return redirect(url_for('detalle_venta', id=venta_id))
    precio_unitario = item["precio_unitario"]
    subtotal_eliminar = precio_unitario * cantidad_eliminar
    # Si elimina todas las unidades, elimina el item
    if cantidad_eliminar == item["cantidad"]:
        venta["items"].remove(item)
        if not venta["items"]:
            ventas = [v for v in ventas if v["id"] != venta_id]
            save_data(ventas, 'ventas.json')
            flash('La venta ha sido eliminada ya que no contiene productos', 'success')
            return redirect(url_for('ventas'))
    else:
        item["cantidad"] -= cantidad_eliminar
        item["subtotal"] = item["precio_unitario"] * item["cantidad"]
    venta["total"] -= subtotal_eliminar
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if producto:
        producto["stock"] += cantidad_eliminar
        save_data(productos, 'productos.json')
    save_data(ventas, 'ventas.json')
    flash(f'{cantidad_eliminar} unidad(es) eliminada(s) de la venta y stock restaurado', 'success')
    return redirect(url_for('detalle_venta', id=venta_id))

# Muestra ventas en la papelera
@app.route('/ventas/papelera')
def papelera_ventas():
    busqueda = request.args.get('busqueda', '').lower()
    papelera = load_data('papelera_ventas.json')
    clientes = load_data('clientes.json')
    # Asocia nombre de cliente a cada venta en papelera
    for venta in papelera:
        cliente = next((c for c in clientes if c["id"] == venta["cliente_id"]), None)
        venta["cliente_nombre"] = cliente["nombre"] if cliente else "Cliente desconocido"
    if busqueda:
        papelera = [v for v in papelera if
                   busqueda in v["cliente_nombre"].lower() or
                   busqueda in v["fecha"] or
                   busqueda in v.get("motivo_eliminacion", "").lower()]
    papelera.sort(key=lambda x: x.get("fecha_eliminacion", ""), reverse=True)
    return render_template('papelera_ventas.html', ventas=papelera)

# Restaura una venta desde la papelera
@app.route('/ventas/papelera/restaurar/<int:id>')
def restaurar_venta(id):
    papelera = load_data('papelera_ventas.json')
    ventas = load_data('ventas.json')
    venta = next((v for v in papelera if v["id"] == id), None)
    if not venta:
        flash('Venta no encontrada en la papelera', 'error')
        return redirect(url_for('papelera_ventas'))
    if "motivo_eliminacion" in venta:
        del venta["motivo_eliminacion"]
    if "fecha_eliminacion" in venta:
        del venta["fecha_eliminacion"]
    ventas.append(venta)
    save_data(ventas, 'ventas.json')
    papelera = [v for v in papelera if v["id"] != id]
    save_data(papelera, 'papelera_ventas.json')
    flash('Venta restaurada correctamente', 'success')
    return redirect(url_for('papelera_ventas'))

# Elimina permanentemente una venta de la papelera
@app.route('/ventas/papelera/eliminar/<int:id>')
def eliminar_venta_permanente(id):
    papelera = load_data('papelera_ventas.json')
    papelera = [v for v in papelera if v["id"] != id]
    save_data(papelera, 'papelera_ventas.json')
    flash('Venta eliminada permanentemente', 'success')
    return redirect(url_for('papelera_ventas'))

# Vacía la papelera de ventas
@app.route('/ventas/papelera/vaciar')
def vaciar_papelera():
    save_data([], 'papelera_ventas.json')
    flash('Papelera de ventas vaciada correctamente', 'success')
    return redirect(url_for('papelera_ventas'))

# API para obtener ventas por día en formato JSON
@app.route('/api/ventas-por-dia')
def api_ventas_por_dia():
    ventas = load_data('ventas.json')
    ventas_por_dia = {}
    for venta in ventas:
        fecha = venta["fecha"]
        if fecha in ventas_por_dia:
            ventas_por_dia[fecha] += venta["total"]
        else:
            ventas_por_dia[fecha] = venta["total"]
    resultado = [{"fecha": fecha, "total": total} for fecha, total in ventas_por_dia.items()]
    resultado.sort(key=lambda x: x["fecha"])
    return jsonify(resultado)

# Ejecuta la app en modo debug
if __name__ == '__main__':
    app.run(debug=True)