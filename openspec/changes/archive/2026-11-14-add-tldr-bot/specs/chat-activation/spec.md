# Spec Delta

## Purpose

Provides single-use token verification and lifecycle activation controls for group chats before bot commands can be executed.

## ADDED Requirements

### Requirement: Chat activation with single-use token
The bot SHALL require unactivated group chats to submit a valid single-use token to enable bot features, marking the token as consumed upon successful activation.

#### Scenario: Successful chat activation
- **WHEN** an authorized user runs `/activate <token>` with a valid, unconsumed token in an unactivated group chat
- **THEN** the system marks the token as used, associates it with the chat ID, and replies with a success confirmation message activating the chat

#### Scenario: Activation attempt with invalid or consumed token
- **WHEN** a user runs `/activate <token>` with a non-existent or previously consumed token
- **THEN** the system rejects activation and replies with an invalid/consumed token warning message

### Requirement: Command blocking for unactivated chats
The bot SHALL block execution of operational commands in unactivated group chats and instruct users to activate.

#### Scenario: Command invoked in unactivated chat
- **WHEN** any command other than `/activate` (e.g. `/tldr`) is issued in an unactivated group chat
- **THEN** the bot replies stating the chat is not activated and provides instructions to run `/activate <token>`

### Requirement: Token generation via administrator direct message
The bot SHALL allow only the configured administrator (identified by Telegram username) to generate new single-use activation tokens via direct message with the bot.

#### Scenario: Administrator generates a token in DM
- **GIVEN** the user's Telegram username matches the configured administrator username
- **WHEN** the administrator sends `/generate_token` in a private chat with the bot
- **THEN** the bot generates a new unique token, saves it as unused in the database, and replies to the administrator with the token

#### Scenario: Non-administrator attempts token generation
- **WHEN** a user whose Telegram username does not match the configured administrator username sends `/generate_token` in a private chat
- **THEN** the bot rejects the request with an unauthorized warning message

#### Scenario: Token generation attempted in a group chat
- **WHEN** any user attempts `/generate_token` in a group or supergroup chat
- **THEN** the bot rejects the command and instructs that token generation is only permitted in direct messages

### Requirement: Chat migration handling on group upgrade
The bot SHALL detect Telegram group migration events (`migrate_to_chat_id` and `migrate_from_chat_id`) and automatically transfer chat activation status, message history, and cached summaries to the new chat ID.

#### Scenario: Automatic migration on group conversion to supergroup
- **WHEN** Telegram converts a basic group to a supergroup and sends a message containing `migrate_to_chat_id`
- **THEN** the system updates the chat activation record in `chats` to the new chat ID, updates all stored messages in `messages` to the new chat ID, and updates cached records in `summaries` to the new chat ID so service is seamlessly maintained without re-activation

#### Scenario: Message received in new supergroup referencing previous basic group
- **WHEN** Telegram sends a message in the newly created supergroup containing `migrate_from_chat_id`
- **THEN** the system verifies that activation and message records from `migrate_from_chat_id` are mapped to the new supergroup ID
