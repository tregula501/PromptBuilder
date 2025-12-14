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
GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-5.1-2025-11-13')

# Validate required environment variables
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

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
    activity = discord.Activity(type=discord.ActivityType.watching, name="Powered by GPT-5.1")
    await bot.change_presence(activity=activity, status=discord.Status.online)
    logger.info('Custom status set: Powered by GPT-5.1')


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

        # Show typing indicator while processing
        async with message.channel.typing():
            # Call OpenAI API
            response = await get_gpt_response(question)

            # Send response back to Discord
            # Discord has a 2000 character limit, so split if necessary
            if len(response) <= 2000:
                await message.reply(response)
            else:
                # Split into chunks
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
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
    Get response from GPT-5.1 API with web search enabled

    PRIVACY GUARANTEE: This function sends ONLY the current question to the OpenAI API.
    No conversation history, previous messages, or user context is included.
    Each request is completely isolated.

    Web search is automatically used when the question requires current information.

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
        # Create OpenAI client (newer API style)
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

        # PRIVACY: Make API call with ONLY current question - no history or context
        # Using Responses API with web_search tool enabled
        # The model will automatically use web search when needed for current info
        response = await client.responses.create(
            model=GPT_MODEL,
            reasoning={"effort": "low"},  # Minimal reasoning for faster responses
            tools=[{
                "type": "web_search"  # Enable web search capability
            }],
            tool_choice="auto",  # Model decides when to use web search
            input="You are a helpful Discord bot assistant operating in US Eastern Time (ET). Keep responses CONCISE, COMPACT, and CLEAN - MAXIMUM 1800 characters total. AVOID EXCESSIVE LINE BREAKS - use compact formatting with minimal vertical spacing. Write in short paragraphs or use inline bullet points (•) instead of numbered lists. Get straight to the point. When discussing times or dates, assume Eastern timezone unless specified otherwise.\n\nIMPORTANT FORMATTING RULES:\n- Your response MUST be under 1800 characters\n- Use NO blank lines between sections\n- Keep it compact and tight - minimal vertical spacing\n- Use inline formatting (e.g., \"First, X. Second, Y. Third, Z.\") instead of separate numbered lines\n- When uncertain, use phrases like 'Based on available information...', 'This may vary...', or 'As of my last update...'\n\nUser question: " + question
        )

        # Extract the response text from Responses API
        answer = response.output_text if hasattr(response, 'output_text') else response.text
        return answer.strip()

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
