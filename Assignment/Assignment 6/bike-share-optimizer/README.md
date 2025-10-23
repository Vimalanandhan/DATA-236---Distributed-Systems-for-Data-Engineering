# Bike-Share Pass Optimizer

An AI-powered ReAct agent that analyzes bike-share trip data and pricing policies to recommend whether users should buy a monthly membership or pay per ride/minute.

## Features

- **ReAct Loop**: Uses a reasoning loop with Thought → Action → Observation → Final Answer
- **MRKL Tools**: Three specialized tools for data analysis:
  - `csv_sql`: Run SQL queries on uploaded trip data
  - `policy_retriever`: Extract pricing information from policy pages
  - `calculator`: Perform safe arithmetic calculations
- **Web UI**: Modern, responsive interface for uploading data and viewing results
- **Real-time Timeline**: Shows the agent's thinking process step-by-step
- **Cost Analysis**: Detailed breakdown of pay-per-use vs membership costs

## Architecture

```
bike-share-optimizer/
├── agent/
│   └── react_agent.js          # Main ReAct agent implementation
├── tools/
│   ├── csv_sql.js              # SQL query tool for trip data
│   ├── policy_retriever.js     # Web scraping tool for pricing info
│   └── calculator.js           # Safe arithmetic calculator
├── ui/
│   └── index.html              # Web interface
├── server.js                   # Express server
├── sample_data.csv            # Sample trip data for testing
└── README.md                  # This file
```

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the server:
```bash
npm run bike-share
```

3. Open your browser to `http://localhost:3001`

## Usage

1. **Upload Trip Data**: Upload a CSV file with your bike-share trip data
2. **Enter Pricing URL**: Provide the URL to the official pricing policy page
3. **Run Analysis**: Click "Run Analysis" to start the AI agent
4. **View Results**: See the recommendation, cost breakdown, and agent timeline

## CSV Data Format

Your CSV file should contain the following columns:
- `trip_id`: Unique identifier for each trip
- `start_time`: Trip start time (YYYY-MM-DD HH:MM:SS)
- `end_time`: Trip end time (YYYY-MM-DD HH:MM:SS)
- `duration`: Trip duration in minutes
- `bike_type`: Type of bike used (classic, ebike, electric, etc.)
- `start_station`: Starting station name
- `end_station`: Ending station name

## Supported Cities

The agent works with any bike-share system that provides:
- Public trip data in CSV format
- Public pricing policy page

Tested with:
- New York City — Citi Bike
- Chicago — Divvy
- San Francisco Bay Area — Bay Wheels
- Washington, DC — Capital Bikeshare

## Agent Process

1. **Data Loading**: Loads and analyzes the uploaded CSV file
2. **Policy Retrieval**: Scrapes pricing information from the policy page
3. **Cost Calculation**: Calculates costs for both pay-per-use and membership
4. **Decision Making**: Compares costs and makes a recommendation
5. **Result Generation**: Produces detailed analysis with citations

## Tools

### CSV SQL Tool
- Runs read-only SQL queries on trip data
- Supports aggregation, filtering, and grouping
- Automatically creates SQLite database from CSV

### Policy Retriever Tool
- Scrapes pricing pages for relevant information
- Extracts membership prices, per-ride costs, surcharges
- Uses semantic search to find relevant passages

### Calculator Tool
- Performs safe arithmetic without eval()
- Supports basic operations: +, -, *, /, parentheses
- Whitelist validation for security

## API Endpoints

- `GET /` - Web interface
- `POST /api/analyze` - Run analysis on uploaded data

## Example Output

```json
{
  "decision": "Buy Monthly Membership",
  "justification": "Monthly membership is more cost-effective, saving $15.50 compared to pay-per-use...",
  "costBreakdown": {
    "payPerUse": {
      "total": 45.50,
      "perTrip": 0.91
    },
    "membership": {
      "total": 30.00,
      "overageCharges": 0.00
    },
    "savings": -15.50
  },
  "citations": [...],
  "steps": [...],
  "totalSteps": 12,
  "totalTime": 2500,
  "stopReason": "completed"
}
```

## Security Features

- File upload validation (CSV only, 10MB limit)
- SQL injection protection (read-only queries)
- Safe arithmetic evaluation (no eval())
- Input sanitization and validation

## Testing

Use the provided `sample_data.csv` file to test the system with realistic trip data.

## License

MIT License
