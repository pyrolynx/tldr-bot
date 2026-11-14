import logging
import sys
from typing import Any
import structlog


def setup_logging(log_level: str = "INFO", log_format: str = "plain"):
    """
    Configures structlog and routes standard library loggers (like aiogram) through structlog.
    Supports:
      - JSON or plain/console formatted logs
      - Log levels (DEBUG, INFO, etc.)
      - Keyword arguments as primary structured payload
      - Interception of standard library loggers (e.g. aiogram, asyncio)
    """
    level_num = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format.lower() == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=False)

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(level_num)

    # Route aiogram, asyncio and other standard loggers into root handler
    for logger_name in ("aiogram", "aiogram.event", "aiogram.dispatcher", "asyncio"):
        log_instance = logging.getLogger(logger_name)
        log_instance.handlers = []
        log_instance.propagate = True
        log_instance.setLevel(level_num)

    # Keep chatty network drivers at warning
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name)
