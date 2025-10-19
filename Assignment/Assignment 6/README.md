# Assignment 6 - MongoDB Task Management & AI Memory System

This assignment consists of two parts:
1. **Part 1**: MongoDB Task Management API (Node.js/Express)
2. **Part 2**: AI Memory System (FastAPI + Ollama + MongoDB)

## 📋 Part 1: MongoDB Task Management API

### Features
- RESTful API with CRUD operations for tasks
- MongoDB integration with Mongoose
- Data validation and error handling
- CORS support for web applications

### API Endpoints
- `POST /api/tasks` - Create a new task
- `GET /api/tasks` - Get all tasks
- `GET /api/tasks/:id` - Get task by ID
- `PUT /api/tasks/:id` - Update task
- `DELETE /api/tasks/:id` - Delete task
- `GET /health` - Health check

### Task Schema
```javascript
{
  title: String (required, max 100 chars),
  description: String,
  status: String (enum: ['pending', 'in-progress', 'completed']),
  priority: String (enum: ['low', 'medium', 'high']),
  dueDate: Date (required),
  category: String (enum: ['Work', 'Personal', 'Shopping', 'Health', 'Other'])
}
```

### Setup & Run
```bash
# Install dependencies
npm install

# Start MongoDB (if not running)
brew services start mongodb-community

# Run the server
node server.js
```

## 🧠 Part 2: AI Memory System

### Features
- Short-term memory (sliding window of recent messages)
- Long-term memory (session and lifetime summaries)
- Episodic memory (fact extraction with embeddings)
- Local LLM integration via Ollama
- Vector similarity search for relevant facts

### API Endpoints
- `POST /api/chat` - Chat with AI assistant
- `GET /api/memory/{user_id}` - Get user's memory
- `GET /api/aggregate/{user_id}` - Get aggregated user data

### Memory Collections
1. **messages** - Conversation history
2. **summaries** - Session and lifetime summaries
3. **episodes** - Extracted facts with embeddings

### Setup & Run
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Setup Ollama and models
./setup_ollama.sh

# Start the FastAPI server
python3 main.py
```

## 📁 File Structure

```
Assignment 6/
├── Part 1 - Task Management/
│   ├── models/
│   │   └── Task.js
│   ├── server.js
│   ├── package.json
│   ├── config.js
│   ├── test_api.js
│   └── test.html
├── Part 2 - AI Memory System/
│   ├── api_endpoints.py
│   ├── memory_logic.py
│   ├── mongodb_models.py
│   ├── main.py
│   ├── requirements.txt
│   ├── setup_ollama.sh
│   └── chat_interface.html
└── README.md
```

## 🚀 Quick Start

### Part 1: Task Management
1. `npm install`
2. `node server.js`
3. Test with `node test_api.js` or open `test.html`

### Part 2: AI Memory System
1. `pip3 install -r requirements.txt`
2. `./setup_ollama.sh`
3. `python3 main.py`
4. Open `chat_interface.html` or use Postman

## 📸 Screenshots Required

For submission, capture:
1. Conversation showing assistant replies
2. JSON result of `GET /api/memory/{user_id}`
3. JSON result of `GET /api/aggregate/{user_id}`
4. MongoDB Compass views of collections
5. Code files for endpoints and memory logic

## 🔧 Dependencies

### Part 1
- Node.js
- Express
- Mongoose
- MongoDB
- CORS
- Body-parser

### Part 2
- Python 3
- FastAPI
- Motor (async MongoDB driver)
- Ollama
- NumPy
- Scikit-learn
- Requests
