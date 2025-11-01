"""
Data models for PromptBuilder.

Defines Pydantic models for type validation and data structures.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator


class SportType(str, Enum):
    """Supported sports types."""
    NFL = "NFL"
    NBA = "NBA"
    MLB = "MLB"
    NHL = "NHL"
    NCAAF = "NCAAF"
    NCAAB = "NCAAB"
    SOCCER = "Soccer"
    PREMIER_LEAGUE = "Premier League"
    LA_LIGA = "La Liga"
    CHAMPIONS_LEAGUE = "Champions League"
    TENNIS = "Tennis"
    MMA = "MMA"
    UFC = "UFC"
    BOXING = "Boxing"
    GOLF = "Golf"


class BetType(str, Enum):
    """Types of bets."""
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTALS = "totals"
    OVER_UNDER = "over_under"
    PARLAY = "parlay"
    TEASER = "teaser"
    PROP = "prop"
    FUTURES = "futures"
    LIVE = "live"


class OddsFormat(str, Enum):
    """Odds display formats."""
    AMERICAN = "american"  # +150, -200
    DECIMAL = "decimal"    # 2.50, 1.50
    FRACTIONAL = "fractional"  # 3/2, 1/2


class RiskLevel(str, Enum):
    """Risk tolerance levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class AnalysisType(str, Enum):
    """Types of betting analysis."""
    VALUE_BETTING = "value_betting"
    RISK_ASSESSMENT = "risk_assessment"
    STATISTICAL_PREDICTIONS = "statistical_predictions"
    TREND_ANALYSIS = "trend_analysis"
    INJURY_IMPACT = "injury_impact"


class AIModel(str, Enum):
    """Target AI models for prompts."""
    CLAUDE = "Claude"
    GPT4 = "GPT-4"
    CHATGPT = "ChatGPT"
    GENERIC = "Generic/Multiple"
    CUSTOM = "Custom"


class TeamStats(BaseModel):
    """Team statistics."""
    team_name: str
    wins: Optional[int] = None
    losses: Optional[int] = None
    points_per_game: Optional[float] = None
    points_allowed_per_game: Optional[float] = None
    streak: Optional[str] = None  # "W3", "L2"
    injuries: Optional[List[str]] = []
    recent_form: Optional[str] = None
    additional_stats: Optional[Dict[str, Any]] = {}


class OddsData(BaseModel):
    """Betting odds data."""
    sportsbook: str
    bet_type: BetType
    odds: str  # e.g., "+150", "-200", "2.50"
    odds_format: OddsFormat = OddsFormat.AMERICAN
    line: Optional[str] = None  # For spreads/totals (e.g., "-3.5", "o47.5")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class Game(BaseModel):
    """Individual game/match data."""
    sport: SportType
    league: Optional[str] = None
    home_team: str
    away_team: str
    game_time: Optional[datetime] = None
    venue: Optional[str] = None
    weather: Optional[str] = None
    home_stats: Optional[TeamStats] = None
    away_stats: Optional[TeamStats] = None
    odds: List[OddsData] = []
    notes: Optional[str] = None

    class Config:
        use_enum_values = True

    def get_unique_key(self) -> str:
        """Generate a unique key for this game based on teams and time."""
        time_str = self.game_time.isoformat() if self.game_time else "no_time"
        return f"{self.sport}_{self.home_team}_{self.away_team}_{time_str}"


class BetSelection(BaseModel):
    """A single bet selection."""
    game: Game
    bet_type: BetType
    selection: str  # e.g., "Lakers ML", "Over 47.5", "Chiefs -3.5"
    odds: str
    sportsbook: str
    stake: Optional[float] = None

    class Config:
        use_enum_values = True


class Parlay(BaseModel):
    """Parlay/accumulator bet."""
    selections: List[BetSelection] = Field(..., min_items=2)
    combined_odds: str
    total_stake: Optional[float] = None
    potential_payout: Optional[float] = None

    @validator('combined_odds')
    def validate_combined_odds(cls, v):
        """Ensure combined odds is a valid string."""
        if not v:
            raise ValueError("Combined odds must be specified")
        return v


class PromptConfig(BaseModel):
    """Configuration for prompt generation."""
    sports: List[SportType]
    max_combined_odds: int = Field(default=400, ge=100)
    bet_types: List[BetType]
    analysis_types: List[AnalysisType]
    risk_tolerance: RiskLevel = RiskLevel.MEDIUM
    ai_model: AIModel = AIModel.GENERIC
    include_stats: bool = True
    include_injuries: bool = True
    include_weather: bool = True
    include_trends: bool = True
    custom_context: Optional[str] = None

    class Config:
        use_enum_values = True


class PromptData(BaseModel):
    """Data structure for generated prompts."""
    config: PromptConfig
    games: List[Game] = []
    parlays: List[Parlay] = []
    generated_at: datetime = Field(default_factory=datetime.now)
    prompt_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

    class Config:
        use_enum_values = True


class DataSource(str, Enum):
    """Available data sources."""
    ODDS_API = "odds_api"
    ESPN_API = "espn_api"
    WEB_SCRAPING = "web_scraping"
    MANUAL_ENTRY = "manual_entry"


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    source: Optional[DataSource] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class ScrapingRule(BaseModel):
    """Web scraping configuration."""
    sportsbook_name: str
    url: str
    selectors: Dict[str, str]  # CSS/XPath selectors
    delay: int = 2  # Delay between requests
    headers: Optional[Dict[str, str]] = None
    enabled: bool = True


class UserPreferences(BaseModel):
    """User preferences and settings."""
    favorite_sports: List[SportType] = []
    favorite_bet_types: List[BetType] = []
    default_risk_level: RiskLevel = RiskLevel.MEDIUM
    default_max_odds: int = 400
    preferred_sportsbooks: List[str] = []
    preferred_ai_model: AIModel = AIModel.GENERIC
    theme: Literal["light", "dark"] = "dark"
    auto_save: bool = False
    auto_commit: bool = False

    class Config:
        use_enum_values = True
