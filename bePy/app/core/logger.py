"""
Centralized logging configuration

Provides consistent logging across the application, replacing print() statements.
"""
import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
  
    
    
    logger = logging.getLogger(name)
    
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    
    return logger


# Create a default logger 
app_logger = setup_logger("app")
