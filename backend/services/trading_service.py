import os
import duckdb
import pandas as pd
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'market_data.duckdb')

class TradingService:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db = duckdb.connect(DB_PATH)
        self._init_db()

    def _init_db(self):
        """Initialize tables for trades and analytics."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id VARCHAR PRIMARY KEY,
                symbol VARCHAR,
                entry_date TIMESTAMP,
                exit_date TIMESTAMP,
                entry_price DOUBLE,
                exit_price DOUBLE,
                pnl DOUBLE,
                pnl_percent DOUBLE,
                is_profit BOOLEAN,
                duration INTEGER,
                journal_tag VARCHAR
            )
        """)
        # Initialize with some seed data if empty
        count = self.db.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        if count == 0:
            self._seed_data()

    def _seed_data(self):
        """Seed some initial trades for a 'warm' experience."""
        tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]
        tags = ["Followed Plan", "FOMO", "Technical Entry"]
        
        for i in range(20):
            symbol = random.choice(tickers)
            entry_date = datetime.now() - timedelta(days=random.randint(1, 100))
            duration = random.randint(1, 10)
            exit_date = entry_date + timedelta(days=duration)
            entry_price = random.uniform(100, 500)
            pnl_pct = random.uniform(-0.05, 0.1)
            exit_price = entry_price * (1 + pnl_pct)
            pnl = (exit_price - entry_price) * 100 # Assuming 100 shares
            is_profit = pnl > 0
            
            self.db.execute("""
                INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"trade_{i}", symbol, entry_date, exit_date, entry_price, 
                exit_price, pnl, pnl_pct * 100, is_profit, duration, 
                random.choice(tags)
            ))

    def get_trades(self, limit=50):
        df = self.db.execute(f"SELECT * FROM trades ORDER BY exit_date DESC LIMIT {limit}").df()
        return df.to_dict('records')

    def get_analytics(self):
        df = self.db.execute("SELECT * FROM trades").df()
        if df.empty:
            return {}

        total_trades = len(df)
        win_rate = (df['is_profit'].sum() / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = df['pnl'].sum()
        
        # Behavioral tags
        tags_df = df.groupby('journal_tag').agg(
            count=('id', 'count'),
            totalPnl=('pnl', 'sum'),
            avgPnl=('pnl', 'mean')
        ).reset_index()
        
        behavioral_tags = []
        for _, row in tags_df.iterrows():
            behavioral_tags.append({
                "tag": row['journal_tag'],
                "count": int(row['count']),
                "totalPnl": float(row['totalPnl']),
                "avgPnl": float(row['avgPnl']),
                "isDestructive": row['totalPnl'] < 0
            })

        return {
            "totalTrades": total_trades,
            "winRate": win_rate,
            "totalPnl": total_pnl,
            "behavioralTags": behavioral_tags
        }

    def get_equity_curve(self, capital=10000):
        df = self.db.execute("SELECT * FROM trades ORDER BY exit_date ASC").df()
        if df.empty:
            return []

        curve = []
        current_equity = capital
        
        # Start point
        start_date = df['exit_date'].min() - timedelta(days=1)
        curve.append({
            "date": start_date.isoformat(),
            "equity": capital,
            "drawdown": 0,
            "drawdownLimit": capital * 0.1
        })

        peak = capital
        for _, row in df.iterrows():
            current_equity += row['pnl']
            if current_equity > peak:
                peak = current_equity
            
            dd = ((peak - current_equity) / peak) * 100 if peak > 0 else 0
            
            curve.append({
                "date": row['exit_date'].isoformat(),
                "equity": current_equity,
                "drawdown": dd,
                "drawdownLimit": capital * 0.1
            })
            
        return curve

trading_service = TradingService()
