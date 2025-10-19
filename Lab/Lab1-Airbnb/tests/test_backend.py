"""
Lab 1 Airbnb - Backend Test Suite
Distributed Systems for Data Engineering (DATA 236)

Comprehensive test suite for the Airbnb listing management system
with distributed systems testing scenarios.
"""

import unittest
import json
import os
import tempfile
from datetime import datetime, date, timedelta
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, db, Listing, Booking

class TestAirbnbAPI(unittest.TestCase):
    """Test cases for the Airbnb API endpoints"""
    
    def setUp(self):
        """Set up test database and client"""
        # Create a temporary database
        self.db_fd, app.config['DATABASE_URL'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.test_client()
        
        # Create tables
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE_URL'])
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'airbnb-listing-service')
        self.assertIn('timestamp', data)
    
    def test_create_listing(self):
        """Test creating a new listing"""
        listing_data = {
            'title': 'Beautiful Apartment in Downtown',
            'description': 'A modern apartment with great views',
            'price_per_night': 150.0,
            'location': 'San Francisco, CA',
            'latitude': 37.7749,
            'longitude': -122.4194,
            'property_type': 'apartment',
            'amenities': ['wifi', 'parking', 'pool'],
            'max_guests': 4,
            'bedrooms': 2,
            'bathrooms': 2.0,
            'host_id': 'host_123'
        }
        
        response = self.app.post('/api/listings', 
                                data=json.dumps(listing_data),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertEqual(data['title'], listing_data['title'])
        self.assertEqual(data['price_per_night'], listing_data['price_per_night'])
        self.assertEqual(data['location'], listing_data['location'])
        self.assertIn('id', data)
        self.assertIn('created_at', data)
    
    def test_get_listings(self):
        """Test retrieving listings"""
        # Create test listings
        with app.app_context():
            listing1 = Listing(
                title='Test Listing 1',
                price_per_night=100.0,
                location='Test City',
                property_type='house',
                host_id='host_1'
            )
            listing2 = Listing(
                title='Test Listing 2',
                price_per_night=200.0,
                location='Test City',
                property_type='apartment',
                host_id='host_2'
            )
            db.session.add(listing1)
            db.session.add(listing2)
            db.session.commit()
        
        response = self.app.get('/api/listings')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('listings', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['listings']), 2)
    
    def test_get_listing_by_id(self):
        """Test retrieving a specific listing"""
        with app.app_context():
            listing = Listing(
                title='Test Listing',
                price_per_night=150.0,
                location='Test City',
                property_type='house',
                host_id='host_1'
            )
            db.session.add(listing)
            db.session.commit()
            listing_id = listing.id
        
        response = self.app.get(f'/api/listings/{listing_id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['title'], 'Test Listing')
        self.assertEqual(data['id'], listing_id)
    
    def test_update_listing(self):
        """Test updating a listing with optimistic locking"""
        with app.app_context():
            listing = Listing(
                title='Original Title',
                price_per_night=100.0,
                location='Original City',
                property_type='house',
                host_id='host_1'
            )
            db.session.add(listing)
            db.session.commit()
            listing_id = listing.id
            original_version = listing.version
        
        update_data = {
            'title': 'Updated Title',
            'price_per_night': 150.0,
            'version': original_version
        }
        
        response = self.app.put(f'/api/listings/{listing_id}',
                               data=json.dumps(update_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['title'], 'Updated Title')
        self.assertEqual(data['price_per_night'], 150.0)
        self.assertEqual(data['version'], original_version + 1)
    
    def test_delete_listing(self):
        """Test soft deleting a listing"""
        with app.app_context():
            listing = Listing(
                title='Test Listing',
                price_per_night=100.0,
                location='Test City',
                property_type='house',
                host_id='host_1'
            )
            db.session.add(listing)
            db.session.commit()
            listing_id = listing.id
        
        response = self.app.delete(f'/api/listings/{listing_id}')
        self.assertEqual(response.status_code, 200)
        
        # Verify listing is soft deleted
        with app.app_context():
            listing = Listing.query.get(listing_id)
            self.assertFalse(listing.is_active)
    
    def test_create_booking(self):
        """Test creating a booking"""
        with app.app_context():
            listing = Listing(
                title='Test Listing',
                price_per_night=100.0,
                location='Test City',
                property_type='house',
                host_id='host_1'
            )
            db.session.add(listing)
            db.session.commit()
            listing_id = listing.id
        
        booking_data = {
            'listing_id': listing_id,
            'guest_id': 'guest_123',
            'check_in': '2024-01-01',
            'check_out': '2024-01-03'
        }
        
        response = self.app.post('/api/bookings',
                                data=json.dumps(booking_data),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertEqual(data['listing_id'], listing_id)
        self.assertEqual(data['guest_id'], 'guest_123')
        self.assertEqual(data['total_price'], 200.0)  # 2 nights * $100
        self.assertEqual(data['status'], 'pending')
    
    def test_get_booking(self):
        """Test retrieving a booking"""
        with app.app_context():
            listing = Listing(
                title='Test Listing',
                price_per_night=100.0,
                location='Test City',
                property_type='house',
                host_id='host_1'
            )
            db.session.add(listing)
            db.session.commit()
            
            booking = Booking(
                listing_id=listing.id,
                guest_id='guest_123',
                check_in=date(2024, 1, 1),
                check_out=date(2024, 1, 3),
                total_price=200.0
            )
            db.session.add(booking)
            db.session.commit()
            booking_id = booking.id
        
        response = self.app.get(f'/api/bookings/{booking_id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['id'], booking_id)
        self.assertEqual(data['guest_id'], 'guest_123')
    
    def test_listing_filters(self):
        """Test listing filtering functionality"""
        with app.app_context():
            # Create test listings with different properties
            listing1 = Listing(
                title='Downtown Apartment',
                price_per_night=200.0,
                location='San Francisco',
                property_type='apartment',
                max_guests=2,
                host_id='host_1'
            )
            listing2 = Listing(
                title='Suburban House',
                price_per_night=150.0,
                location='Oakland',
                property_type='house',
                max_guests=6,
                host_id='host_2'
            )
            listing3 = Listing(
                title='Luxury Villa',
                price_per_night=500.0,
                location='Napa Valley',
                property_type='villa',
                max_guests=8,
                host_id='host_3'
            )
            
            db.session.add_all([listing1, listing2, listing3])
            db.session.commit()
        
        # Test location filter
        response = self.app.get('/api/listings?location=San Francisco')
        data = json.loads(response.data)
        self.assertEqual(len(data['listings']), 1)
        self.assertEqual(data['listings'][0]['location'], 'San Francisco')
        
        # Test property type filter
        response = self.app.get('/api/listings?property_type=house')
        data = json.loads(response.data)
        self.assertEqual(len(data['listings']), 1)
        self.assertEqual(data['listings'][0]['property_type'], 'house')
        
        # Test price range filter
        response = self.app.get('/api/listings?min_price=100&max_price=200')
        data = json.loads(response.data)
        self.assertEqual(len(data['listings']), 2)
        
        # Test max guests filter
        response = self.app.get('/api/listings?max_guests=4')
        data = json.loads(response.data)
        self.assertEqual(len(data['listings']), 2)  # House and Villa
    
    def test_pagination(self):
        """Test pagination functionality"""
        with app.app_context():
            # Create multiple listings
            listings = []
            for i in range(15):
                listing = Listing(
                    title=f'Test Listing {i}',
                    price_per_night=100.0 + i,
                    location='Test City',
                    property_type='house',
                    host_id=f'host_{i}'
                )
                listings.append(listing)
            
            db.session.add_all(listings)
            db.session.commit()
        
        # Test first page
        response = self.app.get('/api/listings?page=1&per_page=10')
        data = json.loads(response.data)
        self.assertEqual(len(data['listings']), 10)
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['per_page'], 10)
        self.assertEqual(data['pagination']['total'], 15)
        self.assertTrue(data['pagination']['has_next'])
        self.assertFalse(data['pagination']['has_prev'])
        
        # Test second page
        response = self.app.get('/api/listings?page=2&per_page=10')
        data = json.loads(response.data)
        self.assertEqual(len(data['listings']), 5)
        self.assertEqual(data['pagination']['page'], 2)
        self.assertFalse(data['pagination']['has_next'])
        self.assertTrue(data['pagination']['has_prev'])
    
    def test_metrics_endpoint(self):
        """Test system metrics endpoint"""
        with app.app_context():
            # Create test data
            listing = Listing(
                title='Test Listing',
                price_per_night=100.0,
                location='Test City',
                property_type='house',
                host_id='host_1'
            )
            db.session.add(listing)
            db.session.commit()
            
            booking = Booking(
                listing_id=listing.id,
                guest_id='guest_123',
                check_in=date(2024, 1, 1),
                check_out=date(2024, 1, 3),
                total_price=200.0
            )
            db.session.add(booking)
            db.session.commit()
        
        response = self.app.get('/api/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total_listings'], 1)
        self.assertEqual(data['active_listings'], 1)
        self.assertEqual(data['total_bookings'], 1)
        self.assertIn('timestamp', data)
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        # Test 404 for non-existent listing
        response = self.app.get('/api/listings/non-existent-id')
        self.assertEqual(response.status_code, 404)
        
        # Test 400 for invalid listing data
        invalid_data = {'title': 'Test'}  # Missing required fields
        response = self.app.post('/api/listings',
                                data=json.dumps(invalid_data),
                                content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Test 404 for non-existent booking
        response = self.app.get('/api/bookings/non-existent-id')
        self.assertEqual(response.status_code, 404)

class TestDistributedSystemsFeatures(unittest.TestCase):
    """Test distributed systems specific features"""
    
    def setUp(self):
        """Set up test environment"""
        self.db_fd, app.config['DATABASE_URL'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE_URL'])
    
    def test_optimistic_locking(self):
        """Test optimistic locking for concurrent updates"""
        with app.app_context():
            listing = Listing(
                title='Test Listing',
                price_per_night=100.0,
                location='Test City',
                property_type='house',
                host_id='host_1'
            )
            db.session.add(listing)
            db.session.commit()
            listing_id = listing.id
            original_version = listing.version
        
        # First update should succeed
        update_data1 = {
            'title': 'Updated Title 1',
            'version': original_version
        }
        
        response1 = self.app.put(f'/api/listings/{listing_id}',
                                data=json.dumps(update_data1),
                                content_type='application/json')
        self.assertEqual(response1.status_code, 200)
        
        # Second update with old version should fail
        update_data2 = {
            'title': 'Updated Title 2',
            'version': original_version  # Using old version
        }
        
        response2 = self.app.put(f'/api/listings/{listing_id}',
                                data=json.dumps(update_data2),
                                content_type='application/json')
        self.assertEqual(response2.status_code, 409)  # Conflict
    
    def test_data_consistency(self):
        """Test data consistency across operations"""
        with app.app_context():
            # Create listing
            listing = Listing(
                title='Consistency Test',
                price_per_night=100.0,
                location='Test City',
                property_type='house',
                host_id='host_1'
            )
            db.session.add(listing)
            db.session.commit()
            listing_id = listing.id
            
            # Create booking
            booking = Booking(
                listing_id=listing_id,
                guest_id='guest_123',
                check_in=date(2024, 1, 1),
                check_out=date(2024, 1, 3),
                total_price=200.0
            )
            db.session.add(booking)
            db.session.commit()
            booking_id = booking.id
        
        # Verify data consistency
        response = self.app.get(f'/api/listings/{listing_id}')
        listing_data = json.loads(response.data)
        
        response = self.app.get(f'/api/bookings/{booking_id}')
        booking_data = json.loads(response.data)
        
        self.assertEqual(booking_data['listing_id'], listing_data['id'])
        self.assertEqual(booking_data['total_price'], 200.0)
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            """Make a request to create a listing"""
            listing_data = {
                'title': f'Concurrent Test {threading.current_thread().ident}',
                'price_per_night': 100.0,
                'location': 'Test City',
                'property_type': 'house',
                'host_id': f'host_{threading.current_thread().ident}'
            }
            
            response = self.app.post('/api/listings',
                                    data=json.dumps(listing_data),
                                    content_type='application/json')
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        self.assertEqual(len(results), 5)
        self.assertTrue(all(status == 201 for status in results))

if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)
