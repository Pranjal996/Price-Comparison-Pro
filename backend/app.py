from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from scraper import scrape_all
import jwt
import datetime
from functools import wraps
import os

app = Flask(__name__)
CORS(app) # Enable CORS for React frontend

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY','fallback-secret')# In production, use env variable

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    query = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

# Global Cache
search_cache = {}

# Authentication Middleware
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(" ")[1] # Bearer <token>
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# API Endpoints
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Missing data!'}), 400
        
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists!'}), 400
        
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token, 'username': user.username})
        
    return jsonify({'message': 'Invalid credentials!'}), 401

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'message': 'Query parameter "q" is required'}), 400
    
    # Save history if token provided
    token = request.headers.get('Authorization')
    if token:
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data['user_id']
            # Delete duplicate search
            History.query.filter_by(user_id=user_id, query=query).delete()
            new_history = History(user_id=user_id, query=query)
            db.session.add(new_history)
            db.session.commit()
        except:
            pass # Ignore invalid token for history
            
    # Simple dictionary cache
    cache_key = query.lower().strip()
    now = datetime.datetime.utcnow()
    if cache_key in search_cache:
        cached_time, cached_results = search_cache[cache_key]
        if (now - cached_time).total_seconds() < 3600: # 1 hour cache
            results = cached_results
            return jsonify({
                'query': query,
                'results': results,
                'cached': True
            })

    # Scraping logic
    results = scrape_all(query)
    
    # Sort results to easily highlight cheapest
    results = sorted(results, key=lambda x: x['price_val'])
    
    # Save to cache
    search_cache[cache_key] = (now, results)
    
    return jsonify({
        'query': query,
        'results': results
    })

@app.route('/api/history', methods=['GET'])
@token_required
def history(current_user):
    history_records = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).limit(15).all()
    queries = [record.query for record in history_records]
    return jsonify({'history': queries})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
