# Discord GPT-5.1 Bot

A Discord bot powered by OpenAI's GPT-5.1 that responds to mentions with AI-generated answers.

## Features

- Responds to @mentions in all channels
- Uses OpenAI's GPT-5.1 model (gpt-5.1-2025-11-13)
- Shows typing indicator while generating responses
- Robust error handling with user-friendly messages
- Fully containerized with Docker
- Easy deployment with docker-compose

## Prerequisites

- Docker and Docker Compose installed
- Discord account with permissions to create bots
- OpenAI API key with access to GPT-5.1

## Setup Instructions

### 1. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "PizzaBot")
3. Navigate to the "Bot" section in the left sidebar
4. Click "Add Bot" and confirm
5. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent (optional)
6. Click "Reset Token" and copy the token (save it securely)

### 2. Generate Bot Invite URL

1. In the Discord Developer Portal, go to "OAuth2" > "URL Generator"
2. Select the following scopes:
   - `bot`
3. Select the following bot permissions:
   - Read Messages/View Channels
   - Send Messages
   - Read Message History
4. Copy the generated URL at the bottom
5. Open the URL in your browser and invite the bot to your server

### 3. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the API key (save it securely - you won't see it again)

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   DISCORD_BOT_TOKEN=your_actual_discord_token_here
   OPENAI_API_KEY=your_actual_openai_key_here
   GPT_MODEL=gpt-5.1-2025-11-13
   ```

### 5. Run the Bot

#### Using Docker Compose (Recommended)

```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

#### Using Docker Directly

```bash
# Build the image
docker build -t discord-gpt-bot .

# Run the container
docker run -d \
  --name discord-gpt-bot \
  --env-file .env \
  --restart unless-stopped \
  discord-gpt-bot

# View logs
docker logs -f discord-gpt-bot

# Stop the bot
docker stop discord-gpt-bot
```

## Usage

Once the bot is running and invited to your server, simply mention it in any channel with a question:

```
@PizzaBot what day does Christmas fall on this year?
```

The bot will:
1. Show a typing indicator
2. Process your question with GPT-5.1
3. Reply with an AI-generated answer

## Troubleshooting

### Bot doesn't respond to mentions

- Verify the bot has the "Message Content Intent" enabled in Discord Developer Portal
- Check that the bot has permission to read and send messages in the channel
- Review logs: `docker-compose logs -f`

### Authentication errors

- Verify your `DISCORD_BOT_TOKEN` is correct in `.env`
- Verify your `OPENAI_API_KEY` is correct in `.env`
- Make sure you copied the tokens correctly without extra spaces

### Rate limit errors

- OpenAI has rate limits based on your API plan
- Consider implementing request queuing or rate limiting
- Check your OpenAI usage dashboard

### Bot is offline

- Check if the container is running: `docker-compose ps`
- Check logs for errors: `docker-compose logs -f`
- Restart the bot: `docker-compose restart`

## Project Structure

```
discord-gpt-bot/
├── bot.py                 # Main bot logic
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Docker Compose setup
├── .env.example          # Environment variable template
├── .dockerignore         # Docker build exclusions
└── README.md            # This file
```

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | - | Your Discord bot token |
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `GPT_MODEL` | No | `gpt-5.1-2025-11-13` | OpenAI model to use |

### Customization

You can customize the bot by editing `bot.py`:

- **System prompt**: Modify the system message in `get_gpt_response()` to change the bot's personality
- **Max tokens**: Adjust `max_tokens` parameter to control response length
- **Temperature**: Change `temperature` (0.0-2.0) to make responses more creative or focused

## Security Notes

- Never commit your `.env` file to version control
- Keep your Discord bot token and OpenAI API key secure
- The bot runs as a non-root user inside the container for security
- Consider implementing rate limiting for production use

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Review Discord Developer Portal settings
3. Verify OpenAI API key permissions
4. Check OpenAI API status page

## Updates

To update the bot:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```
