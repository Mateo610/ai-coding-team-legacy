"""
Consolidated Database Tools
Replaces: db_get_schema, db_list_tables, db_query
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.database_tools import DatabaseTools


class DBTools:
    """Consolidated database tools with mode-based operations"""
    
    @staticmethod
    def db_introspect(connection_string: str, mode: str = "schema", table_name: str = None) -> ToolResult:
        """
        Query schema-level database info.
        
        Replaces: db_get_schema, db_list_tables
        
        Args:
            connection_string: Database connection string
            mode: Operation mode:
                - "schema" (default): Get database schema
                - "tables": List all tables
            table_name: Optional table name for schema mode
        
        Returns:
            ToolResult with schema or table list based on mode
        
        Examples:
            db_introspect("sqlite:///test.db", mode="schema")  # Get schema
            db_introspect("sqlite:///test.db", mode="tables")  # List tables
            db_introspect("sqlite:///test.db", mode="schema", table_name="users")  # Get specific table schema
        """
        try:
            if mode == "schema":
                # Use DatabaseTools.db_get_schema
                result = DatabaseTools.db_get_schema(connection_string, table_name=table_name)
                return result
            elif mode == "tables":
                # Use DatabaseTools.db_list_tables
                result = DatabaseTools.db_list_tables(connection_string)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'schema', 'tables'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in db_introspect with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def db_query(connection_string: str, query: str, read_only: bool = True) -> ToolResult:
        """
        Read-only SQL execution with limit guardrails.
        
        Replaces: db_query (consolidated wrapper)
        
        Args:
            connection_string: Database connection string
            query: SQL query to execute
            read_only: Whether query should be read-only (default: True)
        
        Returns:
            ToolResult with query results
        
        Examples:
            db_query("sqlite:///test.db", "SELECT * FROM users LIMIT 10")  # Read-only query
        """
        try:
            # Use DatabaseTools.db_query
            result = DatabaseTools.db_query(connection_string, query, read_only=read_only)
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in db_query: {str(e)}"
            )

