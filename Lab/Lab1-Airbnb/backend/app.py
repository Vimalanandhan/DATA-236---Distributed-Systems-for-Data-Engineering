"""
Lab 1 Airbnb - Backend API Server
Distributed Systems for Data Engineering (DATA 236)

This module implements a RESTful API for an Airbnb-like listing management system
with distributed systems concepts including microservices architecture, 
load balancing, and horizontal scaling capabilities.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
import logging
import json
from typing import Dict, List, Optional
import uuid

# Configure logging for distributed systems monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app with distributed systems configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'sqlite:///airbnb_lab.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for microservices communication
CORS(app, origins=['http://localhost:3000', 'http://localhost:5000'])

# Initialize database with migration support
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Service discovery and health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancer and service discovery"""
    return jsonify({
        'status': 'healthy',
        'service': 'airbnb-listing-service',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# Database Models for Airbnb Listings
class Listing(db.Model):
    """Airbnb listing model with distributed systems considerations"""
    __tablename__ = 'listings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price_per_night = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    property_type = db.Column(db.String(50), nullable=False)
    amenities = db.Column(db.JSON, nullable=True)  # Store as JSON for flexibility
    max_guests = db.Column(db.Integer, nullable=False, default=1)
    bedrooms = db.Column(db.Integer, nullable=False, default=1)
    bathrooms = db.Column(db.Float, nullable=False, default=1.0)
    host_id = db.Column(db.String(36), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Distributed systems fields
    replica_id = db.Column(db.String(36), nullable=True)  # For data replication
    version = db.Column(db.Integer, default=1)  # For optimistic locking
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price_per_night': self.price_per_night,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'property_type': self.property_type,
            'amenities': self.amenities or [],
            'max_guests': self.max_guests,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'host_id': self.host_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'version': self.version
        }

class Booking(db.Model):
    """Booking model for reservation management"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id = db.Column(db.String(36), db.ForeignKey('listings.id'), nullable=False)
    guest_id = db.Column(db.String(36), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Distributed systems fields
    version = db.Column(db.Integer, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'listing_id': self.listing_id,
            'guest_id': self.guest_id,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'total_price': self.total_price,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'version': self.version
        }

# API Routes for Listings
@app.route('/api/listings', methods=['GET'])
def get_listings():
    """Get all listings with pagination and filtering for distributed systems"""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 100)  # Limit for performance
        
        # Filtering parameters
        location = request.args.get('location')
        property_type = request.args.get('property_type')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        max_guests = request.args.get('max_guests', type=int)
        
        # Build query
        query = Listing.query.filter_by(is_active=True)
        
        if location:
            query = query.filter(Listing.location.ilike(f'%{location}%'))
        if property_type:
            query = query.filter(Listing.property_type == property_type)
        if min_price:
            query = query.filter(Listing.price_per_night >= min_price)
        if max_price:
            query = query.filter(Listing.price_per_night <= max_price)
        if max_guests:
            query = query.filter(Listing.max_guests >= max_guests)
        
        # Execute query with pagination
        paginated_listings = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        logger.info(f"Retrieved {len(paginated_listings.items)} listings for page {page}")
        
        return jsonify({
            'listings': [listing.to_dict() for listing in paginated_listings.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated_listings.total,
                'pages': paginated_listings.pages,
                'has_next': paginated_listings.has_next,
                'has_prev': paginated_listings.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving listings: {str(e)}")
        return jsonify({'error': 'Failed to retrieve listings'}), 500

@app.route('/api/listings/<listing_id>', methods=['GET'])
def get_listing(listing_id):
    """Get a specific listing by ID"""
    try:
        listing = Listing.query.get_or_404(listing_id)
        return jsonify(listing.to_dict())
    except Exception as e:
        logger.error(f"Error retrieving listing {listing_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve listing'}), 500

@app.route('/api/listings', methods=['POST'])
def create_listing():
    """Create a new listing with distributed systems validation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'price_per_night', 'location', 'property_type', 'host_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new listing
        listing = Listing(
            title=data['title'],
            description=data.get('description'),
            price_per_night=float(data['price_per_night']),
            location=data['location'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            property_type=data['property_type'],
            amenities=data.get('amenities', []),
            max_guests=data.get('max_guests', 1),
            bedrooms=data.get('bedrooms', 1),
            bathrooms=data.get('bathrooms', 1.0),
            host_id=data['host_id']
        )
        
        db.session.add(listing)
        db.session.commit()
        
        logger.info(f"Created new listing: {listing.id}")
        return jsonify(listing.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating listing: {str(e)}")
        return jsonify({'error': 'Failed to create listing'}), 500

@app.route('/api/listings/<listing_id>', methods=['PUT'])
def update_listing(listing_id):
    """Update a listing with optimistic locking for distributed systems"""
    try:
        listing = Listing.query.get_or_404(listing_id)
        data = request.get_json()
        
        # Check version for optimistic locking
        if 'version' in data and data['version'] != listing.version:
            return jsonify({'error': 'Version conflict. Please refresh and try again.'}), 409
        
        # Update fields
        updatable_fields = [
            'title', 'description', 'price_per_night', 'location',
            'latitude', 'longitude', 'property_type', 'amenities',
            'max_guests', 'bedrooms', 'bathrooms', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(listing, field, data[field])
        
        listing.version += 1
        listing.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Updated listing: {listing_id}")
        return jsonify(listing.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating listing {listing_id}: {str(e)}")
        return jsonify({'error': 'Failed to update listing'}), 500

@app.route('/api/listings/<listing_id>', methods=['DELETE'])
def delete_listing(listing_id):
    """Soft delete a listing"""
    try:
        listing = Listing.query.get_or_404(listing_id)
        listing.is_active = False
        listing.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Soft deleted listing: {listing_id}")
        return jsonify({'message': 'Listing deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting listing {listing_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete listing'}), 500

# API Routes for Bookings
@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """Create a new booking with distributed systems validation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['listing_id', 'guest_id', 'check_in', 'check_out']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if listing exists and is active
        listing = Listing.query.get(data['listing_id'])
        if not listing or not listing.is_active:
            return jsonify({'error': 'Listing not found or inactive'}), 404
        
        # Calculate total price
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        nights = (check_out - check_in).days
        total_price = nights * listing.price_per_night
        
        # Create booking
        booking = Booking(
            listing_id=data['listing_id'],
            guest_id=data['guest_id'],
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        logger.info(f"Created new booking: {booking.id}")
        return jsonify(booking.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating booking: {str(e)}")
        return jsonify({'error': 'Failed to create booking'}), 500

@app.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get a specific booking by ID"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        return jsonify(booking.to_dict())
    except Exception as e:
        logger.error(f"Error retrieving booking {booking_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve booking'}), 500

# Distributed Systems Monitoring Endpoints
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics for monitoring"""
    try:
        total_listings = Listing.query.count()
        active_listings = Listing.query.filter_by(is_active=True).count()
        total_bookings = Booking.query.count()
        
        return jsonify({
            'total_listings': total_listings,
            'active_listings': active_listings,
            'total_bookings': total_bookings,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve metrics'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Database initialization
def create_tables():
    """Create database tables"""
    db.create_all()
    logger.info("Database tables created")

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Airbnb Lab 1 backend server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
