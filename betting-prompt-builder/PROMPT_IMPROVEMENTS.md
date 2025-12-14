# Prompt Generation Improvements for Sports Betting Analysis

## Overview

This document outlines improvements to make the generated prompts more effective for LLM-based sports betting analysis. The focus is on providing better context, mathematical frameworks, and analytical guidance.

---

## Key Improvements

### 1. **Value Betting & Expected Value Analysis**

**Current Issue:** Prompts don't guide LLMs to calculate implied probability or expected value.

**Enhancement:** Add mathematical frameworks for value betting:

```
BETTING MATH FRAMEWORK:
For each bet recommendation, calculate and include:

1. Implied Probability:
   - Negative odds (-X): Implied % = X / (X + 100) × 100
   - Positive odds (+X): Implied % = 100 / (X + 100) × 100
   - Example: -110 = 110/(110+100) = 52.38% implied probability

2. True Probability Assessment:
   - Based on your analysis, what is the ACTUAL win probability?
   - Compare true probability vs implied probability to find value

3. Expected Value (EV):
   - EV = (True Probability × Win Amount) - (Lose Probability × Bet Amount)
   - Positive EV = Value bet (recommend)
   - Negative EV = Bad bet (avoid)
   - Example: If true probability is 55% and odds are -110:
     * Win: $90.91 profit on $100 bet
     * Lose: -$100
     * EV = (0.55 × $90.91) - (0.45 × $100) = $50.00 - $45.00 = +$5.00 (positive value)

4. Break-Even Percentage:
   - For -110 odds, need to win 52.38% to break even
   - For +150 odds, need to win 40% to break even
   - Only recommend if your true probability exceeds break-even %
```

### 2. **Enhanced Line Shopping & Odds Comparison**

**Current Issue:** Odds are listed but not compared for value.

**Enhancement:** Add structured comparison format:

```
ODDS COMPARISON ANALYSIS:
For each bet type, identify the best value across sportsbooks:

Example Format:
Moneyline - Team A:
  DraftKings: -120 (Implied: 54.55%) ⭐ BEST VALUE
  FanDuel: -125 (Implied: 55.56%)
  BetMGM: -130 (Implied: 56.52%)

Spread - Team A -3.5:
  FanDuel: -105 (Implied: 51.22%) ⭐ BEST VALUE
  DraftKings: -110 (Implied: 52.38%)
  BetMGM: -110 (Implied: 52.38%)

VALUE INDICATORS:
- Highlight when one book offers 5+ point advantage
- Identify arbitrage opportunities (if any)
- Note line discrepancies that may indicate sharp action
```

### 3. **Contextual Team Information**

**Current Issue:** Only basic game info is provided.

**Enhancement:** Add structured context requests:

```
TEAM CONTEXT REQUIRED:
For each team, research and include:

1. Recent Form (Last 5-10 games):
   - Win/Loss record
   - Against the spread (ATS) record
   - Over/Under record
   - Key trends (e.g., "Lakers 7-3 ATS in last 10")

2. Head-to-Head History:
   - Last 5 meetings
   - Trends (e.g., "Over has hit in 4 of last 5 meetings")
   - Home/away splits in matchup

3. Situational Factors:
   - Rest days (back-to-back, extra rest)
   - Travel schedule
   - Motivation factors (playoff race, rivalry, etc.)
   - Recent roster changes or trades

4. Key Matchups:
   - Individual player matchups that could swing the game
   - Coaching strategies
   - Style of play compatibility
```

### 4. **Market Movement Analysis**

**Current Issue:** No guidance on line movement interpretation.

**Enhancement:** Add line movement framework:

```
LINE MOVEMENT ANALYSIS:
When researching current lines, note any significant movement:

1. Opening Line vs Current Line:
   - If line moved 2+ points, identify likely cause:
     * Sharp money (professional bettors)
     * Public money (recreational bettors)
     * Injury/news impact
     * Market correction

2. Movement Interpretation:
   - Line moving toward favorite = Sharp money on favorite OR public betting favorite
   - Line moving toward underdog = Sharp money on dog OR injury to favorite
   - Total moving up = Offensive news OR sharp over bet
   - Total moving down = Defensive news OR sharp under bet

3. Reverse Line Movement:
   - If public bets one side but line moves opposite = Sharp action
   - This is often a strong indicator of value

4. Steam Moves:
   - Rapid line movement = Sharp action
   - Note which book moved first (often indicates sharp book)
```

### 5. **Parlay Correlation Analysis**

**Current Issue:** No guidance on correlated vs uncorrelated bets.

**Enhancement:** Add correlation framework:

```
PARLAY CONSTRUCTION GUIDELINES:

1. Correlation Analysis:
   - AVOID highly correlated bets in same parlay:
     * Team A ML + Team A spread (highly correlated)
     * Team A ML + Over (moderately correlated - if team wins, more likely to go over)
     * Player prop + Team total (correlated)
   
   - PREFER uncorrelated bets:
     * Different games
     * Different bet types from different games
     * Independent outcomes

2. Same Game Parlay (SGP) Considerations:
   - SGPs often have worse odds due to correlation
   - Only recommend if value is exceptional
   - Example of good SGP: Team A -3.5 + Under 230.5 (if expecting low-scoring win)

3. Cross-Game Parlays:
   - Better value typically
   - Less correlation risk
   - Can mix different sports for diversification

4. Leg Selection Strategy:
   - Mix favorites and underdogs (don't stack all favorites)
   - Target 55-60% true probability per leg
   - For 3-leg parlay: Need ~18% combined probability to be profitable at typical odds
```

### 6. **Bankroll Management Guidance**

**Current Issue:** No unit sizing recommendations.

**Enhancement:** Add bankroll management framework:

```
BANKROLL MANAGEMENT:

1. Unit Sizing:
   - 1 unit = 1% of total bankroll (standard)
   - High confidence (★★★★★): 2-3 units
   - Medium confidence (★★★☆☆): 1 unit
   - Low confidence (★★☆☆☆): 0.5 units
   - Speculative (★☆☆☆☆): 0.25 units or skip

2. Kelly Criterion (Optional Advanced):
   - Optimal bet size = (True Probability × Odds - 1) / (Odds - 1)
   - Example: 55% true prob at -110 odds
     * Optimal = (0.55 × 1.909 - 1) / (1.909 - 1) = 0.05 / 0.909 = 5.5% of bankroll
   - Note: Full Kelly is aggressive, consider 25-50% of Kelly for safety

3. Parlay Sizing:
   - Parlays should be smaller units than straight bets
   - 3-leg parlay: 0.5-1 unit max
   - 4+ leg parlay: 0.25-0.5 unit max
   - Higher variance = smaller bet size

4. Risk Management:
   - Never bet more than 5% of bankroll on single bet
   - Limit total daily exposure to 10-15% of bankroll
   - Track all bets and adjust sizing based on results
```

### 7. **Situational Betting Context**

**Current Issue:** Generic factors, not situation-specific.

**Enhancement:** Add situational analysis:

```
SITUATIONAL ANALYSIS FRAMEWORK:

1. Spot Situations (Look for these patterns):
   - Letdown spots (team coming off big win)
   - Bounce-back spots (team coming off bad loss)
   - Lookahead spots (team has important game next)
   - Revenge spots (team lost previous meeting)
   - Trap games (public favorite in bad spot)

2. Schedule Context:
   - Back-to-back games (fatigue factor)
   - Extended rest (rust factor)
   - Travel distance and time zones
   - Home/away splits (especially for specific teams)

3. Motivation Factors:
   - Playoff implications
   - Rivalry games
   - Coaching changes
   - Player milestones
   - Public perception vs reality

4. Market Context:
   - Public betting percentages (if available)
   - Sharp vs public money splits
   - Line value vs market consensus
```

### 8. **Player Prop Analysis Framework**

**Current Issue:** Player props listed but no analysis guidance.

**Enhancement:** Add prop-specific analysis:

```
PLAYER PROP ANALYSIS:

1. Usage & Opportunity:
   - Minutes/usage trends (last 5 games)
   - Matchup advantages (weak defender, pace of play)
   - Injury to teammate (increased opportunity)
   - Role changes (starter vs bench)

2. Recent Form:
   - Last 5 game averages
   - Home vs away splits
   - Performance vs similar opponents
   - Trends (improving/declining)

3. Matchup-Specific Factors:
   - Defensive ranking vs position
   - Pace of play (faster = more opportunities)
   - Game script (blowout = bench time)
   - Head-to-head history vs opponent

4. Value Assessment:
   - Compare prop line to recent averages
   - Identify props where line seems off
   - Consider alternate lines for better value
   - Factor in game total (high total = more scoring)
```

### 9. **Market Efficiency Indicators**

**Current Issue:** No guidance on finding market inefficiencies.

**Enhancement:** Add efficiency analysis:

```
MARKET EFFICIENCY ANALYSIS:

1. Line Quality Indicators:
   - Sharp book consensus (if multiple sharp books agree, line is likely sharp)
   - Public betting percentages (fade public when extreme)
   - Line movement patterns (sharp vs public)
   - Historical closing line value (CLV)

2. Inefficiency Opportunities:
   - Small market sports (less efficient)
   - Player props (often softer lines)
   - Live betting (reactive lines can be inefficient)
   - Alternate lines (sometimes better value)

3. Market Timing:
   - Early lines (often softer, more value)
   - Closing lines (sharpest, less value but more accurate)
   - Line shopping (always compare before betting)

4. Sharp Indicators:
   - Reverse line movement
   - Steam moves
   - Line value at sharp books
   - Historical sharp bet patterns
```

### 10. **Enhanced Output Format**

**Current Issue:** Recommendations format could be more structured.

**Enhancement:** Standardized recommendation format:

```
RECOMMENDATION FORMAT:

For each bet, provide in this exact structure:

[BET TYPE] - [TEAM/PLAYER] - [LINE] @ [SPORTSBOOK]
Odds: [ODDS] | Implied Probability: [%] | True Probability: [%] | EV: [+/-$X.XX]
Confidence: [★★★★★]
Units: [X]

ANALYSIS:
- [Key supporting factors with dates/sources]
- [Matchup advantages]
- [Recent trends]
- [Situational factors]

RISKS:
- [Potential concerns]
- [What could go wrong]

VALUE RATIONALE:
- Why this bet has positive expected value
- Comparison to other sportsbooks
- Market context

ALTERNATIVES:
- Similar bets with comparable value
- Safer/lower variance options
- Higher risk/higher reward options
```

---

## Implementation Priority

### Phase 1 (High Impact, Easy)
1. Add implied probability calculations to odds display
2. Enhance odds comparison format
3. Add EV calculation framework
4. Improve recommendation format structure

### Phase 2 (High Impact, Medium Effort)
1. Add line movement analysis framework
2. Add correlation analysis for parlays
3. Add bankroll management guidance
4. Enhance player prop analysis

### Phase 3 (Medium Impact, Higher Effort)
1. Add contextual team information requests
2. Add situational betting framework
3. Add market efficiency indicators
4. Create betting math helper functions

---

## Example Enhanced Prompt Section

Here's how a section would look with improvements:

```
=== NBA ===

Lakers @ Warriors
Date/Time: Jan 27, 2025, 10:00 PM EST

Available Odds:

  DraftKings:
    Moneyline: Lakers +150 (Implied: 40.00%) | Warriors -175 (Implied: 63.64%)
    Spread: Lakers +4.5 -110 (Implied: 52.38%) | Warriors -4.5 -110 (Implied: 52.38%)
    Total: Over 235.5 -110 (Implied: 52.38%) | Under 235.5 -110 (Implied: 52.38%)
    Last Updated: 2025-01-27 14:30 EST

  FanDuel:
    Moneyline: Lakers +145 (Implied: 40.82%) ⭐ BEST VALUE | Warriors -172 (Implied: 63.24%)
    Spread: Lakers +4.5 -108 (Implied: 51.92%) ⭐ BEST VALUE | Warriors -4.5 -112 (Implied: 52.83%)
    Total: Over 235.5 -108 (Implied: 51.92%) ⭐ BEST VALUE | Under 235.5 -112 (Implied: 52.83%)
    Last Updated: 2025-01-27 14:25 EST

  BetMGM:
    Moneyline: Lakers +140 (Implied: 41.67%) | Warriors -165 (Implied: 62.26%)
    Spread: Lakers +4.5 -110 (Implied: 52.38%) | Warriors -4.5 -110 (Implied: 52.38%)
    Total: Over 235.5 -110 (Implied: 52.38%) | Under 235.5 -110 (Implied: 52.38%)
    Last Updated: 2025-01-27 14:20 EST

LINE MOVEMENT:
- Opening line: Warriors -3.5, moved to -4.5 (sharp money on Warriors OR public betting Warriors)
- Total opened at 233.5, moved to 235.5 (sharp over bet OR offensive news)
- Movement suggests sharp action on Warriors and Over

TEAM CONTEXT REQUIRED:
Lakers:
- Recent Form: 3-7 in last 10, 4-6 ATS, 5-5 O/U
- Key Trend: Lakers 1-4 ATS as road underdog this season
- Rest: 1 day rest (played yesterday)
- Injury: LeBron James Questionable (check latest status)

Warriors:
- Recent Form: 7-3 in last 10, 6-4 ATS, 6-4 O/U
- Key Trend: Warriors 8-2 ATS at home this season
- Rest: 2 days rest
- Injury: Draymond Green Probable

Head-to-Head: Warriors won last 2 meetings, Over hit in 3 of last 4

BETTING MATH FRAMEWORK:
For each recommendation, calculate:
1. Implied Probability from odds
2. Your assessed True Probability
3. Expected Value: EV = (True Prob × Win Amount) - (Lose Prob × Bet Amount)
4. Only recommend if EV is positive

Example Calculation:
- Lakers +4.5 at -108 (FanDuel)
- Implied: 51.92% (need to win 51.92% to break even)
- If you assess true probability at 55%:
  * Win: $92.59 profit on $100 bet
  * Lose: -$100
  * EV = (0.55 × $92.59) - (0.45 × $100) = $50.92 - $45.00 = +$5.92 ✅ VALUE BET

Consider the following factors specific to NBA:
1. Injuries and player availability
2. Recent form and momentum (last 5 games)
3. Home/away splits and performance
4. Back-to-back games and rest days
5. Pace and style matchup
```

---

## Additional Considerations

### 1. **Real-time Data Integration** (Future Enhancement)
- Integrate injury reports
- Line movement tracking
- Public betting percentages
- Sharp money indicators

### 2. **Historical Performance Tracking**
- Track recommendation accuracy
- Identify which bet types/sports perform best
- Learn from past mistakes

### 3. **Advanced Analytics**
- Power ratings
- Elo ratings
- Advanced metrics (DVOA, Net Rating, etc.)
- Machine learning predictions

### 4. **Betting Strategy Templates**
- Conservative strategy (high probability, low variance)
- Aggressive strategy (lower probability, higher payout)
- Balanced strategy (mix of both)
- Arbitrage strategy (guaranteed profit)

---

*This document provides a comprehensive framework for improving prompt generation to better assist LLMs in making informed betting decisions.*


