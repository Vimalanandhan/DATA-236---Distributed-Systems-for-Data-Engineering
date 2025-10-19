# Lab 1 Airbnb - Quick Start Guide

## 🚀 Getting Started

### Option 1: Docker Compose (Recommended)

1. **Start all services**
   ```bash
   cd Lab1-Airbnb
   docker-compose up --build
   ```

2. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Load Balancer: http://localhost:80

### Option 2: Manual Setup

1. **Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm start
   ```

## 🧪 Testing

```bash
# Run all tests
python -m unittest discover tests/

# Run specific test files
python tests/test_backend.py
python tests/test_frontend.py
```

## 📊 Features

- ✅ Create, read, update, delete listings
- ✅ Booking management
- ✅ Advanced filtering and pagination
- ✅ Distributed systems architecture
- ✅ Load balancing with Nginx
- ✅ Health checks and monitoring
- ✅ Optimistic locking for concurrency
- ✅ Comprehensive test suite
- ✅ Docker containerization

## 🔧 API Examples

### Create a Listing
```bash
curl -X POST http://localhost:5000/api/listings \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Beautiful Apartment",
    "price_per_night": 150.0,
    "location": "San Francisco, CA",
    "property_type": "apartment",
    "host_id": "host_123"
  }'
```

### Get Listings with Filters
```bash
curl "http://localhost:5000/api/listings?location=San Francisco&property_type=apartment&min_price=100&max_price=200"
```

### Health Check
```bash
curl http://localhost:5000/health
```

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale backend
docker-compose up -d --scale backend=3

# Stop services
docker-compose down
```

## 📁 Project Structure

```
Lab1-Airbnb/
├── backend/          # Flask API server
├── frontend/         # React application
├── nginx/            # Load balancer config
├── tests/            # Test suites
├── docker-compose.yml
└── README.md
```

## 🆘 Troubleshooting

- **Port conflicts**: Check if ports 3000, 5000, 80 are available
- **Database issues**: Ensure SQLite file permissions are correct
- **Docker issues**: Run `docker system prune -a` to clean cache

For detailed documentation, see the main README.md file.
