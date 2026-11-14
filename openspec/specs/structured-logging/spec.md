# Structured Logging Specification

## Purpose

Provides configurable structured and verbose application logging using structlog for debugging operational events across all bot scenarios.

## Requirements

### Requirement: Configurable log format
The bot SHALL support configurable structured logging formats (JSON and plaintext/console) and configurable log levels.

#### Scenario: Plaintext logging configuration
- **WHEN** the application is configured with log format "plain"
- **THEN** the system outputs human-readable console log entries with timestamps, log level, message, and contextual key-values

#### Scenario: JSON structured logging configuration
- **WHEN** the application is configured with log format "json"
- **THEN** the system outputs single-line JSON log objects containing standard fields and contextual key-values

### Requirement: Positional and keyword argument logging support
The bot logger SHALL support both standard positional printf-style arguments and keyword structured arguments in log calls.

#### Scenario: Logger accepts positional and keyword arguments
- **WHEN** a log call is invoked with positional arguments (e.g., `logger.info("Processed %d items for chat", count, chat_id=123)`)
- **THEN** the logger formats the positional arguments into the event message and includes the keyword attributes in the structured event dictionary
