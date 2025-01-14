# services/milvus_pool.py
from pymilvus import connections
from typing import Dict, Any
import threading
import time
import logging

class MilvusConnectionPool:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.connections = {}
        self.max_connections = 10
        self.connection_timeout = 300  # 5 minutes
        self.cleanup_interval = 60     # 1 minute
        self._initialized = True
        self._start_cleanup_thread()
        
        logging.info("Initialized Milvus connection pool")

    def get_connection(self, alias: str = "default") -> None:
        """
        Get a connection from the pool or create a new one
        """
        current_time = time.time()
        
        with self._lock:
            # Check if connection exists and is not expired
            if alias in self.connections:
                last_used = self.connections[alias]["last_used"]
                if current_time - last_used < self.connection_timeout:
                    self.connections[alias]["last_used"] = current_time
                    return
                else:
                    # Connection expired, remove it
                    self._remove_connection(alias)

            # Create new connection if under limit
            if len(self.connections) < self.max_connections:
                try:
                    connections.connect(
                        alias=alias,
                        host="localhost",
                        port="19530",
                        timeout=self.connection_timeout
                    )
                    self.connections[alias] = {
                        "last_used": current_time
                    }
                    logging.info(f"Created new Milvus connection: {alias}")
                except Exception as e:
                    logging.error(f"Failed to create Milvus connection: {str(e)}")
                    raise
            else:
                raise Exception("Maximum connection limit reached")

    def release_connection(self, alias: str = "default") -> None:
        """
        Release a connection back to the pool
        """
        with self._lock:
            if alias in self.connections:
                self.connections[alias]["last_used"] = time.time()

    def _remove_connection(self, alias: str) -> None:
        """
        Remove and close a connection
        """
        try:
            connections.disconnect(alias)
            del self.connections[alias]
            logging.info(f"Removed Milvus connection: {alias}")
        except Exception as e:
            logging.error(f"Error removing connection {alias}: {str(e)}")

    def _cleanup_expired_connections(self) -> None:
        """
        Remove expired connections
        """
        current_time = time.time()
        with self._lock:
            expired = [
                alias for alias, data in self.connections.items()
                if current_time - data["last_used"] > self.connection_timeout
            ]
            for alias in expired:
                self._remove_connection(alias)

    def _start_cleanup_thread(self) -> None:
        """
        Start background thread for cleaning up expired connections
        """
        def cleanup_worker():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired_connections()

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()