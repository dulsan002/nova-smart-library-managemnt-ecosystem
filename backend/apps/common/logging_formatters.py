"""
Nova — JSON Log Formatter
============================
Structured JSON logging for production use.
"""

import json
import logging
import traceback
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON objects for structured logging.
    Compatible with log aggregation systems (ELK, Grafana Loki, etc.)
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }

        # Add process/thread info
        log_entry['process'] = record.process
        log_entry['thread'] = record.thread

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info),
            }

        # Add extra context if available
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'relativeCreated',
            'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
            'pathname', 'filename', 'module', 'thread', 'threadName',
            'process', 'processName', 'levelname', 'levelno', 'message',
            'msecs',
        }

        extra = {}
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                try:
                    json.dumps(value)  # Check if serializable
                    extra[key] = value
                except (TypeError, ValueError):
                    extra[key] = str(value)

        if extra:
            log_entry['context'] = extra

        return json.dumps(log_entry, default=str)
