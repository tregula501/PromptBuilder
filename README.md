# PromptBuilder 🎯

**AI-Powered Sportsbook Betting Prompt Generator**

PromptBuilder is a powerful desktop application that generates comprehensive, AI-ready prompts for sports betting analysis. Built with Python and CustomTkinter, it combines data from multiple sources to create detailed prompts optimized for AI models like Claude, GPT-4, and others.

---

## Features

### Core Functionality
- **Multi-Sport Support**: NFL, NBA, MLB, NHL, Soccer, MMA, Tennis, and more
- **Multiple Data Sources**:
  - The Odds API integration (free tier available)
  - ESPN API for team stats
  - Web scraping capabilities for custom sources
  - Manual data entry option
- **Advanced Bet Configuration**:
  - All bet types: Moneyline, Spreads, Totals, Parlays, Props, Teasers
  - Maximum combined odds control
  - Risk tolerance settings
  - Bankroll management parameters
- **AI Model Optimization**: Format prompts for Claude, GPT-4, or generic AI models
- **GitHub Integration**:
  - Automatic prompt versioning
  - Configuration sync across devices
  - Commit history tracking

### Analysis Capabilities
- Value betting opportunity identification
- Comprehensive risk assessment
- Statistical predictions
- Trend analysis
- Injury impact evaluation
- Weather condition analysis

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git
- Chrome/Chromium (for web scraping)

### Setup Steps

1. **Clone the repository:**
```bash
git clone https://github.com/tregula501/PromptBuilder.git
cd PromptBuilder
```

2. **Create a virtual environment:**
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API keys
```

5. **Run the application:**
```bash
python app/main.py
```

---

## Configuration

### API Keys

#### The Odds API (Recommended)
1. Sign up at [https://the-odds-api.com/](https://the-odds-api.com/)
2. Get your free API key (500 requests/month)
3. Add to `.env`:
```
ODDS_API_KEY=your_key_here
```

#### GitHub Integration
1. Generate a Personal Access Token at [GitHub Settings](https://github.com/settings/tokens)
2. Add to `.env`:
```
GITHUB_TOKEN=your_token_here
GITHUB_USERNAME=your_username
GITHUB_REPO=PromptBuilder
```

### Custom Web Scraping
Configure custom scraping rules in the Data Sources tab:
- Add sportsbook URLs
- Define CSS selectors
- Set scraping delays to avoid rate limiting

---

## Usage Guide

### Quick Start

1. **Select Sports** (Sports Tab):
   - Choose which sports to analyze
   - Select specific leagues if needed

2. **Configure Bets** (Bet Config Tab):
   - Set maximum combined odds
   - Select bet types to include
   - Adjust risk tolerance
   - Configure bankroll parameters

3. **Choose Data Source** (Data Sources Tab):
   - API: Use The Odds API or ESPN
   - Web Scraping: Configure custom sources
   - Manual Entry: Paste your own data

4. **Generate Prompt** (Preview Tab):
   - Review the generated prompt
   - Edit if needed
   - Copy to clipboard or save

5. **Save & Commit** (Optional):
   - Save prompt to file
   - Auto-commit to GitHub
   - Track your prompt history

### Example Workflow

```
1. Select NFL and NBA in Sports tab
2. Set max combined odds to +400
3. Enable Parlay and Moneyline bet types
4. Fetch data from The Odds API
5. Generate prompt
6. Copy and paste into Claude/ChatGPT
7. Analyze AI recommendations
8. Save prompt for future reference
```

---

## Project Structure

```
PromptBuilder/
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── models.py           # Data models (Pydantic)
│   │   ├── data_fetcher.py     # API clients
│   │   ├── scraper.py          # Web scraping
│   │   ├── prompt_builder.py   # Prompt generation logic
│   │   └── github_sync.py      # GitHub integration
│   ├── ui/
│   │   ├── app_window.py       # Main application window
│   │   ├── styles.py           # UI styling
│   │   ├── tabs/               # UI tab components
│   │   └── widgets.py          # Reusable widgets
│   └── main.py                 # Application entry point
├── templates/                  # Prompt templates
├── prompts/                    # Generated prompts (git-tracked)
├── assets/                     # Images and icons
├── .env.example                # Environment variable template
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## Data Sources

### The Odds API
**Best for**: Real-time odds, multiple sportsbooks, reliable data

**Sports supported**:
- American Football (NFL, NCAAF)
- Basketball (NBA, NCAAB)
- Baseball (MLB)
- Hockey (NHL)
- Soccer (EPL, La Liga, Champions League, etc.)
- MMA/UFC
- Boxing
- Golf
- Tennis

**Free tier**: 500 requests/month

### ESPN API
**Best for**: Team statistics, scores, schedules

**Features**:
- Current scores and standings
- Team and player stats
- Game schedules
- No API key required (public endpoints)

### Web Scraping
**Best for**: Custom sportsbooks, unique data sources

**Capabilities**:
- Configure custom CSS selectors
- Schedule scraping tasks
- Rate limiting built-in
- Selenium support for dynamic content

**Supported sportsbooks** (with configuration):
- DraftKings
- FanDuel
- Bet365
- Bovada
- And any other HTML-based sportsbook

---

## Prompt Templates

PromptBuilder uses customizable templates to generate prompts. Templates support:

- Dynamic data insertion
- Sport-specific formatting
- Conditional sections (stats, weather, injuries)
- Custom analysis requirements
- AI model-specific optimization

### Default Template Sections:
1. **Context**: Background and objective
2. **Game Data**: Teams, matchups, schedules
3. **Odds Information**: All betting odds by type and sportsbook
4. **Analysis Request**: Specific analysis tasks
5. **Constraints**: Odds limits, risk parameters
6. **Additional Context**: Custom user input

### Custom Templates
Create your own templates in the `templates/` directory:
```
{timestamp} - Current date/time
{sports} - Selected sports
{max_odds} - Maximum combined odds
{game_data} - Formatted game information
{odds_data} - Formatted odds data
{bet_types} - Enabled bet types
{risk_level} - Risk tolerance setting
{custom_context} - User-provided context
```

---

## GitHub Integration

### Automatic Versioning
Every generated prompt can be automatically:
- Saved to `prompts/` directory
- Committed to Git with timestamp
- Pushed to GitHub repository
- Tracked for future reference

### Commit Format
```
Generated prompt for NFL, NBA - 2025-11-01 14:30:22

📊 Generated with PromptBuilder
Co-Authored-By: PromptBuilder <noreply@promptbuilder.com>
```

### Configuration Sync
Keep your settings synchronized across multiple devices by pushing `config.json` to GitHub.

---

## Advanced Features

### Parlay Odds Calculator
Automatically calculates combined parlay odds from individual selections:
```python
from app.core.prompt_builder import get_prompt_builder

builder = get_prompt_builder()
combined = builder.calculate_parlay_odds(["+150", "-200", "+300"])
print(combined)  # Output: "+600"
```

### Custom Analysis Types
Enable specific analysis types:
- **Value Betting**: Identify +EV opportunities
- **Risk Assessment**: Detailed risk analysis
- **Statistical Predictions**: Data-driven predictions
- **Trend Analysis**: Recent patterns and streaks
- **Injury Impact**: How injuries affect outcomes

### Multi-Source Data Aggregation
Combine data from multiple sources for comprehensive analysis:
```python
# Fetch from The Odds API
odds_data = odds_client.get_odds(sport, regions="us")

# Enrich with ESPN stats
espn_data = espn_client.get_scores(sport)

# Add web-scraped data
scraped = scraper.scrape()

# Generate unified prompt
prompt = builder.build_prompt(config, games)
```

---

## Troubleshooting

### Common Issues

**API Key Not Working**
- Verify key is correctly added to `.env`
- Check API quota hasn't been exceeded
- Ensure no extra spaces in the key

**Web Scraping Fails**
- Check if website structure changed
- Verify CSS selectors are correct
- Increase scraping delay
- Enable Selenium for dynamic content

**GitHub Push Fails**
- Verify Personal Access Token has correct permissions
- Check repository exists on GitHub
- Ensure remote URL is correct

**Application Won't Start**
- Verify Python version (3.10+)
- Check all dependencies are installed
- Review `app.log` for error details

### Logging
Application logs are saved to `app.log` in the project directory. Set log level in `.env`:
```
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

---

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
# Format code
black app/

# Lint
flake8 app/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## API Usage & Rate Limits

### The Odds API
- **Free Tier**: 500 requests/month
- **Rate Limit**: Built-in 1-second delay between requests
- **Quota Tracking**: Displayed in UI

### Best Practices
- Cache API responses (15-minute default)
- Use web scraping for frequently updated data
- Combine API calls when possible
- Monitor request count in application

---

## Roadmap

### Planned Features
- [ ] Historical data analysis
- [ ] Machine learning predictions
- [ ] Live odds monitoring
- [ ] Telegram/Discord bot integration
- [ ] Mobile app version
- [ ] Cloud deployment option
- [ ] Team collaboration features
- [ ] Advanced analytics dashboard

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

**Important**: This tool is for informational and educational purposes only. Sports betting involves risk, and you should never bet more than you can afford to lose. PromptBuilder provides data aggregation and analysis tools but does not guarantee winning bets. Always gamble responsibly.

The creators of PromptBuilder are not responsible for any financial losses incurred from using this software. Users must comply with all local laws and regulations regarding sports betting.

---

## Support

### Getting Help
- Check the [Issues](https://github.com/tregula501/PromptBuilder/issues) page
- Read the [Documentation](https://github.com/tregula501/PromptBuilder/wiki)
- Join our [Discussions](https://github.com/tregula501/PromptBuilder/discussions)

### Found a Bug?
Please report it by [creating an issue](https://github.com/tregula501/PromptBuilder/issues/new) with:
- Detailed description
- Steps to reproduce
- Expected vs actual behavior
- Log files if applicable

---

## Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [The Odds API](https://the-odds-api.com/) - Sports betting odds data
- [ESPN](https://www.espn.com/) - Sports statistics
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [GitPython](https://gitpython.readthedocs.io/) - Git integration

---

## Author

**tregula501** - [GitHub Profile](https://github.com/tregula501)

---

Built with ❤️ for sports betting enthusiasts who want to make data-driven decisions.
