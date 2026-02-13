import os
import duckdb
import json
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'research_lab.duckdb')

class ResearchService:
    """
    Professional Quant Research Lab Service
    Inspired by MLflow for experiment tracking and strategy comparison
    """
    
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db = duckdb.connect(DB_PATH)
        self._init_db()

    def _init_db(self):
        """Initialize research lab tables."""
        # Experiments table - track different strategy experiments
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id VARCHAR PRIMARY KEY,
                name VARCHAR,
                strategy_type VARCHAR,
                description TEXT,
                created_at TIMESTAMP,
                status VARCHAR
            )
        """)
        
        # Runs table - individual backtest runs within experiments
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id VARCHAR PRIMARY KEY,
                experiment_id VARCHAR,
                run_name VARCHAR,
                symbol VARCHAR,
                timeframe VARCHAR,
                start_date DATE,
                end_date DATE,
                parameters JSON,
                metrics JSON,
                created_at TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
            )
        """)
        
        # Strategy templates
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS strategy_templates (
                template_id VARCHAR PRIMARY KEY,
                name VARCHAR,
                category VARCHAR,
                description TEXT,
                default_params JSON,
                created_at TIMESTAMP
            )
        """)
        
        # Initialize default strategy templates if empty
        count = self.db.execute("SELECT COUNT(*) FROM strategy_templates").fetchone()[0]
        if count == 0:
            self._seed_strategy_templates()

    def _seed_strategy_templates(self):
        """Seed core playbook strategies."""
        templates = [
            {
                "template_id": str(uuid.uuid4()),
                "name": "Momentum Breakout",
                "category": "Momentum",
                "description": "Trend-following strategy using EMA crossovers with momentum confirmation",
                "default_params": {
                    "fast_ema": 20,
                    "slow_ema": 50,
                    "momentum_period": 14,
                    "volume_threshold": 1.5,
                    "stop_loss": 2.0,
                    "take_profit": 5.0
                }
            },
            {
                "template_id": str(uuid.uuid4()),
                "name": "Mean Reversion RSI",
                "category": "Mean-Reversion",
                "description": "Contrarian strategy using RSI oversold/overbought levels",
                "default_params": {
                    "rsi_period": 14,
                    "oversold": 30,
                    "overbought": 70,
                    "mean_period": 20,
                    "stop_loss": 1.5,
                    "take_profit": 3.0
                }
            },
            {
                "template_id": str(uuid.uuid4()),
                "name": "Bollinger Bounce",
                "category": "Mean-Reversion",
                "description": "Mean-reversion using Bollinger Bands",
                "default_params": {
                    "bb_period": 20,
                    "bb_std": 2,
                    "stop_loss": 2.0,
                    "take_profit": 4.0
                }
            },
            {
                "template_id": str(uuid.uuid4()),
                "name": "Seasonal Pattern",
                "category": "Seasonality",
                "description": "Trade based on historical seasonal patterns",
                "default_params": {
                    "lookback_years": 5,
                    "entry_month": 11,
                    "exit_month": 4,
                    "stop_loss": 3.0,
                    "take_profit": 10.0
                }
            },
            {
                "template_id": str(uuid.uuid4()),
                "name": "Momentum Scanner",
                "category": "Momentum",
                "description": "Multi-timeframe momentum with RVOL confirmation",
                "default_params": {
                    "ema_fast": 12,
                    "ema_slow": 26,
                    "rvol_threshold": 2.0,
                    "rsi_min": 50,
                    "stop_loss": 2.5,
                    "take_profit": 6.0
                }
            }
        ]
        
        for template in templates:
            self.db.execute("""
                INSERT INTO strategy_templates VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template["template_id"],
                template["name"],
                template["category"],
                template["description"],
                json.dumps(template["default_params"]),
                datetime.now()
            ))

    def create_experiment(self, name: str, strategy_type: str, description: str = ""):
        """Create a new research experiment."""
        experiment_id = str(uuid.uuid4())
        self.db.execute("""
            INSERT INTO experiments VALUES (?, ?, ?, ?, ?, ?)
        """, (
            experiment_id,
            name,
            strategy_type,
            description,
            datetime.now(),
            "active"
        ))
        return {"experiment_id": experiment_id, "name": name}

    def log_run(self, experiment_id: str, run_name: str, symbol: str, 
                timeframe: str, parameters: dict, metrics: dict,
                start_date: str = None, end_date: str = None):
        """Log a backtest run to an experiment."""
        run_id = str(uuid.uuid4())
        self.db.execute("""
            INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            experiment_id,
            run_name,
            symbol,
            timeframe,
            start_date,
            end_date,
            json.dumps(parameters),
            json.dumps(metrics),
            datetime.now()
        ))
        return {"run_id": run_id}

    def get_experiments(self):
        """Get all experiments."""
        df = self.db.execute("""
            SELECT 
                experiment_id,
                name,
                strategy_type,
                description,
                created_at,
                status,
                (SELECT COUNT(*) FROM runs WHERE runs.experiment_id = experiments.experiment_id) as run_count
            FROM experiments
            ORDER BY created_at DESC
        """).df()
        return df.to_dict('records')

    def get_experiment_runs(self, experiment_id: str):
        """Get all runs for an experiment with detailed metrics."""
        df = self.db.execute("""
            SELECT * FROM runs 
            WHERE experiment_id = ?
            ORDER BY created_at DESC
        """, (experiment_id,)).df()
        
        runs = []
        for _, row in df.iterrows():
            runs.append({
                "run_id": row['run_id'],
                "run_name": row['run_name'],
                "symbol": row['symbol'],
                "timeframe": row['timeframe'],
                "parameters": json.loads(row['parameters']),
                "metrics": json.loads(row['metrics']),
                "created_at": row['created_at'].isoformat()
            })
        return runs

    def get_strategy_templates(self):
        """Get all strategy templates."""
        df = self.db.execute("SELECT * FROM strategy_templates").df()
        templates = []
        for _, row in df.iterrows():
            templates.append({
                "template_id": row['template_id'],
                "name": row['name'],
                "category": row['category'],
                "description": row['description'],
                "default_params": json.loads(row['default_params'])
            })
        return templates

    def compare_runs(self, run_ids: list):
        """Compare multiple runs side by side."""
        placeholders = ','.join(['?' for _ in run_ids])
        df = self.db.execute(f"""
            SELECT * FROM runs WHERE run_id IN ({placeholders})
        """, run_ids).df()
        
        comparison = []
        for _, row in df.iterrows():
            comparison.append({
                "run_id": row['run_id'],
                "run_name": row['run_name'],
                "symbol": row['symbol'],
                "parameters": json.loads(row['parameters']),
                "metrics": json.loads(row['metrics'])
            })
        return comparison

research_service = ResearchService()
