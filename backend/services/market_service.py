import yfinance as yf
from finvizfinance.quote import finvizfinance
from finvizfinance.news import News
import duckdb
import pandas as pd
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'market_data.duckdb')

class MarketService:
    def __init__(self):
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db = duckdb.connect(DB_PATH)
        self._init_db()

    def _init_db(self):
        """Initialize DuckDB tables for raw, cleaned, and features data."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS raw_prices (
                symbol VARCHAR,
                timestamp TIMESTAMP,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume BIGINT,
                timeframe VARCHAR
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS raw_news (
                symbol VARCHAR,
                title VARCHAR,
                source VARCHAR,
                timestamp TIMESTAMP,
                url VARCHAR,
                sentiment VARCHAR
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS cleaned_prices (
                symbol VARCHAR,
                timestamp TIMESTAMP,
                close DOUBLE,
                returns DOUBLE
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS price_features (
                symbol VARCHAR,
                timestamp TIMESTAMP,
                sma_20 DOUBLE,
                volatility DOUBLE
            )
        """)

    def clean_prices(self, symbol: str):
        """Clean raw price data and calculate returns."""
        self.db.execute(f"""
            INSERT INTO cleaned_prices
            SELECT 
                symbol, 
                timestamp, 
                close,
                (close - LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp)) / LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp) as returns
            FROM raw_prices
            WHERE symbol = '{symbol}'
            ON CONFLICT DO NOTHING
        """)

    def extract_features(self, symbol: str):
        """Extract features like Moving Averages and Volatility."""
        self.db.execute(f"""
            INSERT INTO price_features
            SELECT 
                symbol, 
                timestamp,
                AVG(close) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma_20,
                STDDEV(close) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as volatility
            FROM cleaned_prices
            WHERE symbol = '{symbol}'
        """)

    def get_ohlc(self, symbol: str, timeframe: str = '1D', start_date: str = None, end_date: str = None):
        """Get OHLC data using yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            # Map frontend timeframe to yfinance interval
            interval_map = {
                '1M': '1m',
                '5M': '5m',
                '15M': '15m',
                '30M': '30m',
                '1H': '1h',
                '1D': '1d',
                '1W': '1wk',
                '1MO': '1mo'
            }
            interval = interval_map.get(timeframe.upper(), '1d')
            
            df = ticker.history(interval=interval, start=start_date, end=end_date)
            
            if df.empty:
                return []

            # Format for frontend
            df = df.reset_index()
            result = []
            for _, row in df.iterrows():
                ts = row['Date'] if 'Date' in row else row['Datetime']
                result.append({
                    "date": ts.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
                
                # Save to DuckDB (Raw)
                self.db.execute("INSERT INTO raw_prices VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                (symbol, ts, row['Open'], row['High'], row['Low'], row['Close'], row['Volume'], timeframe))
            
            # Optionally trigger cleaning and feature extraction
            # self.clean_prices(symbol)
            # self.extract_features(symbol)
            
            return result
        except Exception as e:
            logger.error(f"Error fetching OHLC for {symbol}: {str(e)}")
            return []

    def get_quote(self, symbol: str):
        """Get real-time quote using yfinance and finviz."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Complement with finviz for more sentiment/context if needed
            # fvz = finvizfinance(symbol)
            
            return {
                "symbol": symbol,
                "price": info.get('currentPrice', info.get('regularMarketPrice')),
                "change": info.get('regularMarketChange'),
                "changePercent": info.get('regularMarketChangePercent'),
                "volume": info.get('regularMarketVolume'),
                "marketCap": info.get('marketCap'),
                "high": info.get('dayHigh'),
                "low": info.get('dayLow'),
                "open": info.get('regularMarketOpen'),
                "previousClose": info.get('regularMarketPreviousClose')
            }
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return None

    def get_news(self, symbol: str = None, limit: int = 10):
        """Get news using finvizfinance."""
        try:
            fnews = News()
            all_news = fnews.get_news()
            
            # finviz news returns a dict with 'news' and 'blogs'
            news_df = all_news.get('news', pd.DataFrame())
            
            if news_df.empty:
                return []

            # Filter by symbol if provided (finviz news is global by default in fnews.get_news())
            # For specific symbol news, we might need a different approach or filter titles
            
            result = []
            for _, row in news_df.head(limit).iterrows():
                result.append({
                    "id": str(hash(row['Title'])),
                    "symbol": symbol or "MARKET",
                    "title": row['Title'],
                    "source": row['Source'],
                    "timestamp": row['Date'], # Finviz date strings can be tricky
                    "url": row['Link'],
                    "sentiment": "neutral" # Simplification; could use textblob/transformers here
                })
            return result
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            return []

    def get_scanner_results(self, filters=None):
        """Mock scanner results using real yfinance data for top tickers."""
        tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "AMD", "INTC"]
        results = []
        for symbol in tickers:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                results.append({
                    "symbol": symbol,
                    "name": info.get('shortName', symbol),
                    "price": info.get('currentPrice', info.get('regularMarketPrice')),
                    "change": info.get('regularMarketChangePercent', 0) * 100,
                    "volume": info.get('regularMarketVolume', 0),
                    "rvol": random.uniform(0.5, 3.0), # Mock RVOL for now
                    "sector": info.get('sector', 'Unknown'),
                    "marketCap": info.get('marketCap', 0) / 1e9 # In Billions
                })
            except:
                continue
        return results

    def get_market_overview(self):
        """Get broad market overview."""
        indices = ["^GSPC", "^DJI", "^IXIC", "^RUT"]
        results = []
        for idx in indices:
            ticker = yf.Ticker(idx)
            info = ticker.info
            results.append({
                "symbol": idx,
                "name": info.get('shortName', idx),
                "value": info.get('regularMarketPrice'),
                "change": info.get('regularMarketChange'),
                "changePercent": info.get('regularMarketChangePercent')
            })
        return {
            "indices": results,
            "topGainers": [], # Implement logic to fetch top gainers
            "topLosers": [],
            "mostActive": []
        }

    def calculate_advanced_metrics(self, returns, trades=None):
        """
        Calculate professional quant metrics:
        - Sharpe Ratio
        - Sortino Ratio
        - Maximum Drawdown
        - Hit Rate
        - Turnover
        """
        import numpy as np
        
        metrics = {}
        
        if len(returns) == 0:
            return metrics
        
        returns_array = np.array(returns)
        
        # Sharpe Ratio (annualized)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        metrics['sharpe_ratio'] = round(sharpe, 2)
        
        # Sortino Ratio (only downside volatility)
        downside_returns = returns_array[returns_array < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino = (mean_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0
        metrics['sortino_ratio'] = round(sortino, 2)
        
        # Maximum Drawdown
        cumulative = np.cumprod(1 + returns_array)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_dd = np.min(drawdown) * 100
        metrics['max_drawdown'] = round(abs(max_dd), 2)
        
        # Hit Rate (if trades provided)
        if trades:
            winning_trades = sum(1 for t in trades if t['pnl'] > 0)
            metrics['hit_rate'] = round((winning_trades / len(trades)) * 100, 2) if len(trades) > 0 else 0
            metrics['total_trades'] = len(trades)
        
        # Turnover (average holding period)
        if trades:
            avg_duration = sum(t.get('duration', 0) for t in trades) / len(trades) if len(trades) > 0 else 0
            metrics['avg_holding_days'] = round(avg_duration, 1)
            metrics['turnover'] = round(252 / avg_duration, 2) if avg_duration > 0 else 0
        
        return metrics

market_service = MarketService()
