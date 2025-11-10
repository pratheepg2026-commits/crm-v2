# Mushroom CRM - Flask Backend
# Production-ready API with database integration

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
# --- ENVIRONMENT SETUP ---
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(dotenv_path='.env', override=False):
        try:
            if not os.path.exists(dotenv_path):
                return False
            with open(dotenv_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('\'"')
                    if override or key not in os.environ:
                        os.environ[key] = val
            return True
        except Exception:
            return False

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
db_user = os.getenv('DB_USER', 'postgres')
db_password = quote_plus(os.getenv('DB_PASSWORD', ''))
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'postgres')

database_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'pool_size': 10,
    'max_overflow': 20
}

db = SQLAlchemy(app)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)

# ==================== MODELS ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), default='Owner')
    phone = db.Column(db.String(20))
    farm_name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'phone': self.phone,
            'farm_name': self.farm_name,
            'created_at': self.created_at.isoformat()
        }


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    unit = db.Column(db.String(20), default='box')
    retail_price = db.Column(db.Float, nullable=False)
    wholesale_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'retail_price': self.retail_price,
            'wholesale_price': self.wholesale_price,
            'created_at': self.created_at.isoformat()
        }


class Warehouse(db.Model):
    __tablename__ = 'warehouses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }


class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    warehouse = db.relationship('Warehouse')
    product = db.relationship('Product')
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'quantity': self.quantity,
            'date': self.date.isoformat(),
            'created_at': self.created_at.isoformat()
        }


class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(20), nullable=False)  # retail or wholesale
    customer_name = db.Column(db.String(120))  # For retail
    shop_name = db.Column(db.String(120))  # For wholesale
    shop_address = db.Column(db.Text)
    contact_number = db.Column(db.String(20))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Float)
    unit_price = db.Column(db.Float)
    total = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'type': self.type,
            'customer_name': self.customer_name,
            'shop_name': self.shop_name,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total': self.total,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat()
        }


class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False)
    vendor = db.Column(db.String(120))
    payment_method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'category': self.category,
            'description': self.description,
            'amount': self.amount,
            'vendor': self.vendor,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat()
        }


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float)
    frequency = db.Column(db.String(50))  # Weekly, Bi-weekly, Monthly
    supply_days = db.Column(db.String(255))  # Stored as comma-separated
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'quantity': self.quantity,
            'frequency': self.frequency,
            'supply_days': self.supply_days.split(',') if self.supply_days else [],
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class WholesaleCustomer(db.Model):
    __tablename__ = 'wholesale_customers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(120))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    credit_limit = db.Column(db.Float, default=0)
    outstanding_balance = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'credit_limit': self.credit_limit,
            'outstanding_balance': self.outstanding_balance,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


# ==================== ROUTES ====================

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    user = User(
        email=data['email'],
        name=data['name'],
        role=data.get('role', 'Owner'),
        phone=data.get('phone'),
        farm_name=data.get('farm_name')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'User account is inactive'}), 403
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


# Products Routes
@app.route('/api/products', methods=['GET'])
@jwt_required()
def get_products():
    """Get all products for user"""
    user_id = get_jwt_identity()
    products = Product.query.filter_by(user_id=user_id).all()
    return jsonify([p.to_dict() for p in products]), 200


@app.route('/api/products', methods=['POST'])
@jwt_required()
def create_product():
    """Create a new product"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('retail_price') or not data.get('wholesale_price'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    product = Product(
        user_id=user_id,
        name=data['name'],
        unit=data.get('unit', 'box'),
        retail_price=data['retail_price'],
        wholesale_price=data['wholesale_price']
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({
        'message': 'Product created successfully',
        'product': product.to_dict()
    }), 201


@app.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update a product"""
    user_id = get_jwt_identity()
    product = Product.query.filter_by(id=product_id, user_id=user_id).first()
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.unit = data.get('unit', product.unit)
    product.retail_price = data.get('retail_price', product.retail_price)
    product.wholesale_price = data.get('wholesale_price', product.wholesale_price)
    product.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Product updated successfully',
        'product': product.to_dict()
    }), 200


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete a product"""
    user_id = get_jwt_identity()
    product = Product.query.filter_by(id=product_id, user_id=user_id).first()
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'message': 'Product deleted successfully'}), 200


# Warehouse Routes
@app.route('/api/warehouses', methods=['GET'])
@jwt_required()
def get_warehouses():
    """Get all warehouses for user"""
    user_id = get_jwt_identity()
    warehouses = Warehouse.query.filter_by(user_id=user_id).all()
    return jsonify([w.to_dict() for w in warehouses]), 200


@app.route('/api/warehouses', methods=['POST'])
@jwt_required()
def create_warehouse():
    """Create a new warehouse"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Warehouse name required'}), 400
    
    warehouse = Warehouse(
        user_id=user_id,
        name=data['name']
    )
    
    db.session.add(warehouse)
    db.session.commit()
    
    return jsonify({
        'message': 'Warehouse created successfully',
        'warehouse': warehouse.to_dict()
    }), 201


@app.route('/api/warehouses/<int:warehouse_id>', methods=['PUT'])
@jwt_required()
def update_warehouse(warehouse_id):
    """Update a warehouse"""
    user_id = get_jwt_identity()
    warehouse = Warehouse.query.filter_by(id=warehouse_id, user_id=user_id).first()
    
    if not warehouse:
        return jsonify({'error': 'Warehouse not found'}), 404
    
    data = request.get_json()
    warehouse.name = data.get('name', warehouse.name)
    warehouse.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Warehouse updated successfully',
        'warehouse': warehouse.to_dict()
    }), 200


@app.route('/api/warehouses/<int:warehouse_id>', methods=['DELETE'])
@jwt_required()
def delete_warehouse(warehouse_id):
    """Delete a warehouse"""
    user_id = get_jwt_identity()
    warehouse = Warehouse.query.filter_by(id=warehouse_id, user_id=user_id).first()
    
    if not warehouse:
        return jsonify({'error': 'Warehouse not found'}), 404
    
    # Delete associated inventory
    Inventory.query.filter_by(warehouse_id=warehouse_id).delete()
    db.session.delete(warehouse)
    db.session.commit()
    
    return jsonify({'message': 'Warehouse deleted successfully'}), 200


# Inventory Routes
@app.route('/api/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    """Get all inventory items for user"""
    user_id = get_jwt_identity()
    inventory = Inventory.query.filter_by(user_id=user_id).all()
    return jsonify([i.to_dict() for i in inventory]), 200


@app.route('/api/inventory/warehouse/<int:warehouse_id>', methods=['GET'])
@jwt_required()
def get_warehouse_inventory(warehouse_id):
    """Get inventory for specific warehouse"""
    user_id = get_jwt_identity()
    inventory = Inventory.query.filter_by(user_id=user_id, warehouse_id=warehouse_id).all()
    return jsonify([i.to_dict() for i in inventory]), 200


@app.route('/api/inventory', methods=['POST'])
@jwt_required()
def create_inventory():
    """Add inventory item"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('warehouse_id') or not data.get('product_id') or not data.get('quantity'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if already exists
    existing = Inventory.query.filter_by(
        user_id=user_id,
        warehouse_id=data['warehouse_id'],
        product_id=data['product_id']
    ).first()
    
    if existing:
        existing.quantity += data['quantity']
        existing.date = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'message': 'Inventory updated successfully',
            'inventory': existing.to_dict()
        }), 200
    
    inventory = Inventory(
        user_id=user_id,
        warehouse_id=data['warehouse_id'],
        product_id=data['product_id'],
        quantity=data['quantity'],
        date=datetime.utcnow()
    )
    
    db.session.add(inventory)
    db.session.commit()
    
    return jsonify({
        'message': 'Inventory created successfully',
        'inventory': inventory.to_dict()
    }), 201


@app.route('/api/inventory/<int:inventory_id>', methods=['PUT'])
@jwt_required()
def update_inventory(inventory_id):
    """Update inventory quantity"""
    user_id = get_jwt_identity()
    inventory = Inventory.query.filter_by(id=inventory_id, user_id=user_id).first()
    
    if not inventory:
        return jsonify({'error': 'Inventory item not found'}), 404
    
    data = request.get_json()
    inventory.quantity = data.get('quantity', inventory.quantity)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Inventory updated successfully',
        'inventory': inventory.to_dict()
    }), 200


@app.route('/api/inventory/<int:inventory_id>', methods=['DELETE'])
@jwt_required()
def delete_inventory(inventory_id):
    """Delete inventory item"""
    user_id = get_jwt_identity()
    inventory = Inventory.query.filter_by(id=inventory_id, user_id=user_id).first()
    
    if not inventory:
        return jsonify({'error': 'Inventory item not found'}), 404
    
    db.session.delete(inventory)
    db.session.commit()
    
    return jsonify({'message': 'Inventory deleted successfully'}), 200


# Sales Routes
@app.route('/api/sales', methods=['GET'])
@jwt_required()
def get_sales():
    """Get all sales for user"""
    user_id = get_jwt_identity()
    sales = Sale.query.filter_by(user_id=user_id).order_by(Sale.date.desc()).all()
    return jsonify([s.to_dict() for s in sales]), 200


@app.route('/api/sales', methods=['POST'])
@jwt_required()
def create_sale():
    """Create a new sale"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('type') or not data.get('total'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    sale = Sale(
        user_id=user_id,
        date=datetime.fromisoformat(data['date']) if data.get('date') else datetime.utcnow(),
        type=data['type'],
        customer_name=data.get('customer_name'),
        shop_name=data.get('shop_name'),
        shop_address=data.get('shop_address'),
        contact_number=data.get('contact_number'),
        product_id=data.get('product_id'),
        quantity=data.get('quantity'),
        unit_price=data.get('unit_price'),
        total=data['total'],
        payment_method=data.get('payment_method'),
        notes=data.get('notes')
    )
    
    db.session.add(sale)
    db.session.commit()
    
    return jsonify({
        'message': 'Sale created successfully',
        'sale': sale.to_dict()
    }), 201


@app.route('/api/sales/<int:sale_id>', methods=['PUT'])
@jwt_required()
def update_sale(sale_id):
    """Update a sale"""
    user_id = get_jwt_identity()
    sale = Sale.query.filter_by(id=sale_id, user_id=user_id).first()
    
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404
    
    data = request.get_json()
    sale.customer_name = data.get('customer_name', sale.customer_name)
    sale.shop_name = data.get('shop_name', sale.shop_name)
    sale.quantity = data.get('quantity', sale.quantity)
    sale.total = data.get('total', sale.total)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Sale updated successfully',
        'sale': sale.to_dict()
    }), 200


@app.route('/api/sales/<int:sale_id>', methods=['DELETE'])
@jwt_required()
def delete_sale(sale_id):
    """Delete a sale"""
    user_id = get_jwt_identity()
    sale = Sale.query.filter_by(id=sale_id, user_id=user_id).first()
    
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404
    
    db.session.delete(sale)
    db.session.commit()
    
    return jsonify({'message': 'Sale deleted successfully'}), 200


# Expenses Routes
@app.route('/api/expenses', methods=['GET'])
@jwt_required()
def get_expenses():
    """Get all expenses for user"""
    user_id = get_jwt_identity()
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    return jsonify([e.to_dict() for e in expenses]), 200


@app.route('/api/expenses', methods=['POST'])
@jwt_required()
def create_expense():
    """Create a new expense"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('category') or not data.get('amount'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    expense = Expense(
        user_id=user_id,
        date=datetime.fromisoformat(data['date']) if data.get('date') else datetime.utcnow(),
        category=data['category'],
        description=data.get('description'),
        amount=data['amount'],
        vendor=data.get('vendor'),
        payment_method=data.get('payment_method')
    )
    
    db.session.add(expense)
    db.session.commit()
    
    return jsonify({
        'message': 'Expense created successfully',
        'expense': expense.to_dict()
    }), 201


@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    """Delete an expense"""
    user_id = get_jwt_identity()
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    
    if not expense:
        return jsonify({'error': 'Expense not found'}), 404
    
    db.session.delete(expense)
    db.session.commit()
    
    return jsonify({'message': 'Expense deleted successfully'}), 200


# Subscriptions Routes
@app.route('/api/subscriptions', methods=['GET'])
@jwt_required()
def get_subscriptions():
    """Get all subscriptions for user"""
    user_id = get_jwt_identity()
    subscriptions = Subscription.query.filter_by(user_id=user_id).all()
    return jsonify([s.to_dict() for s in subscriptions]), 200


@app.route('/api/subscriptions', methods=['POST'])
@jwt_required()
def create_subscription():
    """Create a new subscription"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('customer_name') or not data.get('product_id'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    subscription = Subscription(
        user_id=user_id,
        customer_name=data['customer_name'],
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        product_id=data['product_id'],
        quantity=data.get('quantity'),
        frequency=data.get('frequency'),
        supply_days=','.join(data['supply_days']) if data.get('supply_days') else '',
        status='Active'
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({
        'message': 'Subscription created successfully',
        'subscription': subscription.to_dict()
    }), 201


# Dashboard Analytics Route
@app.route('/api/analytics/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_analytics():
    """Get dashboard metrics"""
    user_id = get_jwt_identity()
    
    # Get current month sales
    today = datetime.utcnow()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    sales = Sale.query.filter(
        Sale.user_id == user_id,
        Sale.date >= start_of_month
    ).all()
    
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_of_month
    ).all()
    
    subscriptions = Subscription.query.filter(
        Subscription.user_id == user_id,
        Subscription.status == 'Active'
    ).all()
    
    # Calculate metrics
    total_revenue = sum(s.total for s in sales)
    total_boxes = sum(s.quantity for s in sales if s.quantity)
    total_expenses = sum(e.amount for e in expenses)
    profit = total_revenue - total_expenses
    
    return jsonify({
        'profit': profit,
        'sales_boxes': total_boxes,
        'active_subscriptions': len(subscriptions),
        'monthly_expenses': total_expenses,
        'total_revenue': total_revenue,
        'sales_count': len(sales),
        'expense_count': len(expenses)
    }), 200


# Health Check Route
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Mushroom CRM API is running'}), 200


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500


# Database initialization
@app.before_request
def create_tables():
    db.create_all()


if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', False)
    )
