# Lab 1 Airbnb - Run Scripts

## 🚀 Quick Start Scripts

### start.sh - Start the application
```bash
#!/bin/bash
echo "🏠 Starting Lab 1 Airbnb - Distributed Systems"
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
curl -f http://localhost:5000/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Backend service is healthy"
else
    echo "❌ Backend service is not responding"
fi

curl -f http://localhost:3000 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Frontend service is healthy"
else
    echo "❌ Frontend service is not responding"
fi

echo ""
echo "🎉 Lab 1 Airbnb is now running!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:5000"
echo "⚖️  Load Balancer: http://localhost:80"
echo "📊 Monitoring: http://localhost:9090"
echo ""
echo "To stop the services, run: ./stop.sh"
```

### stop.sh - Stop the application
```bash
#!/bin/bash
echo "🛑 Stopping Lab 1 Airbnb - Distributed Systems"
echo "==============================================="

# Stop services
echo "🐳 Stopping Docker services..."
docker-compose down

# Clean up containers and images (optional)
read -p "🗑️  Do you want to remove containers and images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning up Docker resources..."
    docker-compose down --rmi all --volumes --remove-orphans
    docker system prune -f
fi

echo "✅ Lab 1 Airbnb has been stopped"
```

### test.sh - Run tests
```bash
#!/bin/bash
echo "🧪 Running Lab 1 Airbnb Tests"
echo "============================="

# Check if services are running
if ! curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "❌ Backend service is not running. Please start the application first."
    exit 1
fi

# Run backend tests
echo "🔧 Running backend tests..."
cd tests
python test_backend.py

# Run frontend tests
echo "📱 Running frontend tests..."
python test_frontend.py

# Run integration tests
echo "🔗 Running integration tests..."
python -m unittest discover . -p "test_*" -v

echo ""
echo "✅ All tests completed!"
```

### deploy.sh - Production deployment
```bash
#!/bin/bash
echo "🚀 Deploying Lab 1 Airbnb to Production"
echo "======================================="

# Set production environment variables
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@db:5432/airbnb
export SECRET_KEY=$(openssl rand -hex 32)

# Build production images
echo "🏗️  Building production images..."
docker-compose -f docker-compose.prod.yml build

# Deploy services
echo "🚀 Deploying services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.prod.yml exec backend flask db upgrade

# Check service health
echo "🔍 Checking service health..."
curl -f http://localhost/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Production deployment successful!"
    echo "🌐 Application: http://localhost"
else
    echo "❌ Production deployment failed"
    exit 1
fi
```

### monitor.sh - Monitor services
```bash
#!/bin/bash
echo "📊 Lab 1 Airbnb - Service Monitoring"
echo "==================================="

# Check service status
echo "🔍 Service Status:"
echo "-----------------"

# Backend health
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Backend: Healthy"
else
    echo "❌ Backend: Unhealthy"
fi

# Frontend health
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend: Healthy"
else
    echo "❌ Frontend: Unhealthy"
fi

# Load balancer health
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Load Balancer: Healthy"
else
    echo "❌ Load Balancer: Unhealthy"
fi

echo ""
echo "📈 System Metrics:"
echo "------------------"

# Get system metrics
curl -s http://localhost:5000/api/metrics | python -m json.tool

echo ""
echo "🐳 Docker Status:"
echo "----------------"
docker-compose ps

echo ""
echo "📊 Resource Usage:"
echo "-----------------"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### setup.sh - Initial setup
```bash
#!/bin/bash
echo "⚙️  Lab 1 Airbnb - Initial Setup"
echo "================================"

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

echo "✅ All prerequisites are installed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p backups

# Set permissions
echo "🔐 Setting permissions..."
chmod +x *.sh

# Create environment file
echo "📝 Creating environment file..."
cat > .env << EOF
FLASK_ENV=development
DATABASE_URL=sqlite:///airbnb_lab.db
SECRET_KEY=dev-secret-key-change-in-production
REACT_APP_API_URL=http://localhost:5000/api
EOF

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run ./start.sh to start the application"
echo "2. Run ./test.sh to run tests"
echo "3. Run ./monitor.sh to monitor services"
echo "4. Run ./stop.sh to stop the application"
```

## 📋 Usage Instructions

### 1. Initial Setup
```bash
chmod +x *.sh
./setup.sh
```

### 2. Start Application
```bash
./start.sh
```

### 3. Run Tests
```bash
./test.sh
```

### 4. Monitor Services
```bash
./monitor.sh
```

### 5. Stop Application
```bash
./stop.sh
```

### 6. Production Deployment
```bash
./deploy.sh
```

## 🔧 Customization

### Environment Variables
Edit `.env` file to customize:
- Database URL
- Secret keys
- API endpoints
- Port configurations

### Docker Configuration
Modify `docker-compose.yml` for:
- Service scaling
- Volume mounts
- Network configuration
- Resource limits

### Monitoring
Customize monitoring in:
- `nginx/nginx.conf` for load balancer
- `monitoring/prometheus.yml` for metrics
- `backend/app.py` for health checks

## 🆘 Troubleshooting

### Common Issues
1. **Port conflicts**: Check if ports 3000, 5000, 80 are available
2. **Docker issues**: Run `docker system prune -a` to clean cache
3. **Permission issues**: Run `chmod +x *.sh` to set execute permissions
4. **Service not starting**: Check logs with `docker-compose logs -f`

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
export FLASK_ENV=development

# View detailed logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Reset Everything
```bash
# Stop and remove everything
docker-compose down --rmi all --volumes --remove-orphans
docker system prune -a -f

# Restart from scratch
./setup.sh
./start.sh
```

---

**Lab 1 Airbnb - Run Scripts**  
*Automated deployment and management scripts for distributed systems*
