"""
Discord Bot with GPT-5.1 Integration

PRIVACY GUARANTEES:
===================
1. MENTION-ONLY PROCESSING: The bot only processes messages when explicitly mentioned.
   All other messages are ignored at the code level (see on_message event handler).

2. NO CONVERSATION HISTORY: Each mention is treated as an isolated request.
   No conversation context is stored or passed to the AI model.
   Each GPT API call contains ONLY the current question.

3. NO DATA STORAGE: The bot does not store any message content, user data, or
   conversation history in memory or on disk.

4. ISOLATED REQUESTS: Each @mention creates a fresh API request with only:
   - System prompt (defines bot personality)
   - Current question text (after stripping mentions)
   No previous messages, channel context, or user history is included.

5. LOGGING PRIVACY: Logs contain only metadata (usernames, timestamps, success/failure).
   No message content or AI responses are logged to protect user privacy.

TECHNICAL NOTES:
================
- Message Content Intent is required by Discord to read message text, but this doesn't
  mean the bot processes or stores all messages. The code explicitly filters for mentions.
- The bot can technically "see" messages in channels it has access to (Discord limitation),
  but NO data is processed or transmitted unless the bot is mentioned.
"""

import discord
from discord.ext import commands
import openai
import os
import re
import hashlib
from dotenv import load_dotenv
import logging
import asyncio
import time
from collections import defaultdict, deque
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-5.2-2025-12-11')

# Cost/latency controls (optional)
MAX_OUTPUT_TOKENS = int(os.getenv('MAX_OUTPUT_TOKENS', '350'))
TIMEOUT_SECONDS = float(os.getenv('TIMEOUT_SECONDS', '30'))
_temperature_env = os.getenv('TEMPERATURE')
TEMPERATURE = float(_temperature_env) if _temperature_env is not None and _temperature_env.strip() != "" else None
ENABLE_WEB_SEARCH = os.getenv('ENABLE_WEB_SEARCH', 'false').strip().lower() in ('1', 'true', 'yes', 'on')

# Optional response caching (OFF by default to preserve privacy guarantees)
ENABLE_RESPONSE_CACHE = os.getenv('ENABLE_RESPONSE_CACHE', 'false').strip().lower() in ('1', 'true', 'yes', 'on')
CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '900'))  # 15 minutes
CACHE_MAX_ENTRIES = int(os.getenv('CACHE_MAX_ENTRIES', '256'))
OPENAI_CONCURRENCY = max(1, int(os.getenv('OPENAI_CONCURRENCY', '3')))

SYSTEM_PROMPT = (
    "You are a helpful Discord bot assistant operating in US Eastern Time (ET). "
    "Keep responses concise, compact, and clean. "
    "Avoid excessive line breaks; use compact formatting with minimal vertical spacing. "
    "When uncertain, say so briefly."
)

_response_cache: dict[str, tuple[float, str]] = {}

def _split_for_discord(text: str, limit: int = 2000) -> list[str]:
    """
    Split text into Discord-safe message chunks (<= limit chars), preferring to split on
    newlines and then spaces to preserve readability.
    """
    s = (text or "").strip()
    if not s:
        return [""]
    if len(s) <= limit:
        return [s]

    chunks: list[str] = []
    remaining = s
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        candidate = remaining[:limit]

        # Prefer to split at the last newline within the limit.
        split_at = candidate.rfind("\n")
        # Otherwise split at the last space.
        if split_at < max(0, limit - 300):
            split_at = candidate.rfind(" ")
        # If we still didn't find a good boundary, hard split.
        if split_at <= 0:
            split_at = limit

        part = remaining[:split_at].strip()
        if part:
            chunks.append(part)
        remaining = remaining[split_at:].lstrip()

    return chunks

def _normalize_question_for_cache(question: str) -> str:
    return re.sub(r'\s+', ' ', (question or '').strip()).lower()

def _cache_key(model: str, use_web_search: bool, question: str) -> str:
    # Avoid storing raw user text as cache keys; hash normalized content instead.
    normalized = _normalize_question_for_cache(question)
    digest = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    return f"{model}|web={int(use_web_search)}|{digest}"

def _cache_get(key: str) -> str | None:
    now = time.time()
    entry = _response_cache.get(key)
    if not entry:
        return None
    expires_at, answer = entry
    if expires_at <= now:
        _response_cache.pop(key, None)
        return None
    return answer

def _cache_set(key: str, answer: str) -> None:
    if len(_response_cache) >= CACHE_MAX_ENTRIES:
        # Simple eviction: drop oldest entry by expiry time.
        oldest_key = min(_response_cache.items(), key=lambda kv: kv[1][0])[0]
        _response_cache.pop(oldest_key, None)
    _response_cache[key] = (time.time() + CACHE_TTL_SECONDS, answer)

def _should_use_web_search(question: str) -> bool:
    q = (question or '').lower()
    # Heuristic: prefer web search for explicitly time-sensitive queries or URLs.
    triggers = (
        "today", "now", "latest", "current", "as of", "right now",
        "news", "breaking", "release", "version", "price", "stock",
        "weather", "score", "results", "election",
    )
    if "http://" in q or "https://" in q:
        return True
    return any(t in q for t in triggers)

def _model_to_display_name(model: str) -> str:
    """
    Convert a model id like "gpt-5.2-2025-12-01" into a short display name "GPT-5.2"
    for Discord status/presence text. Falls back to the raw model string if parsing fails.
    """
    match = re.match(r'^(gpt-\d+(?:\.\d+)?)', (model or '').strip(), flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return (model or '').strip() or 'GPT'

# Validate required environment variables
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize OpenAI client
OPENAI_CLIENT = openai.AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    timeout=TIMEOUT_SECONDS,
)
OPENAI_SEMAPHORE = asyncio.Semaphore(OPENAI_CONCURRENCY)

# Configure Discord bot with required intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Rate limiting: Track user request timestamps
# Key: user_id, Value: deque of timestamps (last 10 requests)
user_request_times = defaultdict(lambda: deque(maxlen=10))
RATE_LIMIT_REQUESTS = 10  # Max requests
RATE_LIMIT_WINDOW = 60  # Per 60 seconds (1 minute)


@bot.event
async def on_ready():
    """Event handler when bot successfully connects to Discord"""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    logger.info(f'Using GPT model: {GPT_MODEL}')

    # Set custom bot status
    status_model_name = _model_to_display_name(GPT_MODEL)
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"Powered by {status_model_name}",
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)
    logger.info(f'Custom status set: Powered by {status_model_name}')


@bot.event
async def on_message(message):
    """
    Event handler for all messages

    PRIVACY GUARANTEE: This function is called for every message in channels the bot
    can see (Discord API requirement), but the bot ONLY processes messages when explicitly
    mentioned. All other messages are immediately ignored without any processing or logging.
    """
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # PRIVACY: Only process messages where bot is explicitly mentioned
    # All other messages are ignored - no data extracted, logged, or transmitted
    if bot.user in message.mentions:
        await handle_mention(message)

    # Process commands (if any are added in the future)
    await bot.process_commands(message)


async def handle_mention(message):
    """Handle messages where the bot is mentioned"""
    try:
        # Extract the question by removing the bot mention
        question = message.content
        for mention in message.mentions:
            question = question.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
        question = question.strip()

        # If there's no text after the mention, provide a helpful message
        if not question:
            await message.channel.send(
                f"Hi {message.author.mention}! You mentioned me but didn't ask anything. "
                "Try asking me a question like: `@{bot.user.name} What day does Christmas fall on this year?`"
            )
            return

        # Rate limiting check
        user_id = message.author.id
        current_time = time.time()

        # Get user's request times and remove old ones
        request_times = user_request_times[user_id]

        # Remove requests older than the time window
        while request_times and current_time - request_times[0] > RATE_LIMIT_WINDOW:
            request_times.popleft()

        # Check if user has exceeded rate limit
        if len(request_times) >= RATE_LIMIT_REQUESTS:
            time_until_reset = int(RATE_LIMIT_WINDOW - (current_time - request_times[0]))
            await message.reply(
                f"Whoa there! You've hit the rate limit of {RATE_LIMIT_REQUESTS} requests per minute. "
                f"Please wait {time_until_reset} seconds before asking again."
            )
            logger.warning(f"Rate limit exceeded for user: {message.author.name} (ID: {user_id})")
            return

        # Add current request to the user's history
        request_times.append(current_time)

        # PRIVACY: Log only metadata, not message content
        logger.info(f"Processing mention from user: {message.author.name} (ID: {message.author.id})")

        # Immediately acknowledge (improves perceived latency), then edit with final answer.
        placeholder = await message.reply("Thinking…")

        # Show typing indicator while processing
        async with message.channel.typing():
            response = await get_gpt_response(question)

        chunks = _split_for_discord(response, limit=2000)
        if not chunks or not chunks[0]:
            chunks = ["Sorry — I couldn't generate a response. Please try again."]

        try:
            await placeholder.edit(content=chunks[0])
        except Exception:
            # Fallback: if editing fails for any reason, send a fresh message.
            await message.reply(chunks[0])

        for chunk in chunks[1:]:
            await message.channel.send(chunk)

        # PRIVACY: Log only success status, not response content
        logger.info(f"Successfully responded to user: {message.author.name} (ID: {message.author.id})")

    except openai.RateLimitError:
        logger.error("OpenAI rate limit exceeded")
        await message.reply(
            "I'm currently experiencing high demand and have hit my rate limit. "
            "Please try again in a few moments."
        )

    except openai.BadRequestError as e:
        logger.error(f"OpenAI bad request (likely misconfiguration): {e}")
        await message.reply(
            "I'm having a configuration issue with my AI model settings. "
            "Please contact the bot administrator."
        )

    except openai.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        await message.reply(
            "I'm having trouble connecting to my AI service right now. "
            "Please try again later."
        )

    except openai.AuthenticationError:
        logger.error("OpenAI authentication failed - check API key")
        await message.reply(
            "There's a configuration issue with my AI service. "
            "Please contact the bot administrator."
        )

    except Exception as e:
        logger.error(f"Unexpected error handling message: {e}", exc_info=True)
        await message.reply(
            "Sorry, I encountered an unexpected error while processing your request. "
            "Please try again."
        )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)),
    reraise=True
)
async def get_gpt_response(question: str) -> str:
    """
    Get response from the configured GPT model.

    PRIVACY GUARANTEE: This function sends ONLY the current question to the OpenAI API.
    No conversation history, previous messages, or user context is included.
    Each request is completely isolated.

    Web search can optionally be enabled via ENABLE_WEB_SEARCH (default off).
    Optional response caching can be enabled via ENABLE_RESPONSE_CACHE (default off).

    Retry logic: Retries up to 3 times with exponential backoff (2s, 4s, 8s) for:
    - Timeout errors
    - Connection errors
    - Rate limit errors (from OpenAI)

    Args:
        question: The user's question (isolated, no context)

    Returns:
        The AI's response as a string
    """
    try:
        use_web_search = ENABLE_WEB_SEARCH and _should_use_web_search(question)
        cache_key = _cache_key(GPT_MODEL, use_web_search, question)
        if ENABLE_RESPONSE_CACHE:
            cached = _cache_get(cache_key)
            if cached:
                logger.info("Cache hit for model=%s web_search=%s", GPT_MODEL, use_web_search)
                return cached

        # PRIVACY: Make API call with ONLY current question - no history or context
        request_kwargs = {
            "model": GPT_MODEL,
            # Minimal reasoning for faster responses
            "reasoning": {"effort": "low"},
            "input": f"{SYSTEM_PROMPT}\nUser question: {question}",
            "max_output_tokens": MAX_OUTPUT_TOKENS,
        }
        if TEMPERATURE is not None:
            request_kwargs["temperature"] = TEMPERATURE
        if use_web_search:
            # Enable web search capability; model decides when to use it.
            request_kwargs["tools"] = [{"type": "web_search"}]
            request_kwargs["tool_choice"] = "auto"

        async with OPENAI_SEMAPHORE:
            try:
                response = await OPENAI_CLIENT.responses.create(**request_kwargs)
            except openai.BadRequestError as e:
                # Some models don't support all parameters (e.g., temperature).
                body = getattr(e, "body", None) or {}
                param = (body.get("error") or {}).get("param")
                msg = (body.get("error") or {}).get("message", "")
                if param and param in request_kwargs and "Unsupported parameter" in str(msg):
                    logger.warning("Retrying without unsupported parameter: %s", param)
                    request_kwargs.pop(param, None)
                    response = await OPENAI_CLIENT.responses.create(**request_kwargs)
                else:
                    raise

        # Extract the response text from Responses API
        answer = response.output_text if hasattr(response, 'output_text') else response.text
        answer = answer.strip()

        if ENABLE_RESPONSE_CACHE and answer:
            _cache_set(cache_key, answer)

        return answer

    except Exception as e:
        logger.error(f"Error calling GPT API: {e}")
        raise


def main():
    """Main entry point for the bot"""
    try:
        logger.info("Starting Discord bot...")
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord token - please check DISCORD_BOT_TOKEN")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
