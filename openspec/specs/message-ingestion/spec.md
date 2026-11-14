# Message Ingestion Specification

## Purpose

Observes, extracts, and stores incoming group chat text messages in MongoDB with automated 30-day data retention, alerting on missing permissions.

## Requirements

### Requirement: Continuous message storage
The bot SHALL store incoming text messages from group chats in MongoDB with chat identification, message thread identifier (for forum topics), sender details, message timestamp, and a 30-day time-to-live (TTL) expiration.

#### Scenario: Storing valid group text message in a topic
- **WHEN** a user posts a text message in a specific forum topic of an observed group chat
- **THEN** the system persists the message content, sender identifier, chat ID, message thread ID (`message_thread_id`), and timestamp into MongoDB with TTL expiration set to 30 days

#### Scenario: Storing valid group text message without topic
- **WHEN** a user posts a text message in a group chat without topics or in the general topic
- **THEN** the system persists the message with `message_thread_id` set to null (or root thread ID)

#### Scenario: Ignoring non-text and system messages
- **WHEN** a user posts media without text, stickers, or a system event occurs
- **THEN** the system ignores the event and does not store an empty message in the database

### Requirement: Missing message access detection
The bot SHALL evaluate its member permissions upon being added to a chat and notify admins if message reading rights are not granted.

#### Scenario: Bot added without admin rights
- **WHEN** the bot is added to a group chat as a regular member while Telegram Bot Privacy Mode is active
- **THEN** the bot posts a warning instructing chat admins to grant admin rights or disable privacy mode in BotFather
