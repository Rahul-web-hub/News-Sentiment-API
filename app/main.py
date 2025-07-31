from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import re

app = FastAPI()

# --- Database Setup ---
conn = sqlite3.connect('news_sentiment.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS news_sentiment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        headlines TEXT,
        overall_sentiment TEXT
    )
''')
conn.commit()

# --- Pydantic Models ---
class HeadlineSentiment(BaseModel):
    title: str
    sentiment: str

class NewsSentimentRequest(BaseModel):
    symbol: str

class NewsSentimentResponse(BaseModel):
    symbol: str
    timestamp: str
    headlines: List[HeadlineSentiment]
    overall_sentiment: str

# --- Utility Functions ---
def fetch_latest_headlines(symbol: str, limit: int = 3) -> List[str]:
    """
    Fetch latest news headlines for a stock symbol from Google News.
    """
    url = f"https://news.google.com/search?q={symbol}%20stock%20india&hl=en-IN&gl=IN&ceid=IN%3Aen"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = []
        for el in soup.find_all('a', class_='JtKRv', limit=limit):
            # Remove HTML tags and whitespace
            title = re.sub(r'<[^>]+>', '', str(el)).strip()
            if title:
                headlines.append(title)
        return headlines
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def analyze_headline_sentiment(text: str) -> str:
    """
    Analyze sentiment of a headline using TextBlob.
    """
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    return "neutral"

def majority_sentiment(headlines: List[HeadlineSentiment]) -> str:
    """
    Determine overall sentiment by majority vote.
    """
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for h in headlines:
        counts[h.sentiment] += 1
    return max(counts, key=counts.get)

# --- API Endpoint ---
@app.post("/news-sentiment", response_model=NewsSentimentResponse)
async def news_sentiment(request: NewsSentimentRequest):
    symbol = request.symbol.upper()

    # Check cache (last 10 minutes)
    cursor.execute(
        """
        SELECT timestamp, headlines, overall_sentiment
        FROM news_sentiment
        WHERE symbol = ? AND timestamp > datetime('now', '-10 minutes')
        ORDER BY timestamp DESC LIMIT 1
        """,
        (symbol,)
    )
    cached = cursor.fetchone()
    if cached:
        return NewsSentimentResponse(
            symbol=symbol,
            timestamp=cached[0],
            headlines=[HeadlineSentiment(**h) for h in json.loads(cached[1])],
            overall_sentiment=cached[2]
        )

    # Fetch and process new headlines
    titles = fetch_latest_headlines(symbol)
    if not titles:
        raise HTTPException(status_code=404, detail="No news headlines found")

    headlines = [
        HeadlineSentiment(title=title, sentiment=analyze_headline_sentiment(title))
        for title in titles
    ]
    overall = majority_sentiment(headlines)

    # Store in DB
    cursor.execute(
        "INSERT INTO news_sentiment (symbol, headlines, overall_sentiment) VALUES (?, ?, ?)",
        (symbol, json.dumps([h.dict() for h in headlines]), overall)
    )
    conn.commit()

    return NewsSentimentResponse(
        symbol=symbol,
        timestamp=datetime.utcnow().isoformat() + "Z",
        headlines=headlines,
        overall_sentiment=overall
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)