# app/core/database/sovereign_db.py
"""
Sovereign Core Database Interface

Abstract database interface that works with Core DB.
Maintains backward compatibility with Supabase queries.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class SovereignDBError(Exception):
    """Raised when database operations fail"""
    pass


class SovereignDBClient:
    """
    Client for Sovereign Core database.
    
    Features:
    - Async database operations
    - Connection pooling
    - Backward compatible with Supabase queries
    - Transaction support
    """
    
    def __init__(
        self,
        db_host: str,
        db_port: int,
        db_name: str,
        db_user: str,
        db_password: str,
        pool_min_size: int = 10,
        pool_max_size: int = 20
    ):
        """
        Initialize Sovereign DB client.
        
        Args:
            db_host: Database host
            db_port: Database port
            db_name: Database name
            db_user: Database user
            db_password: Database password
            pool_min_size: Minimum pool size
            pool_max_size: Maximum pool size
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.pool_min_size = pool_min_size
        self.pool_max_size = pool_max_size
        
        self._pool: Optional[asyncpg.Pool] = None
        
        logger.info(
            f"SovereignDBClient initialized (host={db_host}, db={db_name})"
        )
    
    async def connect(self):
        """Create database connection pool"""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    host=self.db_host,
                    port=self.db_port,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    min_size=self.pool_min_size,
                    max_size=self.pool_max_size
                )
                logger.info("Database connection pool created")
            
            except Exception as e:
                logger.error(f"Failed to create connection pool: {str(e)}")
                raise SovereignDBError(f"Connection failed: {str(e)}")
    
    async def disconnect(self):
        """Close database connection pool"""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire database connection from pool"""
        if self._pool is None:
            await self.connect()
        
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)
    
    async def execute(
        self,
        query: str,
        *args,
        **kwargs
    ) -> str:
        """
        Execute SQL query (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query string
            *args: Query parameters
        
        Returns:
            Query execution status
        """
        try:
            async with self.acquire() as conn:
                result = await conn.execute(query, *args, **kwargs)
                logger.debug(f"Executed query: {query[:100]}...")
                return result
        
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            raise SovereignDBError(f"Execution failed: {str(e)}")
    
    async def fetch(
        self,
        query: str,
        *args,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple rows from database.
        
        Args:
            query: SQL query string
            *args: Query parameters
        
        Returns:
            List of rows as dictionaries
        """
        try:
            async with self.acquire() as conn:
                rows = await conn.fetch(query, *args, **kwargs)
                result = [dict(row) for row in rows]
                logger.debug(f"Fetched {len(result)} rows")
                return result
        
        except Exception as e:
            logger.error(f"Query fetch error: {str(e)}")
            raise SovereignDBError(f"Fetch failed: {str(e)}")
    
    async def fetchrow(
        self,
        query: str,
        *args,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch single row from database.
        
        Args:
            query: SQL query string
            *args: Query parameters
        
        Returns:
            Row as dictionary or None
        """
        try:
            async with self.acquire() as conn:
                row = await conn.fetchrow(query, *args, **kwargs)
                result = dict(row) if row else None
                logger.debug(f"Fetched row: {result is not None}")
                return result
        
        except Exception as e:
            logger.error(f"Query fetchrow error: {str(e)}")
            raise SovereignDBError(f"Fetch failed: {str(e)}")
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Optional[int]:
        """
        Insert row into table.
        
        Args:
            table: Table name
            data: Data to insert
        
        Returns:
            Inserted row ID or None
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(f'${i+1}' for i in range(len(data)))
            values = list(data.values())
            
            query = f"""
                INSERT INTO {table} ({columns})
                VALUES ({placeholders})
                RETURNING id
            """
            
            row = await self.fetchrow(query, *values)
            return row['id'] if row else None
        
        except Exception as e:
            logger.error(f"Insert error: {str(e)}")
            raise SovereignDBError(f"Insert failed: {str(e)}")
    
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any]
    ) -> int:
        """
        Update rows in table.
        
        Args:
            table: Table name
            data: Data to update
            where: WHERE clause conditions
        
        Returns:
            Number of rows updated
        """
        try:
            set_clause = ', '.join(
                f"{k} = ${i+1}" for i, k in enumerate(data.keys())
            )
            where_clause = ' AND '.join(
                f"{k} = ${i+len(data)+1}" 
                for i, k in enumerate(where.keys())
            )
            
            values = list(data.values()) + list(where.values())
            
            query = f"""
                UPDATE {table}
                SET {set_clause}
                WHERE {where_clause}
            """
            
            result = await self.execute(query, *values)
            # Parse result to get row count
            count = int(result.split()[-1]) if result else 0
            return count
        
        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            raise SovereignDBError(f"Update failed: {str(e)}")
    
    async def delete(
        self,
        table: str,
        where: Dict[str, Any]
    ) -> int:
        """
        Delete rows from table.
        
        Args:
            table: Table name
            where: WHERE clause conditions
        
        Returns:
            Number of rows deleted
        """
        try:
            where_clause = ' AND '.join(
                f"{k} = ${i+1}" for i, k in enumerate(where.keys())
            )
            values = list(where.values())
            
            query = f"DELETE FROM {table} WHERE {where_clause}"
            
            result = await self.execute(query, *values)
            count = int(result.split()[-1]) if result else 0
            return count
        
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            raise SovereignDBError(f"Delete failed: {str(e)}")


# Backward compatibility adapter for Supabase
class SupabaseDBCompatibilityAdapter:
    """
    Adapter to maintain backward compatibility with Supabase database queries.
    """
    
    def __init__(self, sovereign_db: SovereignDBClient):
        """
        Initialize DB compatibility adapter.
        
        Args:
            sovereign_db: Sovereign DB client instance
        """
        self.db = sovereign_db
        logger.info("Supabase DB compatibility adapter initialized")
    
    async def from_(self, table: str):
        """
        Supabase-style table query builder.
        
        Args:
            table: Table name
        
        Returns:
            Query builder instance
        """
        return SupabaseQueryBuilder(self.db, table)


class SupabaseQueryBuilder:
    """Query builder for Supabase-style queries"""
    
    def __init__(self, db: SovereignDBClient, table: str):
        self.db = db
        self.table = table
        self._select_cols = "*"
        self._where_conditions = {}
        self._limit_value = None
        self._order_by = None
    
    def select(self, columns: str = "*"):
        """Select columns"""
        self._select_cols = columns
        return self
    
    def eq(self, column: str, value: Any):
        """Add WHERE column = value"""
        self._where_conditions[column] = value
        return self
    
    def limit(self, count: int):
        """Limit results"""
        self._limit_value = count
        return self
    
    def order(self, column: str, desc: bool = False):
        """Order results"""
        self._order_by = f"{column} {'DESC' if desc else 'ASC'}"
        return self
    
    async def execute(self):
        """Execute query"""
        query = f"SELECT {self._select_cols} FROM {self.table}"
        
        if self._where_conditions:
            where_clause = ' AND '.join(
                f"{k} = ${i+1}" 
                for i, k in enumerate(self._where_conditions.keys())
            )
            query += f" WHERE {where_clause}"
        
        if self._order_by:
            query += f" ORDER BY {self._order_by}"
        
        if self._limit_value:
            query += f" LIMIT {self._limit_value}"
        
        values = list(self._where_conditions.values())
        
        return await self.db.fetch(query, *values)