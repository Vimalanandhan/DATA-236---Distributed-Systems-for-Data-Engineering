# Lab 1 Airbnb - Distributed Systems Implementation

**Course:** DATA 236 - Distributed Systems for Data Engineering  
**Assignment:** Lab 1 Airbnb  
**Author:** Student Implementation  

## 📋 Overview

This lab implements a comprehensive Airbnb-like listing management system using distributed systems principles. The application consists of a Flask backend API, React frontend, and Docker containerization with microservices architecture.

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Frontend      │    │   Backend API   │
│   (Nginx)       │◄──►│   (React)       │◄──►│   (Flask)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Redis Cache    │    │   Database      │
│   (Prometheus)  │    │   (Sessions)    │    │   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Distributed Systems Features

- **Microservices Architecture**: Separate frontend and backend services
- **Load Balancing**: Nginx-based load balancing with health checks
- **Horizontal Scaling**: Containerized services for easy scaling
- **Service Discovery**: Health check endpoints for service monitoring
- **Data Consistency**: Optimistic locking for concurrent updates
- **Caching**: Redis integration for session management
- **Monitoring**: Prometheus metrics collection

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Node.js 18+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Lab1-Airbnb
   ```

2. **Start the application with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Load Balancer: http://localhost:80
   - Monitoring: http://localhost:9090

### Manual Setup (Development)

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

## 📁 Project Structure

```
Lab1-Airbnb/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container config
├── frontend/
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   └── App.css           # Styling
│   ├── package.json          # Node.js dependencies
│   └── Dockerfile           # Frontend container config
├── nginx/
│   └── nginx.conf           # Load balancer configuration
├── tests/
│   ├── test_backend.py      # Backend test suite
│   └── test_frontend.py     # Frontend test suite
├── docker-compose.yml       # Multi-container orchestration
└── README.md               # This file
```

## 🔧 API Endpoints

### Listings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/listings` | Get all listings with pagination and filtering |
| GET | `/api/listings/{id}` | Get specific listing by ID |
| POST | `/api/listings` | Create new listing |
| PUT | `/api/listings/{id}` | Update listing (with optimistic locking) |
| DELETE | `/api/listings/{id}` | Soft delete listing |

### Bookings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/bookings/{id}` | Get specific booking by ID |
| POST | `/api/bookings` | Create new booking |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check for load balancer |
| GET | `/api/metrics` | System metrics for monitoring |

### Query Parameters

**Listings Filtering:**
- `location`: Filter by location (partial match)
- `property_type`: Filter by property type
- `min_price`: Minimum price per night
- `max_price`: Maximum price per night
- `max_guests`: Minimum guest capacity
- `page`: Page number for pagination
- `per_page`: Items per page (max 100)

## 🗄️ Database Schema

### Listings Table

```sql
CREATE TABLE listings (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    price_per_night FLOAT NOT NULL,
    location VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    property_type VARCHAR(50) NOT NULL,
    amenities JSON,
    max_guests INTEGER DEFAULT 1,
    bedrooms INTEGER DEFAULT 1,
    bathrooms FLOAT DEFAULT 1.0,
    host_id VARCHAR(36) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    replica_id VARCHAR(36),
    version INTEGER DEFAULT 1
);
```

### Bookings Table

```sql
CREATE TABLE bookings (
    id VARCHAR(36) PRIMARY KEY,
    listing_id VARCHAR(36) REFERENCES listings(id),
    guest_id VARCHAR(36) NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    total_price FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);
```

## 🧪 Testing

### Running Tests

```bash
# Backend tests
cd tests
python test_backend.py

# Frontend tests
python test_frontend.py

# All tests
python -m unittest discover tests/
```

### Test Coverage

- **Backend Tests**: API endpoints, database operations, error handling, distributed systems features
- **Frontend Tests**: Component rendering, API integration, error handling, state management
- **Integration Tests**: End-to-end workflows, concurrent operations, data consistency

## 🔍 Distributed Systems Features

### 1. Microservices Architecture

- **Backend Service**: Handles API requests and database operations
- **Frontend Service**: Serves the React application
- **Load Balancer**: Distributes requests across services
- **Cache Service**: Redis for session management and caching

### 2. Load Balancing

```nginx
upstream backend {
    server backend:5000;
}

upstream frontend {
    server frontend:80;
}
```

### 3. Health Checks

```python
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'airbnb-listing-service',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })
```

### 4. Optimistic Locking

```python
# Check version for concurrent updates
if 'version' in data and data['version'] != listing.version:
    return jsonify({'error': 'Version conflict'}), 409

listing.version += 1
```

### 5. Horizontal Scaling

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    restart: unless-stopped
```

### 6. Monitoring and Metrics

```python
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    return jsonify({
        'total_listings': Listing.query.count(),
        'active_listings': Listing.query.filter_by(is_active=True).count(),
        'total_bookings': Booking.query.count(),
        'timestamp': datetime.utcnow().isoformat()
    })
```

## 🚀 Deployment

### Docker Compose Deployment

```bash
# Start all services
docker-compose up -d

# Scale backend service
docker-compose up -d --scale backend=3

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Production Considerations

1. **Environment Variables**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:pass@db:5432/airbnb
   export SECRET_KEY=your-secret-key
   ```

2. **Database Migration**
   ```bash
   flask db upgrade
   ```

3. **SSL/TLS Configuration**
   - Configure SSL certificates in Nginx
   - Enable HTTPS redirects
   - Set secure cookie flags

## 📊 Performance Considerations

### Backend Optimization

- **Database Indexing**: Indexes on frequently queried fields
- **Connection Pooling**: SQLAlchemy connection pooling
- **Caching**: Redis for frequently accessed data
- **Pagination**: Limit result sets for large queries

### Frontend Optimization

- **Code Splitting**: Lazy loading of components
- **Caching**: Browser caching for static assets
- **Compression**: Gzip compression for API responses
- **CDN**: Content delivery network for static files

## 🔒 Security Features

### API Security

- **CORS Configuration**: Proper cross-origin resource sharing
- **Input Validation**: Server-side validation of all inputs
- **SQL Injection Prevention**: Parameterized queries
- **Rate Limiting**: Request rate limiting per IP

### Container Security

- **Non-root User**: Containers run as non-root user
- **Minimal Base Images**: Alpine Linux for smaller attack surface
- **Security Scanning**: Regular vulnerability scanning
- **Secrets Management**: Environment variables for sensitive data

## 🐛 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   lsof -i :5000
   lsof -i :3000
   ```

2. **Database Connection Issues**
   ```bash
   # Check database file permissions
   ls -la airbnb_lab.db
   ```

3. **Docker Build Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a
   ```

### Debug Mode

```bash
# Enable debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1
```

## 📈 Monitoring and Logging

### Application Logs

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Health Monitoring

- **Health Checks**: Regular health check endpoints
- **Metrics Collection**: Prometheus metrics
- **Log Aggregation**: Centralized logging
- **Alerting**: Automated alerts for failures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Flask framework for the backend API
- React for the frontend application
- Docker for containerization
- Nginx for load balancing
- Redis for caching
- Prometheus for monitoring

---

**Lab 1 Airbnb - Distributed Systems Implementation**  
*DATA 236 - Distributed Systems for Data Engineering*
