# News Sentiment Analysis API

A FastAPI-based service that analyzes sentiment of stock-related news headlines using natural language processing.

## Features

- Fetches latest stock news headlines from Google News
- Performs sentiment analysis on headlines using TextBlob
- Caches results for 10 minutes to minimize API calls
- Returns aggregated sentiment analysis with individual headline scores

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Rahul-web-hub/diversifi-news-sentiment.git
cd diversifi-news-sentiment
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install required packages:
```bash
pip install fastapi uvicorn requests beautifulsoup4 textblob pydantic sqlite3
```

### Running the Service

Start the API server:
```bash
python main.py
```

The service will be available at `http://localhost:8000`

## API Usage

Make a POST request to `/news-sentiment` endpoint:

```bash
curl -X POST "http://localhost:8000/news-sentiment" \
     -H "Content-Type: application/json" \
     -d '{"symbol":"AAPL"}'
```

### Sample Response

```json
{
    "symbol": "AAPL",
    "timestamp": "2025-07-31T12:00:00Z",
    "headlines": [
        {
            "title": "Apple Stock Surges After Strong Earnings Report",
            "sentiment": "positive"
        },
        {
            "title": "Apple's New iPhone Expected to Drive Growth",
            "sentiment": "positive"
        },
        {
            "title": "Market Analysis: Apple's Position in Tech Sector",
            "sentiment": "neutral"
        }
    ],
    "overall_sentiment": "positive"
}
```

## Technical Details

### News Source
- Uses Google News API to fetch latest headlines
- Configurable limit for number of headlines (default: 3)
- Headlines are filtered for stock-specific news

### Sentiment Analysis
- Implements TextBlob for natural language processing
- Sentiment classification:
  - Positive: polarity > 0.1
  - Negative: polarity < -0.1
  - Neutral: -0.1 ≤ polarity ≤ 0.1
- Overall sentiment determined by majority voting

### Data Storage
- SQLite database for caching results
- 10-minute cache window to reduce API calls
- Stores headline data and aggregated sentiment

## Contributing
Feel free to open issues or submit pull requests for improvements.