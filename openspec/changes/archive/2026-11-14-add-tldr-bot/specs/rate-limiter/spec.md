# Spec Delta

## Purpose

Enforces per-chat rate limiting on summary requests and serves previously generated summaries when throttled.

## ADDED Requirements

### Requirement: Per-chat rate limit enforcement
The bot SHALL enforce a maximum of one successful summary request per 5-minute window for each chat. In Telegram groups supporting forum topics, a chat context is uniquely identified by the tuple of group chat ID and forum topic (`message_thread_id`); in groups without forum topics, it is identified by the group chat ID alone (`message_thread_id` is null).

#### Scenario: Request within cooldown window in a topic
- **WHEN** a user requests `/tldr` within 5 minutes of a previous request in the same forum topic thread of a group chat and a previous summary is cached for that topic
- **THEN** the bot replies indicating the 5-minute cooldown and appends the last generated summary for that topic thread

#### Scenario: Request in a different topic of the same group
- **WHEN** a user requests `/tldr` in topic A and shortly after another user requests `/tldr` in topic B of the same group chat
- **THEN** the cooldown in topic A does not throttle topic B

#### Scenario: Request within cooldown window in non-topic group
- **WHEN** a user requests `/tldr` within 5 minutes of a previous request in a group without topics and a previous summary is cached
- **THEN** the bot replies indicating the 5-minute cooldown and appends the last generated summary for the chat
