
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import logging

class DatabaseOptimizer:
    """Database optimization utilities"""
    
    @staticmethod
    def create_optimized_engine(database_url: str):
        """Create optimized database engine"""
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
    
    @staticmethod
    def create_indexes(engine):
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_product_id ON inventory(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status)",
            "CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON agent_logs(timestamp)"
        ]
        
        with engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                except Exception as e:
                    logging.warning(f"Index creation failed: {e}")
