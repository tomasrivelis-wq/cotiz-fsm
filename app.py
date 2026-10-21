from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import os

app = Flask(__name__)

# Configuración Base de Datos: Si estamos en Koyeb usa Postgres, sino SQLite local.
database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__name__)), 'cotizador.db'))
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Tablas de Base de Datos
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    desc = db.Column(db.String(255))
    modelo = db.Column(db.String(255))
    pago = db.Column(db.String(100))
    precio = db.Column(db.Float)

class Cotizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numCot = db.Column(db.String(50))
    fecha = db.Column(db.String(50))
    vendedor = db.Column(db.String(100))
    cliente = db.Column(db.String(255))
    cuit = db.Column(db.String(50))
    items = db.Column(db.Text)
    total = db.Column(db.Float)
    estado = db.Column(db.String(50))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('Cotizador_Online.html')

@app.route('/api/productos', methods=['GET'])
def get_productos():
    productos = Producto.query.all()
    return jsonify([{'id': p.id, 'desc': p.desc, 'modelo': p.modelo, 'pago': p.pago, 'precio': p.precio} for p in productos])

@app.route('/api/productos/sync', methods=['POST'])
def sync_productos():
    data = request.json
    if not data or not isinstance(data, list): return jsonify({'error': 'Error de datos'}), 400
    try:
        db.session.query(Producto).delete()
        nuevos = [Producto(desc=p.get('desc'), modelo=p.get('modelo'), pago=p.get('pago'), precio=p.get('precio')) for p in data]
        db.session.add_all(nuevos)
        db.session.commit()
        return jsonify({'status': 'ok'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cotizaciones', methods=['GET', 'POST'])
def cotizaciones():
    if request.method == 'GET':
        cots = Cotizacion.query.order_by(Cotizacion.id.desc()).all()
        return jsonify([{
            'numCot': c.numCot, 'fecha': c.fecha, 'vendedor': c.vendedor,
            'cliente': c.cliente, 'cuit': c.cuit, 'items': json.loads(c.items) if c.items else [],
            'total': c.total, 'estado': c.estado
        } for c in cots])
    elif request.method == 'POST':
        data = request.json
        nueva = Cotizacion(
            numCot=data.get('numCot'), fecha=data.get('fecha'), vendedor=data.get('vendedor'), 
            cliente=data.get('cliente'), cuit=data.get('cuit'), items=json.dumps(data.get('items', [])),
            total=data.get('total'), estado=data.get('estado', 'Emitido')
        )
        db.session.add(nueva)
        db.session.commit()
        return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)