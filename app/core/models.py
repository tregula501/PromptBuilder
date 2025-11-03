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
    WNBA = "WNBA"
    MLB = "MLB"
    NHL = "NHL"
    NCAAF = "NCAAF"
    NCAAB = "NCAAB"
    SOCCER = "Soccer"
    PREMIER_LEAGUE = "Premier League"
    LA_LIGA = "La Liga"
    CHAMPIONS_LEAGUE = "Champions League"
    MLS = "MLS"
    TENNIS = "Tennis"
    MMA = "MMA"
    UFC = "UFC"
    BOXING = "Boxing"
    GOLF = "Golf"


class BetType(str, Enum):
    """Types of bets and markets."""

    # ===== BASIC MARKETS =====
    MONEYLINE = "moneyline"  # h2h in API
    SPREAD = "spread"  # spreads in API
    TOTALS = "totals"  # totals in API
    OVER_UNDER = "over_under"  # Alias for totals
    PARLAY = "parlay"  # Client-side combination
    TEASER = "teaser"  # Client-side combination
    LIVE = "live"  # In-play odds

    # ===== ALTERNATE LINES =====
    ALTERNATE_SPREADS = "alternate_spreads"
    ALTERNATE_TOTALS = "alternate_totals"
    ALTERNATE_TEAM_TOTALS = "alternate_team_totals"

    # ===== SOCCER-SPECIFIC MARKETS =====
    H2H_3_WAY = "h2h_3_way"  # Win/Draw/Win
    BTTS = "btts"  # Both Teams to Score
    DRAW_NO_BET = "draw_no_bet"

    # ===== PERIOD MARKETS - QUARTERS =====
    H2H_Q1 = "h2h_q1"
    H2H_Q2 = "h2h_q2"
    H2H_Q3 = "h2h_q3"
    H2H_Q4 = "h2h_q4"
    SPREADS_Q1 = "spreads_q1"
    SPREADS_Q2 = "spreads_q2"
    SPREADS_Q3 = "spreads_q3"
    SPREADS_Q4 = "spreads_q4"
    TOTALS_Q1 = "totals_q1"
    TOTALS_Q2 = "totals_q2"
    TOTALS_Q3 = "totals_q3"
    TOTALS_Q4 = "totals_q4"

    # ===== PERIOD MARKETS - HALVES =====
    H2H_H1 = "h2h_h1"
    H2H_H2 = "h2h_h2"
    SPREADS_H1 = "spreads_h1"
    SPREADS_H2 = "spreads_h2"
    TOTALS_H1 = "totals_h1"
    TOTALS_H2 = "totals_h2"

    # ===== PERIOD MARKETS - HOCKEY PERIODS =====
    H2H_P1 = "h2h_p1"
    H2H_P2 = "h2h_p2"
    H2H_P3 = "h2h_p3"

    # ===== PERIOD MARKETS - BASEBALL INNINGS =====
    H2H_1ST_1_INNINGS = "h2h_1st_1_innings"
    H2H_1ST_3_INNINGS = "h2h_1st_3_innings"
    H2H_1ST_5_INNINGS = "h2h_1st_5_innings"
    H2H_1ST_7_INNINGS = "h2h_1st_7_innings"

    # ===== PLAYER PROPS - NFL/NCAAF =====
    PLAYER_PASS_YDS = "player_pass_yds"
    PLAYER_PASS_TDS = "player_pass_tds"
    PLAYER_RUSH_YDS = "player_rush_yds"
    PLAYER_RUSH_TDS = "player_rush_tds"
    PLAYER_RECEPTIONS = "player_receptions"
    PLAYER_RECEPTION_YDS = "player_reception_yds"
    PLAYER_ANYTIME_TD = "player_anytime_td"

    # ===== PLAYER PROPS - NBA/WNBA/NCAAB =====
    PLAYER_POINTS = "player_points"
    PLAYER_REBOUNDS = "player_rebounds"
    PLAYER_ASSISTS = "player_assists"
    PLAYER_THREES = "player_threes"
    PLAYER_BLOCKS = "player_blocks"
    PLAYER_STEALS = "player_steals"
    PLAYER_DOUBLE_DOUBLE = "player_double_double"
    PLAYER_TRIPLE_DOUBLE = "player_triple_double"

    # ===== PLAYER PROPS - MLB =====
    BATTER_HOME_RUNS = "batter_home_runs"
    BATTER_HITS = "batter_hits"
    BATTER_TOTAL_BASES = "batter_total_bases"
    BATTER_RBIS = "batter_rbis"
    PITCHER_STRIKEOUTS = "pitcher_strikeouts"
    PITCHER_HITS_ALLOWED = "pitcher_hits_allowed"
    PITCHER_EARNED_RUNS = "pitcher_earned_runs"

    # ===== PLAYER PROPS - NHL =====
    PLAYER_GOALS = "player_goals"
    PLAYER_GOAL_SCORER_ANYTIME = "player_anytime_goal_scorer"
    PLAYER_SHOTS_ON_GOAL = "player_shots_on_goal"


# ===== MARKET ORGANIZATION HELPERS =====

class MarketCategory(str, Enum):
    """Categories for organizing betting markets in UI."""
    BASIC = "Basic Markets"
    ALTERNATE_LINES = "Alternate Lines"
    PERIOD = "Period Betting"
    SOCCER = "Soccer Markets"
    PLAYER_PROPS_NFL = "Player Props - Football"
    PLAYER_PROPS_NBA = "Player Props - Basketball"
    PLAYER_PROPS_MLB = "Player Props - Baseball"
    PLAYER_PROPS_NHL = "Player Props - Hockey"


# Market groupings for UI display
MARKET_GROUPS = {
    MarketCategory.BASIC: [
        BetType.MONEYLINE,
        BetType.SPREAD,
        BetType.TOTALS,
        BetType.PARLAY,
    ],
    MarketCategory.ALTERNATE_LINES: [
        BetType.ALTERNATE_SPREADS,
        BetType.ALTERNATE_TOTALS,
        BetType.ALTERNATE_TEAM_TOTALS,
    ],
    MarketCategory.PERIOD: [
        BetType.H2H_Q1, BetType.H2H_Q2, BetType.H2H_Q3, BetType.H2H_Q4,
        BetType.SPREADS_Q1, BetType.SPREADS_Q2, BetType.SPREADS_Q3, BetType.SPREADS_Q4,
        BetType.TOTALS_Q1, BetType.TOTALS_Q2, BetType.TOTALS_Q3, BetType.TOTALS_Q4,
        BetType.H2H_H1, BetType.H2H_H2,
        BetType.SPREADS_H1, BetType.SPREADS_H2,
        BetType.TOTALS_H1, BetType.TOTALS_H2,
        BetType.H2H_P1, BetType.H2H_P2, BetType.H2H_P3,
        BetType.H2H_1ST_1_INNINGS, BetType.H2H_1ST_3_INNINGS,
        BetType.H2H_1ST_5_INNINGS, BetType.H2H_1ST_7_INNINGS,
    ],
    MarketCategory.SOCCER: [
        BetType.H2H_3_WAY,
        BetType.BTTS,
        BetType.DRAW_NO_BET,
    ],
    MarketCategory.PLAYER_PROPS_NFL: [
        BetType.PLAYER_PASS_YDS, BetType.PLAYER_PASS_TDS,
        BetType.PLAYER_RUSH_YDS, BetType.PLAYER_RUSH_TDS,
        BetType.PLAYER_RECEPTIONS, BetType.PLAYER_RECEPTION_YDS,
        BetType.PLAYER_ANYTIME_TD,
    ],
    MarketCategory.PLAYER_PROPS_NBA: [
        BetType.PLAYER_POINTS, BetType.PLAYER_REBOUNDS, BetType.PLAYER_ASSISTS,
        BetType.PLAYER_THREES, BetType.PLAYER_BLOCKS, BetType.PLAYER_STEALS,
        BetType.PLAYER_DOUBLE_DOUBLE, BetType.PLAYER_TRIPLE_DOUBLE,
    ],
    MarketCategory.PLAYER_PROPS_MLB: [
        BetType.BATTER_HOME_RUNS, BetType.BATTER_HITS,
        BetType.BATTER_TOTAL_BASES, BetType.BATTER_RBIS,
        BetType.PITCHER_STRIKEOUTS, BetType.PITCHER_HITS_ALLOWED,
        BetType.PITCHER_EARNED_RUNS,
    ],
    MarketCategory.PLAYER_PROPS_NHL: [
        BetType.PLAYER_GOALS, BetType.PLAYER_GOAL_SCORER_ANYTIME,
        BetType.PLAYER_SHOTS_ON_GOAL,
    ],
}


# Mapping from BetType to API market parameter
BET_TYPE_TO_API_MARKET = {
    # Basic markets
    BetType.MONEYLINE: "h2h",
    BetType.SPREAD: "spreads",
    BetType.TOTALS: "totals",

    # Alternate lines
    BetType.ALTERNATE_SPREADS: "alternate_spreads",
    BetType.ALTERNATE_TOTALS: "alternate_totals",
    BetType.ALTERNATE_TEAM_TOTALS: "alternate_team_totals",

    # Soccer markets
    BetType.H2H_3_WAY: "h2h_3_way",
    BetType.BTTS: "btts",
    BetType.DRAW_NO_BET: "draw_no_bet",

    # Period markets - Quarters
    BetType.H2H_Q1: "h2h_q1",
    BetType.H2H_Q2: "h2h_q2",
    BetType.H2H_Q3: "h2h_q3",
    BetType.H2H_Q4: "h2h_q4",
    BetType.SPREADS_Q1: "spreads_q1",
    BetType.SPREADS_Q2: "spreads_q2",
    BetType.SPREADS_Q3: "spreads_q3",
    BetType.SPREADS_Q4: "spreads_q4",
    BetType.TOTALS_Q1: "totals_q1",
    BetType.TOTALS_Q2: "totals_q2",
    BetType.TOTALS_Q3: "totals_q3",
    BetType.TOTALS_Q4: "totals_q4",

    # Period markets - Halves
    BetType.H2H_H1: "h2h_h1",
    BetType.H2H_H2: "h2h_h2",
    BetType.SPREADS_H1: "spreads_h1",
    BetType.SPREADS_H2: "spreads_h2",
    BetType.TOTALS_H1: "totals_h1",
    BetType.TOTALS_H2: "totals_h2",

    # Period markets - Hockey
    BetType.H2H_P1: "h2h_p1",
    BetType.H2H_P2: "h2h_p2",
    BetType.H2H_P3: "h2h_p3",

    # Period markets - Baseball
    BetType.H2H_1ST_1_INNINGS: "h2h_1st_1_innings",
    BetType.H2H_1ST_3_INNINGS: "h2h_1st_3_innings",
    BetType.H2H_1ST_5_INNINGS: "h2h_1st_5_innings",
    BetType.H2H_1ST_7_INNINGS: "h2h_1st_7_innings",

    # Player props - NFL
    BetType.PLAYER_PASS_YDS: "player_pass_yds",
    BetType.PLAYER_PASS_TDS: "player_pass_tds",
    BetType.PLAYER_RUSH_YDS: "player_rush_yds",
    BetType.PLAYER_RUSH_TDS: "player_rush_tds",
    BetType.PLAYER_RECEPTIONS: "player_receptions",
    BetType.PLAYER_RECEPTION_YDS: "player_reception_yds",
    BetType.PLAYER_ANYTIME_TD: "player_anytime_td",

    # Player props - NBA/WNBA
    BetType.PLAYER_POINTS: "player_points",
    BetType.PLAYER_REBOUNDS: "player_rebounds",
    BetType.PLAYER_ASSISTS: "player_assists",
    BetType.PLAYER_THREES: "player_threes",
    BetType.PLAYER_BLOCKS: "player_blocks",
    BetType.PLAYER_STEALS: "player_steals",
    BetType.PLAYER_DOUBLE_DOUBLE: "player_double_double",
    BetType.PLAYER_TRIPLE_DOUBLE: "player_triple_double",

    # Player props - MLB
    BetType.BATTER_HOME_RUNS: "batter_home_runs",
    BetType.BATTER_HITS: "batter_hits",
    BetType.BATTER_TOTAL_BASES: "batter_total_bases",
    BetType.BATTER_RBIS: "batter_rbis",
    BetType.PITCHER_STRIKEOUTS: "pitcher_strikeouts",
    BetType.PITCHER_HITS_ALLOWED: "pitcher_hits_allowed",
    BetType.PITCHER_EARNED_RUNS: "pitcher_earned_runs",

    # Player props - NHL
    BetType.PLAYER_GOALS: "player_goals",
    BetType.PLAYER_GOAL_SCORER_ANYTIME: "player_anytime_goal_scorer",
    BetType.PLAYER_SHOTS_ON_GOAL: "player_shots_on_goal",
}


# Friendly display names for bet types
BET_TYPE_DISPLAY_NAMES = {
    # Basic
    BetType.MONEYLINE: "Moneyline",
    BetType.SPREAD: "Point Spread",
    BetType.TOTALS: "Over/Under (Totals)",
    BetType.PARLAY: "Parlay/Accumulator",

    # Alternate lines
    BetType.ALTERNATE_SPREADS: "Alternate Spreads",
    BetType.ALTERNATE_TOTALS: "Alternate Totals",
    BetType.ALTERNATE_TEAM_TOTALS: "Alternate Team Totals",

    # Soccer
    BetType.H2H_3_WAY: "3-Way (Win/Draw/Win)",
    BetType.BTTS: "Both Teams to Score",
    BetType.DRAW_NO_BET: "Draw No Bet",

    # Period markets
    BetType.H2H_Q1: "1st Quarter Winner",
    BetType.H2H_Q2: "2nd Quarter Winner",
    BetType.H2H_Q3: "3rd Quarter Winner",
    BetType.H2H_Q4: "4th Quarter Winner",
    BetType.H2H_H1: "1st Half Winner",
    BetType.H2H_H2: "2nd Half Winner",
    BetType.H2H_P1: "1st Period Winner",
    BetType.H2H_P2: "2nd Period Winner",
    BetType.H2H_P3: "3rd Period Winner",
    BetType.H2H_1ST_1_INNINGS: "First Inning Winner",
    BetType.H2H_1ST_3_INNINGS: "First 3 Innings Winner",
    BetType.H2H_1ST_5_INNINGS: "First 5 Innings Winner",
    BetType.H2H_1ST_7_INNINGS: "First 7 Innings Winner",

    # Player props - NFL
    BetType.PLAYER_PASS_YDS: "Passing Yards",
    BetType.PLAYER_PASS_TDS: "Passing Touchdowns",
    BetType.PLAYER_RUSH_YDS: "Rushing Yards",
    BetType.PLAYER_RUSH_TDS: "Rushing Touchdowns",
    BetType.PLAYER_RECEPTIONS: "Receptions",
    BetType.PLAYER_RECEPTION_YDS: "Receiving Yards",
    BetType.PLAYER_ANYTIME_TD: "Anytime Touchdown Scorer",

    # Player props - NBA
    BetType.PLAYER_POINTS: "Points",
    BetType.PLAYER_REBOUNDS: "Rebounds",
    BetType.PLAYER_ASSISTS: "Assists",
    BetType.PLAYER_THREES: "3-Pointers Made",
    BetType.PLAYER_BLOCKS: "Blocks",
    BetType.PLAYER_STEALS: "Steals",
    BetType.PLAYER_DOUBLE_DOUBLE: "Double-Double",
    BetType.PLAYER_TRIPLE_DOUBLE: "Triple-Double",

    # Player props - MLB
    BetType.BATTER_HOME_RUNS: "Home Runs",
    BetType.BATTER_HITS: "Hits",
    BetType.BATTER_TOTAL_BASES: "Total Bases",
    BetType.BATTER_RBIS: "RBIs",
    BetType.PITCHER_STRIKEOUTS: "Strikeouts",
    BetType.PITCHER_HITS_ALLOWED: "Hits Allowed",
    BetType.PITCHER_EARNED_RUNS: "Earned Runs",

    # Player props - NHL
    BetType.PLAYER_GOALS: "Goals",
    BetType.PLAYER_GOAL_SCORER_ANYTIME: "Anytime Goal Scorer",
    BetType.PLAYER_SHOTS_ON_GOAL: "Shots on Goal",
}


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
    min_parlay_legs: int = Field(default=2, ge=2, le=15)
    max_parlay_legs: int = Field(default=10, ge=2, le=15)
    bet_types: List[BetType]
    analysis_types: List[AnalysisType]
    risk_tolerance: RiskLevel = RiskLevel.MEDIUM
    ai_model: AIModel = AIModel.GENERIC
    include_stats: bool = True
    include_injuries: bool = True
    include_weather: bool = True
    include_trends: bool = True
    custom_context: Optional[str] = None
    selected_sportsbooks: List[str] = []

    @validator('sports')
    def validate_sports_not_empty(cls, v):
        """Ensure at least one sport is selected."""
        if not v:
            raise ValueError("At least one sport must be selected")
        return v

    @validator('bet_types')
    def validate_bet_types_not_empty(cls, v):
        """Ensure at least one bet type is selected."""
        if not v:
            raise ValueError("At least one bet type must be selected")
        return v

    @validator('max_parlay_legs')
    def validate_parlay_legs_range(cls, v, values):
        """Ensure max_parlay_legs is greater than or equal to min_parlay_legs."""
        if 'min_parlay_legs' in values and v < values['min_parlay_legs']:
            raise ValueError(f"max_parlay_legs ({v}) must be >= min_parlay_legs ({values['min_parlay_legs']})")
        return v

    @validator('custom_context')
    def validate_custom_context_length(cls, v):
        """Ensure custom context doesn't exceed reasonable length."""
        MAX_LENGTH = 5000
        if v and len(v) > MAX_LENGTH:
            raise ValueError(f"Custom context exceeds maximum length of {MAX_LENGTH} characters")
        return v

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
