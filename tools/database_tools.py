"""
Database tools for agents to query databases, inspect schemas, and test migrations
"""
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from tools.code_tools import ToolResult
from agents.timeout_config import TIMEOUT_CONFIG


class DatabaseTools:
    """Tools for database operations with security restrictions"""
    
    # Supported database types
    SUPPORTED_DATABASES = ['postgresql', 'mysql', 'sqlite', 'sqlite3']
    
    @staticmethod
    def _parse_connection_string(connection_string: str) -> Dict[str, str]:
        """
        Parse database connection string.
        
        Supports:
        - postgresql://user:pass@host:port/db
        - mysql://user:pass@host:port/db
        - sqlite:///path/to/db
        - sqlite3:///path/to/db
        """
        try:
            # Extract protocol
            if '://' in connection_string:
                protocol, rest = connection_string.split('://', 1)
            else:
                # Assume sqlite if no protocol
                protocol = 'sqlite3'
                rest = connection_string
            
            result = {'protocol': protocol.lower()}
            
            if protocol.lower() in ['sqlite', 'sqlite3']:
                # SQLite: sqlite:///path/to/db
                result['database'] = rest.lstrip('/')
                return result
            
            # PostgreSQL/MySQL: user:pass@host:port/db
            # Extract credentials
            if '@' in rest:
                creds, location = rest.split('@', 1)
                if ':' in creds:
                    result['user'], result['password'] = creds.split(':', 1)
                else:
                    result['user'] = creds
            
            # Extract host and port
            if '/' in location:
                host_port, result['database'] = location.split('/', 1)
                if ':' in host_port:
                    result['host'], result['port'] = host_port.split(':')
                else:
                    result['host'] = host_port
                    result['port'] = '5432' if protocol == 'postgresql' else '3306'
            else:
                result['host'] = location
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _is_read_only_query(sql: str) -> bool:
        """
        Check if SQL query is read-only (safe to execute).
        
        Args:
            sql: SQL query string
        
        Returns:
            True if read-only, False otherwise
        """
        sql_upper = sql.strip().upper()
        
        # Read-only keywords (SELECT, SHOW, DESCRIBE, EXPLAIN, etc.)
        read_only_keywords = [
            'SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN',
            'PRAGMA', 'WITH'  # WITH can be used for SELECT
        ]
        
        # Check if query starts with read-only keyword
        for keyword in read_only_keywords:
            if sql_upper.startswith(keyword):
                return True
        
        # Check if it's a WITH clause followed by SELECT
        if sql_upper.startswith('WITH'):
            return 'SELECT' in sql_upper
        
        # Write keywords (dangerous)
        write_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
            'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE', 'COMMIT',
            'ROLLBACK', 'EXEC', 'EXECUTE', 'CALL'
        ]
        
        # If contains write keywords, it's not read-only
        for keyword in write_keywords:
            if keyword in sql_upper:
                return False
        
        # Default: assume read-only if we can't determine
        return True
    
    @staticmethod
    def _execute_query(sql: str, connection_string: str, read_only: bool = True) -> ToolResult:
        """
        Execute SQL query using appropriate database driver.
        
        Security: Only executes read-only queries by default.
        
        Args:
            sql: SQL query string
            connection_string: Database connection string
            read_only: Whether to enforce read-only mode
        
        Returns:
            ToolResult with query results or error
        """
        try:
            # Parse connection string
            conn_info = DatabaseTools._parse_connection_string(connection_string)
            
            if 'error' in conn_info:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid connection string: {conn_info['error']}",
                    metadata={"connection_string": connection_string}
                )
            
            protocol = conn_info.get('protocol', 'sqlite')
            
            # Check if read-only
            if read_only:
                if not DatabaseTools._is_read_only_query(sql):
                    return ToolResult(
                        success=False,
                        result=None,
                        error="Query contains write operations (INSERT/UPDATE/DELETE). Only read-only queries allowed.",
                        metadata={"query": sql[:100]}
                    )
            
            # Execute based on database type
            if protocol in ['sqlite', 'sqlite3']:
                return DatabaseTools._execute_sqlite_query(sql, conn_info)
            elif protocol == 'postgresql':
                return DatabaseTools._execute_postgresql_query(sql, conn_info)
            elif protocol == 'mysql':
                return DatabaseTools._execute_mysql_query(sql, conn_info)
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unsupported database type: {protocol}. Supported: {', '.join(DatabaseTools.SUPPORTED_DATABASES)}",
                    metadata={"protocol": protocol}
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error executing query: {str(e)}",
                metadata={"query": sql[:100]}
            )
    
    @staticmethod
    def _execute_sqlite_query(sql: str, conn_info: Dict) -> ToolResult:
        """Execute SQLite query"""
        try:
            import sqlite3
            
            db_path = conn_info.get('database', ':memory:')
            if not Path(db_path).exists() and db_path != ':memory:':
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Database file not found: {db_path}",
                    metadata={"database": db_path}
                )
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Return dict-like rows
            cursor = conn.cursor()
            
            try:
                cursor.execute(sql)
                
                if sql.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    # Convert to list of dicts
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    results = [dict(row) for row in rows]
                    
                    return ToolResult(
                        success=True,
                        result=results,
                        metadata={
                            "rows": len(results),
                            "columns": columns,
                            "database": db_path
                        }
                    )
                else:
                    conn.commit()
                    return ToolResult(
                        success=True,
                        result="Query executed successfully",
                        metadata={"database": db_path}
                    )
            finally:
                conn.close()
        
        except ImportError:
            return ToolResult(
                success=False,
                result=None,
                error="sqlite3 module not available",
                metadata={}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"SQLite error: {str(e)}",
                metadata={"database": conn_info.get('database')}
            )
    
    @staticmethod
    def _execute_postgresql_query(sql: str, conn_info: Dict) -> ToolResult:
        """Execute PostgreSQL query (requires psycopg2)"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Build connection string
            conn_params = {
                'host': conn_info.get('host', 'localhost'),
                'port': conn_info.get('port', '5432'),
                'database': conn_info.get('database'),
                'user': conn_info.get('user'),
                'password': conn_info.get('password'),
            }
            
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            try:
                cursor.execute(sql)
                
                if sql.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    results = [dict(row) for row in rows]
                    
                    return ToolResult(
                        success=True,
                        result=results,
                        metadata={
                            "rows": len(results),
                            "database": conn_params['database']
                        }
                    )
                else:
                    conn.commit()
                    return ToolResult(
                        success=True,
                        result="Query executed successfully",
                        metadata={"database": conn_params['database']}
                    )
            finally:
                conn.close()
        
        except ImportError:
            return ToolResult(
                success=False,
                result=None,
                error="psycopg2 not installed. Install with: pip install psycopg2-binary",
                metadata={"install_hint": "pip install psycopg2-binary"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"PostgreSQL error: {str(e)}",
                metadata={"database": conn_info.get('database')}
            )
    
    @staticmethod
    def _execute_mysql_query(sql: str, conn_info: Dict) -> ToolResult:
        """Execute MySQL query (requires pymysql or mysql-connector)"""
        try:
            import pymysql
            
            conn = pymysql.connect(
                host=conn_info.get('host', 'localhost'),
                port=int(conn_info.get('port', 3306)),
                user=conn_info.get('user'),
                password=conn_info.get('password'),
                database=conn_info.get('database'),
                cursorclass=pymysql.cursors.DictCursor
            )
            
            cursor = conn.cursor()
            
            try:
                cursor.execute(sql)
                
                if sql.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    results = [dict(row) for row in rows]
                    
                    return ToolResult(
                        success=True,
                        result=results,
                        metadata={
                            "rows": len(results),
                            "database": conn_info.get('database')
                        }
                    )
                else:
                    conn.commit()
                    return ToolResult(
                        success=True,
                        result="Query executed successfully",
                        metadata={"database": conn_info.get('database')}
                    )
            finally:
                conn.close()
        
        except ImportError:
            return ToolResult(
                success=False,
                result=None,
                error="pymysql not installed. Install with: pip install pymysql",
                metadata={"install_hint": "pip install pymysql"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"MySQL error: {str(e)}",
                metadata={"database": conn_info.get('database')}
            )
    
    @staticmethod
    def connect(connection_string: str) -> ToolResult:
        """
        Test database connection.
        
        Security: Only tests connection, doesn't modify database.
        
        Usage from agent:
        TOOL: connect
        INPUT: <connection_string>
        
        Args:
            connection_string: Database connection string
        
        Returns:
            ToolResult with connection status
        """
        try:
            conn_info = DatabaseTools._parse_connection_string(connection_string)
            
            if 'error' in conn_info:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid connection string: {conn_info['error']}",
                    metadata={"connection_string": connection_string}
                )
            
            protocol = conn_info.get('protocol', 'sqlite')
            
            # Test connection based on database type
            if protocol in ['sqlite', 'sqlite3']:
                db_path = conn_info.get('database', ':memory:')
                if db_path != ':memory:' and not Path(db_path).exists():
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Database file not found: {db_path}",
                        metadata={"database": db_path}
                    )
                
                try:
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    conn.close()
                    return ToolResult(
                        success=True,
                        result=f"Successfully connected to SQLite database: {db_path}",
                        metadata={"protocol": protocol, "database": db_path}
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Connection failed: {str(e)}",
                        metadata={"database": db_path}
                    )
            
            elif protocol == 'postgresql':
                # For PostgreSQL, try a simple SELECT
                query_result = DatabaseTools._execute_postgresql_query("SELECT 1", conn_info)
                if query_result.success:
                    return ToolResult(
                        success=True,
                        result=f"Successfully connected to PostgreSQL database: {conn_info.get('database')}",
                        metadata={"protocol": protocol, "database": conn_info.get('database')}
                    )
                else:
                    return query_result
            
            elif protocol == 'mysql':
                # For MySQL, try a simple SELECT
                query_result = DatabaseTools._execute_mysql_query("SELECT 1", conn_info)
                if query_result.success:
                    return ToolResult(
                        success=True,
                        result=f"Successfully connected to MySQL database: {conn_info.get('database')}",
                        metadata={"protocol": protocol, "database": conn_info.get('database')}
                    )
                else:
                    return query_result
            
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unsupported database type: {protocol}",
                    metadata={"protocol": protocol}
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Connection error: {str(e)}",
                metadata={"connection_string": connection_string}
            )
    
    @staticmethod
    def query(sql: str, connection_string: str, read_only: bool = True) -> ToolResult:
        """
        Execute SQL query (read-only by default).
        
        Security: Only executes SELECT/SHOW/DESCRIBE queries by default.
        
        Usage from agent:
        TOOL: query
        INPUT: <sql>\n<connection_string>
        
        Args:
            sql: SQL query string
            connection_string: Database connection string
            read_only: Whether to enforce read-only mode (default: True)
        
        Returns:
            ToolResult with query results or error
        """
        return DatabaseTools._execute_query(sql, connection_string, read_only=read_only)
    
    @staticmethod
    def get_schema(table_name: str, connection_string: str) -> ToolResult:
        """
        Get table schema (columns, types, constraints).
        
        Usage from agent:
        TOOL: get_schema
        INPUT: <table_name>\n<connection_string>
        
        Args:
            table_name: Name of table
            connection_string: Database connection string
        
        Returns:
            ToolResult with schema information
        """
        try:
            conn_info = DatabaseTools._parse_connection_string(connection_string)
            protocol = conn_info.get('protocol', 'sqlite')
            
            # Generate schema query based on database type
            if protocol in ['sqlite', 'sqlite3']:
                sql = f"PRAGMA table_info({table_name})"
            elif protocol == 'postgresql':
                sql = f"""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
                """
            elif protocol == 'mysql':
                sql = f"DESCRIBE {table_name}"
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unsupported database type: {protocol}",
                    metadata={"protocol": protocol}
                )
            
            return DatabaseTools._execute_query(sql, connection_string, read_only=True)
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error getting schema: {str(e)}",
                metadata={"table_name": table_name}
            )
    
    @staticmethod
    def list_tables(connection_string: str) -> ToolResult:
        """
        List all tables in database.
        
        Usage from agent:
        TOOL: list_tables
        INPUT: <connection_string>
        
        Args:
            connection_string: Database connection string
        
        Returns:
            ToolResult with list of table names
        """
        try:
            conn_info = DatabaseTools._parse_connection_string(connection_string)
            protocol = conn_info.get('protocol', 'sqlite')
            
            # Generate list tables query based on database type
            if protocol in ['sqlite', 'sqlite3']:
                sql = "SELECT name as table_name FROM sqlite_master WHERE type='table'"
            elif protocol == 'postgresql':
                sql = """
                SELECT table_name 
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            elif protocol == 'mysql':
                sql = "SHOW TABLES"
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unsupported database type: {protocol}",
                    metadata={"protocol": protocol}
                )
            
            return DatabaseTools._execute_query(sql, connection_string, read_only=True)
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error listing tables: {str(e)}",
                metadata={}
            )

