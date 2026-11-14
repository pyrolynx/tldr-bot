# TLDR Summary Specification

## Purpose

Handles the /tldr command, validates request parameters, formats message history, and queries OpenAI for conversation summaries.

## Requirements

### Requirement: Range validation for summary requests
The bot SHALL validate the requested message count $N$ against bounds of 50 to 1000, replying with designated responses when outside bounds.

#### Scenario: Requested count below minimum
- **WHEN** a user invokes `/tldr` with $N < 50$
- **THEN** the bot replies with the message "Just read it, bro"

#### Scenario: Requested count above maximum
- **WHEN** a user invokes `/tldr` with $N > 1000$
- **THEN** the bot replies with the message "It's too much, pay for my tokens first!"

### Requirement: AI-powered summary generation
The bot SHALL retrieve the last $N$ stored text messages for the specific topic/thread where the command was issued in chronological order, format them for OpenAI, and reply with the generated summary inside that same topic.

#### Scenario: Successful summary generation inside a topic
- **WHEN** a user invokes `/tldr <N>` with $50 \le N \le 1000$ inside a forum topic in an activated chat under rate limits
- **THEN** the system retrieves the last $N$ text messages belonging to that specific topic (`message_thread_id`), submits them to OpenAI, updates the cached last summary for that topic, and replies within that same topic

#### Scenario: Successful summary generation in regular chat
- **WHEN** a user invokes `/tldr <N>` in a non-forum chat or the general topic
- **THEN** the system retrieves the last $N$ text messages for that chat/thread and replies with the summary

#### Scenario: Insufficient messages stored in topic
- **WHEN** a user requests a summary of $N$ messages, but the topic history contains fewer than 50 messages
- **THEN** the bot replies that not enough messages have been recorded yet in this topic to generate a summary

### Requirement: Language consistency in summaries
The bot SHALL generate the summary in the same language as the original messages posted in the conversation. When multiple languages are used across the messages, the summary SHALL be generated in the language that was used the most (predominant language).

#### Scenario: Unilingual message history
- **WHEN** messages in the summarized history are written in a specific language (e.g., Ukrainian, Spanish, German)
- **THEN** the AI summary is generated entirely in that same language

#### Scenario: Multilingual message history
- **WHEN** messages in the summarized history are written in a mix of different languages
- **THEN** the AI summary is generated entirely in the language that appears most predominantly in the conversation

### Requirement: Timestamped conversation transcripts
The bot SHALL include each message's timestamp (in UTC format `YYYY-MM-DD HH:MM UTC`) in the formatted conversation transcript submitted to OpenAI, enabling the summarizer to understand the temporal sequence, intervals, and timing of events.

#### Scenario: Message formatting with timestamp
- **WHEN** messages are formatted for AI summarization
- **THEN** each message entry contains its timestamp, sender identifier, and message text (e.g. `[2026-11-14 17:00 UTC] [alice]: Hello`)
