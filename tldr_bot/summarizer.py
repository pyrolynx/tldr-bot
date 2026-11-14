from datetime import datetime
from typing import List, Dict, Any
from openai import AsyncOpenAI
from tldr_bot.logger import get_logger

logger = get_logger("tldr_bot.summarizer")


class SummarizerService:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    def format_chat_history(self, messages: List[Dict[str, Any]]) -> str:
        """Format list of message dicts into chronological transcript for prompt."""
        lines = []
        for msg in messages:
            sender = msg.get("username") or msg.get("full_name") or "User"
            # Format timestamp if present
            date_val = msg.get("date")
            time_prefix = ""
            if isinstance(date_val, datetime):
                # Format as YYYY-MM-DD HH:MM UTC
                time_str = date_val.strftime("%Y-%m-%d %H:%M UTC")
                time_prefix = f"[{time_str}] "
            elif date_val:
                time_prefix = f"[{date_val}] "

            # Sanitize multiline messages to avoid confusing formatting
            text = (msg.get("text") or "").replace("\n", " ").strip()
            if text:
                lines.append(f"{time_prefix}[{sender}]: {text}")
        return "\n".join(lines)

    async def summarize_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Generates a summary of the provided messages using OpenAI."""
        if not messages:
            return "No messages to summarize."

        transcript = self.format_chat_history(messages)
        logger.debug(
            "Calling OpenAI chat completions",
            model=self.model,
            transcript_chars=len(transcript),
            message_count=len(messages),
        )

        system_prompt = (
            "You are a helpful assistant providing TLDR summaries for a Telegram group chat. "
            "Given the chronological conversation log below, write a clear, concise, and structured summary. "
            "Highlight key discussion points, important decisions, shared links, and any unresolved questions. "
            "Keep the tone friendly, informative, and easy to skim. Format using Telegram-friendly Markdown. "
            "IMPORTANT: Write the summary in the same language as the conversation messages. "
            "If multiple languages are used in the messages, write the entire summary in the one that was used the most."
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Here is the chat history:\n\n{transcript}",
                },
            ],
            temperature=0.4,
            max_tokens=800,
        )

        logger.debug("Received OpenAI completion response", model=self.model)
        return response.choices[0].message.content.strip()
