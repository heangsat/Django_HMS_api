"""
Debugging and logging utilities for performance monitoring and request tracking.
"""
import logging
import time
from functools import wraps
from django.db import connection
from django.db.utils import DEFAULT_DB_ALIAS

logger = logging.getLogger("hospital_api")

# Configure logger
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class QueryCounter:
    """Helper class to count and display database queries."""
    
    def __init__(self):
        self.initial_queries = len(connection.queries)
    
    def count(self):
        """Get number of queries executed."""
        return len(connection.queries) - self.initial_queries
    
    def get_queries(self):
        """Get all queries executed."""
        return connection.queries[self.initial_queries:]
    
    def print_summary(self, operation_name: str = "Operation"):
        """Print summary of queries executed."""
        queries = self.get_queries()
        count = len(queries)
        
        total_time = sum(float(q.get('time', 0)) for q in queries)
        logger.debug(f"{operation_name}: {count} queries, {total_time:.3f}s total")
        
        if count > 5:  # Warn if many queries
            logger.warning(f"HIGH QUERY COUNT: {operation_name} executed {count} queries")
        
        return count, total_time


def debug_request(operation_name: str = "Request", log_queries: bool = False):
    """
    Decorator to log request execution time and optionally database queries.
    
    Args:
        operation_name: Name of operation for logging
        log_queries: Whether to log database queries (use only during debug)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            query_counter = QueryCounter() if log_queries else None
            
            try:
                result = func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                logger.info(f"{operation_name} completed in {elapsed:.3f}s")
                
                if query_counter:
                    query_counter.print_summary(operation_name)
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{operation_name} failed after {elapsed:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


def log_request_details(request, method: str, endpoint: str):
    """Log detailed request information."""
    logger.info(f"{method} {endpoint}")
    logger.debug(f"Query params: {request.GET.dict()}")
    if hasattr(request, 'POST'):
        logger.debug(f"User: {request.user}")


def log_response_details(status_code: int, data: dict = None):
    """Log response details."""
    logger.info(f"Response: {status_code}")
    if data and isinstance(data, dict):
        logger.debug(f"Response size: {len(str(data))} bytes")


def get_db_query_log():
    """Get all database queries executed in this request (for debugging)."""
    return [
        {
            "sql": q["sql"],
            "time": float(q["time"]),
        }
        for q in connection.queries
    ]


class PerformanceMonitor:
    """Context manager for monitoring operation performance."""
    
    def __init__(self, operation_name: str, log_queries: bool = False):
        self.operation_name = operation_name
        self.log_queries = log_queries
        self.start_time = None
        self.query_counter = None
    
    def __enter__(self):
        self.start_time = time.time()
        if self.log_queries:
            self.query_counter = QueryCounter()
        logger.debug(f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        
        if exc_type is None:
            logger.info(f"{self.operation_name} completed in {elapsed:.3f}s")
            if self.query_counter:
                self.query_counter.print_summary(self.operation_name)
        else:
            logger.error(f"{self.operation_name} failed after {elapsed:.3f}s: {str(exc_val)}")
        
        return False  # Don't suppress exceptions
