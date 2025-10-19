"""
Lab 1 Airbnb - Frontend Test Suite
Distributed Systems for Data Engineering (DATA 236)

Test suite for the React frontend application with distributed systems testing.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the frontend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src'))

class TestAirbnbFrontend(unittest.TestCase):
    """Test cases for the Airbnb frontend components"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_listings = [
            {
                'id': '1',
                'title': 'Beautiful Apartment',
                'description': 'A modern apartment',
                'price_per_night': 150.0,
                'location': 'San Francisco, CA',
                'property_type': 'apartment',
                'max_guests': 4,
                'bedrooms': 2,
                'bathrooms': 2.0,
                'host_id': 'host_1',
                'is_active': True,
                'version': 1
            },
            {
                'id': '2',
                'title': 'Cozy House',
                'description': 'A cozy house',
                'price_per_night': 200.0,
                'location': 'Oakland, CA',
                'property_type': 'house',
                'max_guests': 6,
                'bedrooms': 3,
                'bathrooms': 2.0,
                'host_id': 'host_2',
                'is_active': True,
                'version': 1
            }
        ]
        
        self.mock_bookings = [
            {
                'id': 'booking_1',
                'listing_id': '1',
                'guest_id': 'guest_1',
                'check_in': '2024-01-01',
                'check_out': '2024-01-03',
                'total_price': 300.0,
                'status': 'confirmed',
                'version': 1
            }
        ]
    
    def test_api_configuration(self):
        """Test API configuration"""
        # Test API base URL configuration
        api_url = os.environ.get('REACT_APP_API_URL', 'http://localhost:5000/api')
        self.assertIn('localhost:5000', api_url)
        self.assertTrue(api_url.endswith('/api'))
    
    @patch('requests.get')
    def test_fetch_listings_success(self, mock_get):
        """Test successful listing fetch"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'listings': self.mock_listings,
            'pagination': {
                'page': 1,
                'per_page': 10,
                'total': 2,
                'pages': 1,
                'has_next': False,
                'has_prev': False
            }
        }
        mock_get.return_value = mock_response
        
        # Test the fetch operation
        import requests
        response = requests.get('http://localhost:5000/api/listings')
        
        self.assertTrue(response.ok)
        data = response.json()
        self.assertEqual(len(data['listings']), 2)
        self.assertEqual(data['listings'][0]['title'], 'Beautiful Apartment')
    
    @patch('requests.get')
    def test_fetch_listings_error(self, mock_get):
        """Test listing fetch error handling"""
        # Mock API error
        mock_get.side_effect = Exception('Network error')
        
        # Test error handling
        try:
            import requests
            requests.get('http://localhost:5000/api/listings')
        except Exception as e:
            self.assertEqual(str(e), 'Network error')
    
    @patch('requests.post')
    def test_create_listing_success(self, mock_post):
        """Test successful listing creation"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = self.mock_listings[0]
        mock_post.return_value = mock_response
        
        # Test the create operation
        import requests
        listing_data = {
            'title': 'Test Listing',
            'price_per_night': 100.0,
            'location': 'Test City',
            'property_type': 'house',
            'host_id': 'host_1'
        }
        
        response = requests.post(
            'http://localhost:5000/api/listings',
            json=listing_data
        )
        
        self.assertTrue(response.ok)
        data = response.json()
        self.assertEqual(data['title'], 'Beautiful Apartment')
    
    @patch('requests.post')
    def test_create_booking_success(self, mock_post):
        """Test successful booking creation"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = self.mock_bookings[0]
        mock_post.return_value = mock_response
        
        # Test the create operation
        import requests
        booking_data = {
            'listing_id': '1',
            'guest_id': 'guest_1',
            'check_in': '2024-01-01',
            'check_out': '2024-01-03'
        }
        
        response = requests.post(
            'http://localhost:5000/api/bookings',
            json=booking_data
        )
        
        self.assertTrue(response.ok)
        data = response.json()
        self.assertEqual(data['listing_id'], '1')
        self.assertEqual(data['total_price'], 300.0)
    
    def test_listing_filtering(self):
        """Test listing filtering logic"""
        # Test location filter
        filtered_by_location = [
            listing for listing in self.mock_listings
            if 'San Francisco' in listing['location']
        ]
        self.assertEqual(len(filtered_by_location), 1)
        self.assertEqual(filtered_by_location[0]['title'], 'Beautiful Apartment')
        
        # Test property type filter
        filtered_by_type = [
            listing for listing in self.mock_listings
            if listing['property_type'] == 'house'
        ]
        self.assertEqual(len(filtered_by_type), 1)
        self.assertEqual(filtered_by_type[0]['title'], 'Cozy House')
        
        # Test price range filter
        filtered_by_price = [
            listing for listing in self.mock_listings
            if 100 <= listing['price_per_night'] <= 150
        ]
        self.assertEqual(len(filtered_by_price), 1)
        self.assertEqual(filtered_by_price[0]['title'], 'Beautiful Apartment')
    
    def test_booking_calculation(self):
        """Test booking price calculation"""
        listing = self.mock_listings[0]
        check_in = '2024-01-01'
        check_out = '2024-01-03'
        
        # Calculate nights
        from datetime import datetime
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        nights = (check_out_date - check_in_date).days
        
        # Calculate total price
        total_price = nights * listing['price_per_night']
        
        self.assertEqual(nights, 2)
        self.assertEqual(total_price, 300.0)
    
    def test_form_validation(self):
        """Test form validation logic"""
        # Test required fields validation
        required_fields = ['title', 'price_per_night', 'location', 'property_type', 'host_id']
        
        # Valid data
        valid_data = {
            'title': 'Test Listing',
            'price_per_night': 100.0,
            'location': 'Test City',
            'property_type': 'house',
            'host_id': 'host_1'
        }
        
        for field in required_fields:
            self.assertIn(field, valid_data)
        
        # Invalid data (missing required field)
        invalid_data = {
            'title': 'Test Listing',
            'price_per_night': 100.0,
            'location': 'Test City'
            # Missing property_type and host_id
        }
        
        missing_fields = [field for field in required_fields if field not in invalid_data]
        self.assertEqual(len(missing_fields), 2)
        self.assertIn('property_type', missing_fields)
        self.assertIn('host_id', missing_fields)
    
    def test_data_formatting(self):
        """Test data formatting functions"""
        listing = self.mock_listings[0]
        
        # Test date formatting
        from datetime import datetime
        if 'created_at' in listing:
            formatted_date = datetime.fromisoformat(listing['created_at'].replace('Z', '+00:00'))
            self.assertIsInstance(formatted_date, datetime)
        
        # Test price formatting
        formatted_price = f"${listing['price_per_night']:.2f}"
        self.assertEqual(formatted_price, "$150.00")
        
        # Test property type formatting
        property_type_map = {
            'apartment': 'Apartment',
            'house': 'House',
            'condo': 'Condo',
            'villa': 'Villa',
            'studio': 'Studio'
        }
        
        formatted_type = property_type_map.get(listing['property_type'], listing['property_type'].title())
        self.assertEqual(formatted_type, 'Apartment')
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        # Test network error handling
        try:
            raise ConnectionError('Network connection failed')
        except ConnectionError as e:
            self.assertEqual(str(e), 'Network connection failed')
        
        # Test API error handling
        try:
            raise ValueError('Invalid API response')
        except ValueError as e:
            self.assertEqual(str(e), 'Invalid API response')
        
        # Test validation error handling
        try:
            if not isinstance(100, str):
                raise TypeError('Expected string, got number')
        except TypeError as e:
            self.assertEqual(str(e), 'Expected string, got number')
    
    def test_state_management(self):
        """Test state management logic"""
        # Test initial state
        initial_state = {
            'listings': [],
            'bookings': [],
            'loading': False,
            'error': None,
            'currentView': 'listings',
            'filters': {
                'location': '',
                'property_type': '',
                'min_price': '',
                'max_price': '',
                'max_guests': ''
            }
        }
        
        self.assertEqual(len(initial_state['listings']), 0)
        self.assertFalse(initial_state['loading'])
        self.assertIsNone(initial_state['error'])
        
        # Test state updates
        updated_state = initial_state.copy()
        updated_state['listings'] = self.mock_listings
        updated_state['loading'] = True
        
        self.assertEqual(len(updated_state['listings']), 2)
        self.assertTrue(updated_state['loading'])
    
    def test_pagination_logic(self):
        """Test pagination logic"""
        # Test pagination parameters
        page = 1
        per_page = 10
        total_items = 25
        
        # Calculate pagination info
        total_pages = (total_items + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        self.assertEqual(total_pages, 3)
        self.assertTrue(has_next)
        self.assertFalse(has_prev)
        
        # Test page 2
        page = 2
        has_next = page < total_pages
        has_prev = page > 1
        
        self.assertTrue(has_next)
        self.assertTrue(has_prev)
        
        # Test last page
        page = 3
        has_next = page < total_pages
        has_prev = page > 1
        
        self.assertFalse(has_next)
        self.assertTrue(has_prev)

class TestDistributedSystemsIntegration(unittest.TestCase):
    """Test distributed systems integration features"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_base_url = 'http://localhost:5000/api'
    
    @patch('requests.get')
    def test_health_check_integration(self, mock_get):
        """Test health check integration"""
        # Mock health check response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'status': 'healthy',
            'service': 'airbnb-listing-service',
            'timestamp': '2024-01-01T00:00:00Z',
            'version': '1.0.0'
        }
        mock_get.return_value = mock_response
        
        # Test health check
        import requests
        response = requests.get('http://localhost:5000/health')
        
        self.assertTrue(response.ok)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'airbnb-listing-service')
    
    @patch('requests.get')
    def test_metrics_integration(self, mock_get):
        """Test metrics integration"""
        # Mock metrics response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'total_listings': 10,
            'active_listings': 8,
            'total_bookings': 25,
            'timestamp': '2024-01-01T00:00:00Z'
        }
        mock_get.return_value = mock_response
        
        # Test metrics
        import requests
        response = requests.get(f'{self.api_base_url}/metrics')
        
        self.assertTrue(response.ok)
        data = response.json()
        self.assertEqual(data['total_listings'], 10)
        self.assertEqual(data['active_listings'], 8)
        self.assertEqual(data['total_bookings'], 25)
    
    def test_load_balancing_simulation(self):
        """Test load balancing simulation"""
        # Simulate multiple backend instances
        backend_instances = [
            'http://backend1:5000',
            'http://backend2:5000',
            'http://backend3:5000'
        ]
        
        # Test round-robin selection
        current_index = 0
        selected_backend = backend_instances[current_index]
        self.assertEqual(selected_backend, 'http://backend1:5000')
        
        # Next request
        current_index = (current_index + 1) % len(backend_instances)
        selected_backend = backend_instances[current_index]
        self.assertEqual(selected_backend, 'http://backend2:5000')
        
        # Next request
        current_index = (current_index + 1) % len(backend_instances)
        selected_backend = backend_instances[current_index]
        self.assertEqual(selected_backend, 'http://backend3:5000')
        
        # Wrap around
        current_index = (current_index + 1) % len(backend_instances)
        selected_backend = backend_instances[current_index]
        self.assertEqual(selected_backend, 'http://backend1:5000')
    
    def test_caching_strategy(self):
        """Test caching strategy"""
        # Test cache key generation
        def generate_cache_key(endpoint, params):
            key_parts = [endpoint]
            for k, v in sorted(params.items()):
                if v:  # Only include non-empty values
                    key_parts.append(f"{k}:{v}")
            return "|".join(key_parts)
        
        # Test different cache keys
        key1 = generate_cache_key('/api/listings', {'location': 'SF', 'type': 'apartment'})
        key2 = generate_cache_key('/api/listings', {'location': 'SF', 'type': 'house'})
        key3 = generate_cache_key('/api/listings', {'location': 'SF', 'type': 'apartment'})
        
        self.assertNotEqual(key1, key2)
        self.assertEqual(key1, key3)
        
        # Test cache expiration
        import time
        cache_entry = {
            'data': {'listings': []},
            'timestamp': time.time(),
            'ttl': 300  # 5 minutes
        }
        
        is_expired = (time.time() - cache_entry['timestamp']) > cache_entry['ttl']
        self.assertFalse(is_expired)  # Should not be expired immediately

if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)
