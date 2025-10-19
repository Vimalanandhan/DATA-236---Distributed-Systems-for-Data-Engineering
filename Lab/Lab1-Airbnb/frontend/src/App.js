/*
Lab 1 Airbnb - Frontend React Application
Distributed Systems for Data Engineering (DATA 236)

This module implements a modern React frontend for the Airbnb listing management system
with responsive design, state management, and distributed systems integration.
*/

import React, { useState, useEffect } from 'react';
import './App.css';

// API Configuration for distributed systems
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Main App Component
function App() {
  const [listings, setListings] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentView, setCurrentView] = useState('homes');
  const [searchFilters, setSearchFilters] = useState({
    location: '',
    checkIn: '',
    checkOut: '',
    guests: ''
  });
  const [filters, setFilters] = useState({
    location: '',
    property_type: '',
    min_price: '',
    max_price: '',
    max_guests: ''
  });

  // Fetch listings from distributed backend
  const fetchListings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const queryParams = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) queryParams.append(key, value);
      });
      
      const response = await fetch(`${API_BASE_URL}/listings?${queryParams}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setListings(data.listings || []);
      
      console.log(`Fetched ${data.listings?.length || 0} listings`);
    } catch (err) {
      console.error('Error fetching listings:', err);
      setError('Failed to fetch listings. Please check if the backend service is running.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch bookings
  const fetchBookings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/bookings`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setBookings(data.bookings || []);
      
      console.log(`Fetched ${data.bookings?.length || 0} bookings`);
    } catch (err) {
      console.error('Error fetching bookings:', err);
      setError('Failed to fetch bookings. Please check if the backend service is running.');
    } finally {
      setLoading(false);
    }
  };

  // Create new listing
  const createListing = async (listingData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/listings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(listingData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const newListing = await response.json();
      setListings(prev => [...prev, newListing]);
      return newListing;
    } catch (err) {
      console.error('Error creating listing:', err);
      throw err;
    }
  };

  // Create new booking
  const createBooking = async (bookingData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookingData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const newBooking = await response.json();
      setBookings(prev => [...prev, newBooking]);
      return newBooking;
    } catch (err) {
      console.error('Error creating booking:', err);
      throw err;
    }
  };

  // Update listing
  const updateListing = async (id, updateData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/listings/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const updatedListing = await response.json();
      setListings(prev => 
        prev.map(listing => 
          listing.id === id ? updatedListing : listing
        )
      );
      return updatedListing;
    } catch (err) {
      console.error('Error updating listing:', err);
      throw err;
    }
  };

  // Delete listing
  const deleteListing = async (id) => {
    try {
      const response = await fetch(`${API_BASE_URL}/listings/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      setListings(prev => prev.filter(listing => listing.id !== id));
    } catch (err) {
      console.error('Error deleting listing:', err);
      throw err;
    }
  };

  // Health check for distributed systems monitoring
  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
      const health = await response.json();
      console.log('Backend health status:', health);
      return health;
    } catch (err) {
      console.error('Health check failed:', err);
      return null;
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchListings();
    checkHealth();
  }, []);

  // Re-fetch when filters change
  useEffect(() => {
    fetchListings();
  }, [filters]);

  return (
    <div className="App">
      {/* Airbnb-style Header */}
      <header className="airbnb-header">
        <div className="header-content">
          <div className="logo">
            <div className="airbnb-icon">🏠</div>
            <span className="airbnb-text">airbnb</span>
          </div>
          
          <nav className="main-nav">
            <button 
              className={`nav-item ${currentView === 'homes' ? 'active' : ''}`}
              onClick={() => setCurrentView('homes')}
            >
              <span className="nav-icon">🏠</span>
              <span>Homes</span>
            </button>
            <button 
              className={`nav-item ${currentView === 'experiences' ? 'active' : ''}`}
              onClick={() => setCurrentView('experiences')}
            >
              <span className="nav-icon">🎈</span>
              <span>Experiences</span>
              <span className="new-badge">NEW</span>
            </button>
            <button 
              className={`nav-item ${currentView === 'services' ? 'active' : ''}`}
              onClick={() => setCurrentView('services')}
            >
              <span className="nav-icon">🔔</span>
              <span>Services</span>
              <span className="new-badge">NEW</span>
            </button>
          </nav>

          <div className="header-actions">
            <button className="become-host-btn">Become a host</button>
            <button className="profile-btn">M</button>
            <button className="menu-btn">☰</button>
          </div>
        </div>
      </header>

      {/* Main Search Bar */}
      <div className="search-section">
        <div className="search-bar">
          <div className="search-field">
            <label>Where</label>
            <input 
              type="text" 
              placeholder="Search destinations"
              value={searchFilters.location}
              onChange={(e) => setSearchFilters(prev => ({ ...prev, location: e.target.value }))}
            />
          </div>
          <div className="search-field">
            <label>Check in</label>
            <input 
              type="date" 
              placeholder="Add dates"
              value={searchFilters.checkIn}
              onChange={(e) => setSearchFilters(prev => ({ ...prev, checkIn: e.target.value }))}
            />
          </div>
          <div className="search-field">
            <label>Check out</label>
            <input 
              type="date" 
              placeholder="Add dates"
              value={searchFilters.checkOut}
              onChange={(e) => setSearchFilters(prev => ({ ...prev, checkOut: e.target.value }))}
            />
          </div>
          <div className="search-field">
            <label>Who</label>
            <input 
              type="text" 
              placeholder="Add guests"
              value={searchFilters.guests}
              onChange={(e) => setSearchFilters(prev => ({ ...prev, guests: e.target.value }))}
            />
          </div>
          <button className="search-btn">
            <span className="search-icon">🔍</span>
          </button>
        </div>
      </div>

      {/* Content Sections */}

      <main className="App-main">
        {/* Error Display */}
        {error && (
          <div className="error-message">
            <span className="warning-icon">⚠️</span>
            <p>{error}</p>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading...</p>
          </div>
        )}

        {/* Homes View */}
        {currentView === 'homes' && (
          <HomesView 
            listings={listings}
            filters={filters}
            setFilters={setFilters}
            onUpdateListing={updateListing}
            onDeleteListing={deleteListing}
            onCreateBooking={createBooking}
          />
        )}

        {/* Experiences View */}
        {currentView === 'experiences' && (
          <ExperiencesView />
        )}

        {/* Services View */}
        {currentView === 'services' && (
          <ServicesView />
        )}
      </main>

      <footer className="App-footer">
        <p>Airbnb - Distributed Systems Implementation</p>
        <p>Built with React, Flask, and distributed systems principles</p>
      </footer>
    </div>
  );
}

// Homes View Component (Airbnb-style property listings)
function HomesView({ listings, filters, setFilters, onUpdateListing, onDeleteListing, onCreateBooking }) {
  const [editingListing, setEditingListing] = useState(null);
  const [bookingForm, setBookingForm] = useState({ listingId: '', guestId: '', checkIn: '', checkOut: '' });

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleEditListing = (listing) => {
    setEditingListing(listing);
  };

  const handleSaveEdit = async (updatedData) => {
    try {
      await onUpdateListing(editingListing.id, updatedData);
      setEditingListing(null);
    } catch (err) {
      alert('Failed to update listing');
    }
  };

  const handleDeleteListing = async (id) => {
    if (window.confirm('Are you sure you want to delete this listing?')) {
      try {
        await onDeleteListing(id);
      } catch (err) {
        alert('Failed to delete listing');
      }
    }
  };

  const handleCreateBooking = async (e) => {
    e.preventDefault();
    try {
      await onCreateBooking(bookingForm);
      setBookingForm({ listingId: '', guestId: '', checkIn: '', checkOut: '' });
      alert('Booking created successfully!');
    } catch (err) {
      alert('Failed to create booking');
    }
  };

  return (
    <div className="homes-view">
      {/* Popular homes section */}
      <div className="section-header">
        <h2>Popular homes in Los Angeles</h2>
        <span className="section-arrow">></span>
      </div>
      
      {/* Filters */}
      <div className="filters">
        <h3>Filter Listings</h3>
        <div className="filter-grid">
          <input
            type="text"
            placeholder="Location"
            value={filters.location}
            onChange={(e) => handleFilterChange('location', e.target.value)}
          />
          <select
            value={filters.property_type}
            onChange={(e) => handleFilterChange('property_type', e.target.value)}
          >
            <option value="">All Property Types</option>
            <option value="apartment">Apartment</option>
            <option value="house">House</option>
            <option value="condo">Condo</option>
            <option value="villa">Villa</option>
            <option value="studio">Studio</option>
          </select>
          <input
            type="number"
            placeholder="Min Price"
            value={filters.min_price}
            onChange={(e) => handleFilterChange('min_price', e.target.value)}
          />
          <input
            type="number"
            placeholder="Max Price"
            value={filters.max_price}
            onChange={(e) => handleFilterChange('max_price', e.target.value)}
          />
          <input
            type="number"
            placeholder="Max Guests"
            value={filters.max_guests}
            onChange={(e) => handleFilterChange('max_guests', e.target.value)}
          />
        </div>
      </div>

      {/* Homes Grid */}
      <div className="homes-grid">
        {listings.map(listing => (
          <div key={listing.id} className="listing-card">
            <div className="listing-image">
              <div className="guest-favorite-tag">Guest favorite</div>
              <button className="favorite-btn">♡</button>
            </div>
            
            <div className="listing-content">
              <h3>{listing.title}</h3>
              <p className="listing-location">{listing.location}</p>
              <p className="listing-price">${listing.price_per_night}/night</p>
              <div className="listing-rating">
                <span className="stars">★</span>
                <span className="rating">4.9</span>
              </div>
              
              <div className="listing-details">
                <p><strong>Type:</strong> {listing.property_type}</p>
                <p><strong>Guests:</strong> {listing.max_guests}</p>
                <p><strong>Bedrooms:</strong> {listing.bedrooms}</p>
                <p><strong>Bathrooms:</strong> {listing.bathrooms}</p>
                {listing.description && <p><strong>Description:</strong> {listing.description}</p>}
              </div>

              <div className="listing-actions">
                <button onClick={() => handleEditListing(listing)} className="edit-btn">✏️ Edit</button>
                <button onClick={() => handleDeleteListing(listing.id)} className="delete-btn">🗑️ Delete</button>
              </div>

              {/* Booking Form */}
              <div className="booking-form">
                <h4>Book This Listing</h4>
                <form onSubmit={handleCreateBooking}>
                  <input
                    type="hidden"
                    value={listing.id}
                    onChange={(e) => setBookingForm(prev => ({ ...prev, listingId: e.target.value }))}
                  />
                  <input
                    type="text"
                    placeholder="Guest ID"
                    value={bookingForm.guestId}
                    onChange={(e) => setBookingForm(prev => ({ ...prev, guestId: e.target.value }))}
                    required
                  />
                  <input
                    type="date"
                    placeholder="Check-in Date"
                    value={bookingForm.checkIn}
                    onChange={(e) => setBookingForm(prev => ({ ...prev, checkIn: e.target.value }))}
                    required
                  />
                  <input
                    type="date"
                    placeholder="Check-out Date"
                    value={bookingForm.checkOut}
                    onChange={(e) => setBookingForm(prev => ({ ...prev, checkOut: e.target.value }))}
                    required
                  />
                  <button type="submit" className="book-btn">Book Now</button>
                </form>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Modal */}
      {editingListing && (
        <EditListingModal
          listing={editingListing}
          onSave={handleSaveEdit}
          onCancel={() => setEditingListing(null)}
        />
      )}
    </div>
  );
}

// Experiences View Component
function ExperiencesView() {
  const experiences = [
    {
      id: 1,
      title: "Turkish Mosaic Lamp Workshops",
      price: 89,
      rating: 4.93,
      image: "🎨",
      date: "Sun 10 AM"
    },
    {
      id: 2,
      title: "Rug Tufting Workshop",
      price: 99,
      rating: 4.96,
      image: "🧶",
      date: "Sat 9 AM"
    },
    {
      id: 3,
      title: "Experience whale watching with a Naturalist",
      price: 185,
      rating: 4.94,
      image: "🐋",
      date: "Sun 8 AM"
    },
    {
      id: 4,
      title: "Explore Silicon Valley's landmarks",
      price: 150,
      rating: 4.91,
      image: "🏢",
      date: "Sat 2 PM"
    },
    {
      id: 5,
      title: "Take surf lessons with small group coaching",
      price: 139,
      rating: 4.9,
      image: "🏄",
      date: "Sun 9 AM"
    },
    {
      id: 6,
      title: "Unwind at a Santa Cruz Mountains spa retreat",
      price: 125,
      rating: 4.95,
      image: "🧘",
      date: "Sat 11 AM"
    },
    {
      id: 7,
      title: "Connect with rescue horses in a peaceful pasture",
      price: 65,
      rating: 4.99,
      image: "🐴",
      date: "Sun 3 PM"
    }
  ];

  return (
    <div className="experiences-view">
      {/* Experiences this weekend */}
      <div className="section-header">
        <h2>Experiences this weekend</h2>
        <span className="section-arrow">></span>
      </div>
      
      <div className="experiences-grid">
        {experiences.map(experience => (
          <div key={experience.id} className="experience-card">
            <div className="experience-image">
              <div className="experience-date">{experience.date}</div>
              <button className="favorite-btn">♡</button>
              <div className="experience-emoji">{experience.image}</div>
            </div>
            
            <div className="experience-content">
              <h3>{experience.title}</h3>
              <p className="experience-price">From ${experience.price}/guest</p>
              <div className="experience-rating">
                <span className="stars">★</span>
                <span className="rating">{experience.rating}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* All experiences section */}
      <div className="section-header">
        <h2>All experiences in San Jose</h2>
        <span className="section-arrow">></span>
      </div>
      
      <div className="experiences-grid">
        {experiences.map(experience => (
          <div key={`all-${experience.id}`} className="experience-card">
            <div className="experience-image">
              <div className="popular-tag">Popular</div>
              <button className="favorite-btn">♡</button>
              <div className="experience-emoji">{experience.image}</div>
            </div>
            
            <div className="experience-content">
              <h3>{experience.title}</h3>
              <p className="experience-price">From ${experience.price}/guest</p>
              <div className="experience-rating">
                <span className="stars">★</span>
                <span className="rating">{experience.rating}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Services View Component
function ServicesView() {
  const serviceCategories = [
    { name: "Photography", available: 10, image: "📸" },
    { name: "Chefs", available: 1, image: "👨‍🍳" },
    { name: "Prepared meals", available: 1, image: "🍽️" },
    { name: "Massage", available: 1, image: "💆" },
    { name: "Training", available: 3, image: "💪" },
    { name: "Hair", available: 1, image: "💇" },
    { name: "Spa treatments", available: 2, image: "🧖" },
    { name: "Catering", available: 2, image: "🍴" },
    { name: "Makeup", available: 0, image: "💄", comingSoon: true },
    { name: "Nails", available: 0, image: "💅", comingSoon: true }
  ];

  const photographyServices = [
    { name: "Classically beautiful photos by Deanna", price: 425, image: "📷" },
    { name: "Bay Area Photo Session", price: 400, image: "📸" },
    { name: "Say it in pictures by Marcus", price: 250, image: "🎭" },
    { name: "Photography by Lighting Up Your Life Studio", price: 350, image: "💡" },
    { name: "Handcrafted moments by Christopher", price: 1500, image: "🎨" },
    { name: "Family and friends photos by Chris", price: 325, image: "👨‍👩‍👧‍👦" },
    { name: "Bay area photography by Jennifer", price: 295, image: "🌉" }
  ];

  return (
    <div className="services-view">
      <div className="section-header">
        <h2>Services in San Jose</h2>
      </div>
      
      {/* Service Categories */}
      <div className="service-categories">
        {serviceCategories.map((service, index) => (
          <div key={index} className="service-category-card">
            <div className="service-category-image">
              <div className="service-emoji">{service.image}</div>
            </div>
            <div className="service-category-content">
              <h3>{service.name}</h3>
              <p>{service.comingSoon ? "Coming soon" : `${service.available} available`}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Photography Services */}
      <div className="section-header">
        <h2>Photography</h2>
        <span className="section-arrow">></span>
      </div>
      
      <div className="photography-grid">
        {photographyServices.map((service, index) => (
          <div key={index} className="photography-card">
            <div className="photography-image">
              <button className="favorite-btn">♡</button>
              <div className="photography-emoji">{service.image}</div>
            </div>
            
            <div className="photography-content">
              <h3>{service.name}</h3>
              <p className="photography-price">From ${service.price} / group</p>
            </div>
          </div>
        ))}
      </div>

      {/* More services section */}
      <div className="section-header">
        <h2>More services in San Jose</h2>
        <span className="section-arrow">></span>
      </div>
    </div>
  );
}

// Create Listing View Component
function CreateListingView({ onCreateListing }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price_per_night: '',
    location: '',
    latitude: '',
    longitude: '',
    property_type: '',
    amenities: [],
    max_guests: 1,
    bedrooms: 1,
    bathrooms: 1.0,
    host_id: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await onCreateListing(formData);
      alert('Listing created successfully!');
      setFormData({
        title: '',
        description: '',
        price_per_night: '',
        location: '',
        latitude: '',
        longitude: '',
        property_type: '',
        amenities: [],
        max_guests: 1,
        bedrooms: 1,
        bathrooms: 1.0,
        host_id: ''
      });
    } catch (err) {
      alert('Failed to create listing');
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="create-listing-view">
      <h2>➕ Create New Listing</h2>
      
      <form onSubmit={handleSubmit} className="create-form">
        <div className="form-group">
          <label>Title *</label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => handleChange('title', e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label>Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            rows="3"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Price per Night *</label>
            <input
              type="number"
              step="0.01"
              value={formData.price_per_night}
              onChange={(e) => handleChange('price_per_night', e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Location *</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => handleChange('location', e.target.value)}
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Property Type *</label>
            <select
              value={formData.property_type}
              onChange={(e) => handleChange('property_type', e.target.value)}
              required
            >
              <option value="">Select Type</option>
              <option value="apartment">Apartment</option>
              <option value="house">House</option>
              <option value="condo">Condo</option>
              <option value="villa">Villa</option>
              <option value="studio">Studio</option>
            </select>
          </div>

          <div className="form-group">
            <label>Host ID *</label>
            <input
              type="text"
              value={formData.host_id}
              onChange={(e) => handleChange('host_id', e.target.value)}
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Max Guests</label>
            <input
              type="number"
              min="1"
              value={formData.max_guests}
              onChange={(e) => handleChange('max_guests', parseInt(e.target.value))}
            />
          </div>

          <div className="form-group">
            <label>Bedrooms</label>
            <input
              type="number"
              min="1"
              value={formData.bedrooms}
              onChange={(e) => handleChange('bedrooms', parseInt(e.target.value))}
            />
          </div>

          <div className="form-group">
            <label>Bathrooms</label>
            <input
              type="number"
              step="0.5"
              min="1"
              value={formData.bathrooms}
              onChange={(e) => handleChange('bathrooms', parseFloat(e.target.value))}
            />
          </div>
        </div>

        <button type="submit" className="submit-btn">Create Listing</button>
      </form>
    </div>
  );
}

// Edit Listing Modal Component
function EditListingModal({ listing, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    title: listing.title,
    description: listing.description || '',
    price_per_night: listing.price_per_night,
    location: listing.location,
    property_type: listing.property_type,
    max_guests: listing.max_guests,
    bedrooms: listing.bedrooms,
    bathrooms: listing.bathrooms,
    is_active: listing.is_active,
    version: listing.version
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Edit Listing</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              rows="3"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Price per Night</label>
              <input
                type="number"
                step="0.01"
                value={formData.price_per_night}
                onChange={(e) => handleChange('price_per_night', parseFloat(e.target.value))}
                required
              />
            </div>

            <div className="form-group">
              <label>Location</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => handleChange('location', e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Property Type</label>
              <select
                value={formData.property_type}
                onChange={(e) => handleChange('property_type', e.target.value)}
                required
              >
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="condo">Condo</option>
                <option value="villa">Villa</option>
                <option value="studio">Studio</option>
              </select>
            </div>

            <div className="form-group">
              <label>Max Guests</label>
              <input
                type="number"
                min="1"
                value={formData.max_guests}
                onChange={(e) => handleChange('max_guests', parseInt(e.target.value))}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Bedrooms</label>
              <input
                type="number"
                min="1"
                value={formData.bedrooms}
                onChange={(e) => handleChange('bedrooms', parseInt(e.target.value))}
              />
            </div>

            <div className="form-group">
              <label>Bathrooms</label>
              <input
                type="number"
                step="0.5"
                min="1"
                value={formData.bathrooms}
                onChange={(e) => handleChange('bathrooms', parseFloat(e.target.value))}
              />
            </div>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => handleChange('is_active', e.target.checked)}
              />
              Active Listing
            </label>
          </div>

          <div className="modal-actions">
            <button type="submit" className="save-btn">Save Changes</button>
            <button type="button" onClick={onCancel} className="cancel-btn">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default App;
