import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Format log records as JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        # working on the base log structure / template
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc
            ).isoformat(),
            "message": record.getMessage(),
            "level": record.levelname,
            "name": record.name,
            "module": record.module,
            "function": record.funcName,
            "line_number": record.lineno,
        }

        # format exception traceback if present
        if record.exc_info:
            log_payload['exception'] = self.formatException(record.exc_info)

        # merge custom dict/context
        for key, value in record.__dict__.items():
            if key not in [
                'args', 'asctime', 'created', 'exc_info', 'exc_text', 
                'filename', 'funcName', 'levelname', 'levelno',
                'lineno', 'module', 'msecs', 'message', 'msg',
                'name', 'pathname', 'process', 'processName',
                'relativeCreated', 'stack_info', 'thread', 'threadName',
            ]:
                log_payload[key] = value

        return json.dumps(log_payload, ensure_ascii=False)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """configure and return a logger instance"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # prevents duplicate handlers when called multiple times
    if logger.hasHandlers():
        return logger

    # create JSON formatter
    formatter = JSONFormatter()

    # console / standard out handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(formatter)

    # add handler to logger
    logger.addHandler(stdout_handler)

    return logger

# expose a logger for convenience
logger = setup_logger('fastapi-book-project')