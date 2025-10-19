#!/usr/bin/env python3
"""
Sample Data Generator for Lab 1 Airbnb
Adds sample listings to the database for testing
"""

import requests
import json
import time

# API base URL
API_BASE_URL = 'http://localhost:5000/api'

# Sample listings data
sample_listings = [
    {
        "title": "Cozy Studio in Downtown LA",
        "description": "Beautiful studio apartment in the heart of downtown Los Angeles with modern amenities and city views.",
        "price_per_night": 115.0,
        "location": "Los Angeles, CA",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "property_type": "apartment",
        "amenities": ["WiFi", "Kitchen", "Air Conditioning", "TV"],
        "max_guests": 2,
        "bedrooms": 1,
        "bathrooms": 1.0,
        "host_id": "host_001",
        "is_active": True
    },
    {
        "title": "Modern House in Burbank",
        "description": "Spacious modern house with a beautiful garden and pool. Perfect for families.",
        "price_per_night": 229.0,
        "location": "Burbank, CA",
        "latitude": 34.1808,
        "longitude": -118.3090,
        "property_type": "house",
        "amenities": ["WiFi", "Kitchen", "Pool", "Garden", "Parking"],
        "max_guests": 6,
        "bedrooms": 3,
        "bathrooms": 2.0,
        "host_id": "host_002",
        "is_active": True
    },
    {
        "title": "Luxury Condo in Santa Monica",
        "description": "High-end condo with ocean views and premium amenities. Walking distance to the beach.",
        "price_per_night": 210.0,
        "location": "Santa Monica, CA",
        "latitude": 34.0195,
        "longitude": -118.4912,
        "property_type": "condo",
        "amenities": ["WiFi", "Kitchen", "Ocean View", "Gym", "Concierge"],
        "max_guests": 4,
        "bedrooms": 2,
        "bathrooms": 2.0,
        "host_id": "host_003",
        "is_active": True
    },
    {
        "title": "Charming Guesthouse in Hawthorne",
        "description": "Quaint guesthouse with vintage charm and modern comforts. Private entrance and garden.",
        "price_per_night": 291.0,
        "location": "Hawthorne, CA",
        "latitude": 33.9164,
        "longitude": -118.3526,
        "property_type": "house",
        "amenities": ["WiFi", "Kitchen", "Garden", "Private Entrance"],
        "max_guests": 3,
        "bedrooms": 1,
        "bathrooms": 1.0,
        "host_id": "host_004",
        "is_active": True
    },
    {
        "title": "Elegant Guest Suite in LA",
        "description": "Sophisticated guest suite with premium finishes and excellent location.",
        "price_per_night": 281.0,
        "location": "Los Angeles, CA",
        "latitude": 34.0736,
        "longitude": -118.4004,
        "property_type": "apartment",
        "amenities": ["WiFi", "Kitchen", "Air Conditioning", "TV", "Balcony"],
        "max_guests": 2,
        "bedrooms": 1,
        "bathrooms": 1.0,
        "host_id": "host_005",
        "is_active": True
    },
    {
        "title": "Beachfront Villa in San Diego",
        "description": "Stunning beachfront villa with direct beach access and panoramic ocean views.",
        "price_per_night": 274.0,
        "location": "San Diego, CA",
        "latitude": 32.7157,
        "longitude": -117.1611,
        "property_type": "villa",
        "amenities": ["WiFi", "Kitchen", "Beach Access", "Pool", "Ocean View"],
        "max_guests": 8,
        "bedrooms": 4,
        "bathrooms": 3.0,
        "host_id": "host_006",
        "is_active": True
    },
    {
        "title": "Urban Loft in Brooklyn",
        "description": "Trendy loft in Brooklyn with exposed brick walls and industrial design.",
        "price_per_night": 177.0,
        "location": "Brooklyn, NY",
        "latitude": 40.6782,
        "longitude": -73.9442,
        "property_type": "apartment",
        "amenities": ["WiFi", "Kitchen", "Exposed Brick", "High Ceilings"],
        "max_guests": 3,
        "bedrooms": 1,
        "bathrooms": 1.0,
        "host_id": "host_007",
        "is_active": True
    },
    {
        "title": "Mountain Cabin in Aspen",
        "description": "Rustic mountain cabin with fireplace and stunning mountain views.",
        "price_per_night": 334.0,
        "location": "Aspen, CO",
        "latitude": 39.1911,
        "longitude": -106.8175,
        "property_type": "house",
        "amenities": ["WiFi", "Kitchen", "Fireplace", "Mountain View", "Hot Tub"],
        "max_guests": 6,
        "bedrooms": 3,
        "bathrooms": 2.0,
        "host_id": "host_008",
        "is_active": True
    }
]

def add_sample_listings():
    """Add sample listings to the database"""
    print("Adding sample listings to the database...")
    
    for i, listing in enumerate(sample_listings, 1):
        try:
            response = requests.post(
                f"{API_BASE_URL}/listings",
                json=listing,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                print(f"✅ Added listing {i}: {listing['title']}")
            else:
                print(f"❌ Failed to add listing {i}: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error adding listing {i}: {e}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    print("\nSample listings added! Check your application at http://localhost:3000")

if __name__ == "__main__":
    add_sample_listings()
