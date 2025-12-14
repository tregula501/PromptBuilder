const { getFactorsForSport, getSportDisplayName } = require('./sportTemplateService');

// All available sportsbooks
const allSportsbooks = [
  { key: 'draftkings', title: 'DraftKings', availableInApi: true },
  { key: 'fanduel', title: 'FanDuel', availableInApi: true },
  { key: 'betmgm', title: 'BetMGM', availableInApi: true },
  { key: 'bet365', title: 'Bet365', availableInApi: false },
  { key: 'hardrock', title: 'HardRock', availableInApi: false }
];

// Team-based sports that require lineup verification
const teamSports = [
  'americanfootball_nfl',
  'americanfootball_ncaaf',
  'basketball_nba',
  'basketball_ncaab',
  'basketball_wncaab',
  'basketball_wnba',
  'baseball_mlb',
  'icehockey_nhl',
  'icehockey_ncaa',
  'soccer_usa_mls',
  'soccer_epl',
  'mma_mixed_martial_arts'
];

// Sports where player props should be excluded (regulations, market availability, or data limitations)
const playerPropExcludedSports = new Set([
  'americanfootball_ncaaf',
  'basketball_ncaab',
  'basketball_wncaab',
  'icehockey_ncaa'
]);

/**
 * Calculate implied probability from American odds
 */
function calculateImpliedProbability(odds) {
  if (odds > 0) {
    return (100 / (odds + 100)) * 100;
  } else {
    return (Math.abs(odds) / (Math.abs(odds) + 100)) * 100;
  }
}

/**
 * Format odds with implied probability
 */
function formatOddsWithImplied(odds) {
  const formatted = formatOdds(odds);
  const implied = calculateImpliedProbability(odds);
  return `${formatted} (Implied: ${implied.toFixed(2)}%)`;
}

/**
 * Find best value odds across sportsbooks for a specific outcome
 */
function findBestOdds(game, marketKey, outcomeName, selectedSportsbooks) {
  let bestOdds = null;
  let bestBook = null;
  
  for (const sportsbookKey of selectedSportsbooks) {
    const bookmaker = game.bookmakers?.find(b => b.key === sportsbookKey);
    if (!bookmaker) continue;
    
    const market = bookmaker.markets?.find(m => m.key === marketKey);
    if (!market) continue;
    
    const outcome = market.outcomes?.find(o => 
      o.name === outcomeName || 
      (marketKey === 'spreads' && o.name === game.awayTeam) ||
      (marketKey === 'spreads' && o.name === game.homeTeam) ||
      (marketKey === 'totals' && (o.name === 'Over' || o.name === 'Under'))
    );
    
    if (outcome) {
      const odds = outcome.price;
      if (!bestOdds || (odds > 0 && odds > bestOdds) || (odds < 0 && odds > bestOdds)) {
        bestOdds = odds;
        bestBook = allSportsbooks.find(s => s.key === sportsbookKey)?.title;
      }
    }
  }
  
  return { odds: bestOdds, book: bestBook };
}

function generatePrompt(selectedGames, selectedSportsbooks, selectedBetTypes, parlayPreferences, betStyle, excludePlayerProps = false) {
  if (!selectedGames || selectedGames.length === 0) {
    return 'No games selected. Please select at least one game.';
  }

  let effectiveBetTypes = Array.isArray(selectedBetTypes) ? [...selectedBetTypes] : [];

  const lines = [];

  // Group games by sport
  const gamesBySport = {};
  for (const game of selectedGames) {
    if (!gamesBySport[game.sportKey]) {
      gamesBySport[game.sportKey] = [];
    }
    gamesBySport[game.sportKey].push(game);
  }

  // Determine whether any selected games allow player props
  const anyPlayerPropsAllowed = selectedGames.some(g => !playerPropExcludedSports.has(g.sportKey));

  // Enforce player prop exclusion at the prompt level when:
  // - user toggled "exclude player props", OR
  // - all selected games are in sports where player props are disallowed/unavailable
  if (excludePlayerProps || !anyPlayerPropsAllowed) {
    effectiveBetTypes = effectiveBetTypes.filter(bt => bt !== 'player_props');
  }

  lines.push('Analyze the following matchups and provide your top betting recommendations with confidence ratings:');
  lines.push('');
  lines.push('IMPORTANT: Use the betting math framework below to calculate expected value for each recommendation.');
  lines.push('');

  for (const [sportKey, games] of Object.entries(gamesBySport)) {
    const sportName = getSportDisplayName(sportKey);
    const isOutright = sportKey.startsWith('golf_');

    lines.push(`=== ${sportName} ===`);
    lines.push('');

    for (const game of games) {
      if (isOutright) {
        lines.push(`Tournament: ${game.homeTeam}`);
      } else {
        lines.push(`${game.awayTeam} @ ${game.homeTeam}`);
      }
      lines.push(`Date/Time: ${formatCommenceTime(game.commenceTime)}`);
      lines.push('');

      // Add odds for each selected sportsbook with enhanced formatting
      if (isOutright) {
        lines.push('Tournament Winner Odds (Top Contenders):');
      } else {
        lines.push('Available Odds:');
      }

      // Build odds comparison table
      const oddsComparison = {};
      
      for (const sportsbookKey of selectedSportsbooks) {
        const sportsbook = allSportsbooks.find(s => s.key === sportsbookKey);
        if (!sportsbook) continue;

        const bookmakerOdds = game.bookmakers?.find(b => b.key === sportsbookKey);

        if (bookmakerOdds && bookmakerOdds.markets?.length > 0) {
          lines.push(`  ${sportsbook.title}:`);
          if (isOutright) {
            buildOutrightOddsLines(lines, bookmakerOdds);
          } else {
            buildOddsLinesEnhanced(lines, bookmakerOdds, effectiveBetTypes, game, oddsComparison);
          }
          
          // Add last update time if available
          if (bookmakerOdds.lastUpdate) {
            const updateTime = new Date(bookmakerOdds.lastUpdate).toLocaleString('en-US', {
              timeZone: 'America/New_York',
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
              hour12: true
            });
            lines.push(`    Last Updated: ${updateTime} EST`);
          }
        } else {
          const isManual = game && game.source === 'manual';
          if (sportsbook.availableInApi && !isManual) {
            lines.push(`  ${sportsbook.title}: (No odds available)`);
          } else {
            lines.push(`  ${sportsbook.title}: (Please research current odds)`);
          }
        }
        lines.push('');
      }

      // Add best value summary if multiple sportsbooks
      if (selectedSportsbooks.length > 1 && !isOutright) {
        lines.push('BEST VALUE SUMMARY:');
        for (const [marketType, outcomes] of Object.entries(oddsComparison)) {
          for (const [outcomeName, books] of Object.entries(outcomes)) {
            if (books.length > 1) {
              // Find best odds
              const best = books.reduce((best, current) => {
                return current.odds > best.odds ? current : best;
              });
              lines.push(`  ${marketType} - ${outcomeName}: ${best.book} ${formatOdds(best.odds)} ⭐ BEST VALUE`);
            }
          }
        }
        lines.push('');
      }

      // Add player props section if selected and not excluded
      if (effectiveBetTypes.includes('player_props') && !playerPropExcludedSports.has(game.sportKey)) {
        const hasPlayerProps = game.bookmakers?.some(b =>
          b.markets?.some(m => m.key.startsWith('player_'))
        );

        if (hasPlayerProps) {
          lines.push('Available Player Props:');
          for (const bookmaker of game.bookmakers || []) {
            const propMarkets = (bookmaker.markets || []).filter(m => m.key.startsWith('player_'));

            if (propMarkets.length > 0) {
              for (const market of propMarkets) {
                const propType = formatPlayerPropType(market.key);
                for (const outcome of market.outcomes || []) {
                  const player = outcome.description || outcome.name;
                  const odds = formatOddsWithImplied(outcome.price);
                  lines.push(`  ${player} - ${propType}: ${outcome.name} ${outcome.point || ''} (${odds})`);
                }
              }
            }
          }
          lines.push('');
        } else {
          lines.push('Player Props: Please research available player props for this game');
          lines.push('');
        }
      }

      // Add note about player prop restrictions for certain sports
      if (playerPropExcludedSports.has(game.sportKey)) {
        lines.push('NOTE: Player props are not available for this sport (regulations and/or market availability).');
        lines.push('Focus only on team-based bets: moneyline, spreads, and totals.');
        lines.push('');
      }
    }

    // Add sport-specific factors
    const factors = getFactorsForSport(sportKey);
    lines.push(`Consider the following factors specific to ${sportName}:`);

    factors.forEach((factor, i) => {
      lines.push(`${i + 1}. ${factor}`);
    });

    // Add enhanced weather instructions for outdoor sports only
    const outdoorSports = ['americanfootball_nfl', 'americanfootball_ncaaf', 'baseball_mlb', 'soccer_usa_mls', 'soccer_epl'];
    if (outdoorSports.includes(sportKey)) {
      lines.push('');
      lines.push('WEATHER ANALYSIS REQUIRED:');
      lines.push('Research current forecast for game location at game time:');
      lines.push('- Temperature & wind speed/direction (affects passing, kicking, fly balls)');
      lines.push('- Precipitation forecast (rain/snow affects ball handling, field conditions)');

      if (sportKey === 'baseball_mlb' || sportKey === 'americanfootball_nfl') {
        lines.push('- Check if stadium has retractable roof/dome and likely roof status');
      }

      lines.push('- Consider historical team performance in similar weather conditions');
    }

    lines.push('');
    lines.push('---');
    lines.push('');
  }

  // Add betting math framework
  lines.push('BETTING MATH FRAMEWORK:');
  lines.push('For each bet recommendation, calculate and include:');
  lines.push('');
  lines.push('1. Implied Probability:');
  lines.push('   - Negative odds (-X): Implied % = X / (X + 100) × 100');
  lines.push('   - Positive odds (+X): Implied % = 100 / (X + 100) × 100');
  lines.push('   - Example: -110 = 110/(110+100) = 52.38% implied probability');
  lines.push('   - Example: +150 = 100/(150+100) = 40.00% implied probability');
  lines.push('');
  lines.push('2. True Probability Assessment:');
  lines.push('   - Based on your analysis, what is the ACTUAL win probability?');
  lines.push('   - Compare true probability vs implied probability to find value');
  lines.push('   - Only recommend if true probability > implied probability');
  lines.push('');
  lines.push('3. Expected Value (EV) Calculation:');
  lines.push('   - EV = (True Probability × Win Amount) - (Lose Probability × Bet Amount)');
  lines.push('   - Positive EV = Value bet (recommend)');
  lines.push('   - Negative EV = Bad bet (avoid)');
  lines.push('   - Example: True prob 55% at -110 odds:');
  lines.push('     * Win: $90.91 profit on $100 bet');
  lines.push('     * Lose: -$100');
  lines.push('     * EV = (0.55 × $90.91) - (0.45 × $100) = $50.00 - $45.00 = +$5.00 ✅');
  lines.push('');
  lines.push('4. Break-Even Percentage:');
  lines.push('   - For -110 odds, need to win 52.38% to break even');
  lines.push('   - For +150 odds, need to win 40% to break even');
  lines.push('   - Only recommend if your true probability exceeds break-even %');
  lines.push('');

  // Add lineup verification instructions for team sports
  const hasTeamSports = selectedGames.some(g => teamSports.includes(g.sportKey));

  if (hasTeamSports) {
    lines.push('CRITICAL - LINEUP VERIFICATION REQUIRED:');
    lines.push('Before making ANY player-specific recommendations (player props, individual performances, etc.):');
    lines.push('1. Verify the current starting lineup for each team');
    lines.push('2. Confirm each player\'s status (Active, Questionable, Doubtful, Out, IR)');
    lines.push('3. Check for recent injury reports and practice participation');
    lines.push('4. DO NOT recommend props for players who are Out, on IR, or unlikely to play');
    lines.push('5. For Questionable players, note the uncertainty and recommend alternatives');
    lines.push('');
    lines.push('If you cannot verify a player\'s current status, state this clearly and avoid recommending bets involving that player.');
    lines.push('');
  }

  // Add data freshness instructions
  lines.push('DATA FRESHNESS REQUIREMENTS:');
  lines.push('Before making recommendations, verify the recency of all information:');
  lines.push('1. Only use injury/lineup data updated within the last 24 hours');
  lines.push('2. For each key fact, note when it was last reported (e.g., "as of Nov 30")');
  lines.push('3. If data appears stale or undated, explicitly state this uncertainty');
  lines.push('4. Cross-reference multiple sources when possible to confirm current status');
  lines.push('');

  // Enhanced odds comparison instructions
  if (selectedSportsbooks.length > 1) {
    lines.push('IMPORTANT - Odds Comparison & Line Shopping:');
    lines.push(`Compare odds across all ${selectedSportsbooks.length} selected sportsbooks for each bet.`);
    lines.push('For each recommended bet, identify which sportsbook offers the best value.');
    lines.push('Include odds comparison in your analysis (e.g., "DraftKings -110 vs FanDuel -105 - FanDuel offers 5-point advantage").');
    lines.push('Highlight when there are significant differences (5+ points) between sportsbooks.');
    lines.push('Note: Even small differences in odds can significantly impact long-term profitability.');
    lines.push('');
  }

  // Add bet type restrictions with strong emphasis
  const allBetTypes = ['h2h', 'spreads', 'totals', 'player_props', 'sgpx', 'alternates'];
  const excludedBetTypes = allBetTypes.filter(bt => !effectiveBetTypes.includes(bt));

  if (excludedBetTypes.length > 0) {
    const betTypeNames = {
      'h2h': 'Moneyline bets',
      'spreads': 'Spread bets',
      'totals': 'Total (Over/Under) bets',
      'player_props': 'Player Props',
      'sgpx': 'SGPx parlays',
      'alternates': 'Alternate Lines'
    };

    lines.push('CRITICAL - BET TYPE RESTRICTIONS:');
    lines.push('You MUST ONLY recommend the following bet types:');
    for (const bt of effectiveBetTypes) {
      lines.push(`  ✓ ${betTypeNames[bt] || bt}`);
    }
    lines.push('');
    lines.push('NEVER suggest the following bet types under any circumstances:');
    for (const bt of excludedBetTypes) {
      lines.push(`  ✗ ${betTypeNames[bt] || bt}`);
    }
    lines.push('');
    lines.push('Any recommendation that includes an excluded bet type will be rejected.');
    lines.push('');
  }

  // Add parlay correlation analysis if parlays are included
  if (betStyle === 'Parlay') {
    lines.push('PARLAY CONSTRUCTION GUIDELINES:');
    lines.push('');
    lines.push('1. Correlation Analysis:');
    lines.push('   - AVOID highly correlated bets in same parlay:');
    lines.push('     * Team A ML + Team A spread (highly correlated)');
    lines.push('     * Team A ML + Over (moderately correlated - if team wins, more likely to go over)');
    lines.push('     * Player prop + Team total (correlated)');
    lines.push('   - PREFER uncorrelated bets:');
    lines.push('     * Different games');
    lines.push('     * Different bet types from different games');
    lines.push('     * Independent outcomes');
    lines.push('');
    lines.push('2. Same Game Parlay (SGP) Considerations:');
    lines.push('   - SGPs often have worse odds due to correlation');
    lines.push('   - Only recommend if value is exceptional');
    lines.push('   - Example of good SGP: Team A -3.5 + Under 230.5 (if expecting low-scoring win)');
    lines.push('');
    lines.push('3. Cross-Game Parlays:');
    lines.push('   - Better value typically');
    lines.push('   - Less correlation risk');
    lines.push('   - Can mix different sports for diversification');
    lines.push('');
    lines.push('4. Leg Selection Strategy:');
    lines.push('   - Mix favorites and underdogs (don\'t stack all favorites)');
    lines.push('   - Target 55-60% true probability per leg');
    lines.push('   - For 3-leg parlay: Need ~18% combined probability to be profitable at typical odds');
    lines.push('');
  }

  // Final instructions based on bet style
  lines.push('Recommendations Requested:');

  if (betStyle === 'Straight') {
    const recCount = parlayPreferences.recommendationCount || 3;
    lines.push(`- Provide at least ${recCount} straight bet recommendations in the ${formatOdds(parlayPreferences.minOdds)} to ${formatOdds(parlayPreferences.maxOdds)} odds range`);
    lines.push('- Include a confidence rating (1-5 stars) for each bet WITH SUPPORTING EVIDENCE:');
    lines.push('  ★★★★★ = Very High Confidence - cite 3+ verified supporting factors');
    lines.push('  ★★★★☆ = High Confidence - cite 2-3 verified supporting factors');
    lines.push('  ★★★☆☆ = Medium Confidence - cite 1-2 supporting factors with some uncertainty');
    lines.push('  ★★☆☆☆ = Low Confidence - limited data or conflicting information');
    lines.push('  ★☆☆☆☆ = Speculative - gut feel or incomplete data');
    lines.push('- For each rating, list the specific facts that justify that confidence level');
    lines.push('- Provide analysis and reasoning for each bet');
    lines.push('- Identify the best sportsbook for each bet');
    lines.push('');
    lines.push('IMPORTANT: Do NOT suggest any parlays. Only individual straight bets.');
  } else {
    const recCount = parlayPreferences.recommendationCount || 3;
    lines.push(`- Provide at least ${recCount} straight bet recommendations`);
    lines.push(`- Provide at least ${recCount} parlay recommendations`);
    lines.push(`- Parlays should have ${parlayPreferences.minLegs}-${parlayPreferences.maxLegs} legs with ${formatOdds(parlayPreferences.minOdds)} to ${formatOdds(parlayPreferences.maxOdds)} total odds`);
    lines.push('- Include a confidence rating (1-5 stars) for each bet/parlay WITH SUPPORTING EVIDENCE:');
    lines.push('  ★★★★★ = Very High Confidence - cite 3+ verified supporting factors');
    lines.push('  ★★★★☆ = High Confidence - cite 2-3 verified supporting factors');
    lines.push('  ★★★☆☆ = Medium Confidence - cite 1-2 supporting factors with some uncertainty');
    lines.push('  ★★☆☆☆ = Low Confidence - limited data or conflicting information');
    lines.push('  ★☆☆☆☆ = Speculative - gut feel or incomplete data');
    lines.push('- For each rating, list the specific facts that justify that confidence level');
    lines.push('- Provide analysis and reasoning for each pick');
    lines.push('- Identify the best sportsbook for each bet');
  }

  const canRecommendPlayerProps = effectiveBetTypes.includes('player_props') &&
    selectedGames.some(g => !playerPropExcludedSports.has(g.sportKey));

  if (canRecommendPlayerProps) {
    lines.push('- High-value player prop opportunities');
    lines.push('  * Consider usage trends, matchup advantages, recent form');
    lines.push('  * Factor in game script (blowout = bench time)');
    lines.push('  * Compare prop line to recent averages');
  }

  if (effectiveBetTypes.includes('sgpx')) {
    lines.push('- SGPx (Same Game Parlay Extra) opportunities');
  }

  if (effectiveBetTypes.includes('alternates')) {
    lines.push('- Alternate lines (spreads, totals, props)');
    lines.push('  * Consider alternate lines for better value or higher confidence');
    lines.push('  * Note: Odds typically get worse as alternates become more likely');
  }

  lines.push('');

  // Add bankroll management guidance
  lines.push('BANKROLL MANAGEMENT:');
  lines.push('1. Unit Sizing:');
  lines.push('   - 1 unit = 1% of total bankroll (standard)');
  lines.push('   - High confidence (★★★★★): 2-3 units');
  lines.push('   - Medium confidence (★★★☆☆): 1 unit');
  lines.push('   - Low confidence (★★☆☆☆): 0.5 units');
  lines.push('   - Speculative (★☆☆☆☆): 0.25 units or skip');
  lines.push('');
  lines.push('2. Parlay Sizing:');
  lines.push('   - Parlays should be smaller units than straight bets');
  lines.push('   - 3-leg parlay: 0.5-1 unit max');
  lines.push('   - 4+ leg parlay: 0.25-0.5 unit max');
  lines.push('   - Higher variance = smaller bet size');
  lines.push('');
  lines.push('3. Risk Management:');
  lines.push('   - Never bet more than 5% of bankroll on single bet');
  lines.push('   - Limit total daily exposure to 10-15% of bankroll');
  lines.push('');

  // Add risk level guidance
  const riskLevel = parlayPreferences.riskLevel || 'average';
  if (riskLevel === 'conservative') {
    lines.push('RISK PREFERENCE: Conservative');
    lines.push('- Prioritize high-probability bets with lower payouts');
    lines.push('- Focus on heavy favorites and likely outcomes');
    lines.push('- Avoid longshots and high-variance plays');
    lines.push('- Target bets with 60%+ true probability');
    lines.push('');
  } else if (riskLevel === 'aggressive') {
    lines.push('RISK PREFERENCE: Aggressive');
    lines.push('- Include higher-risk, higher-reward opportunities');
    lines.push('- Consider underdogs and longshot parlays with big payouts');
    lines.push('- Willing to accept lower win probability for larger potential returns');
    lines.push('- Can target bets with 45%+ true probability if value is exceptional');
    lines.push('');
  } else {
    lines.push('RISK PREFERENCE: Balanced');
    lines.push('- Mix of safe plays and moderate risk opportunities');
    lines.push('- Balance win probability with potential payout');
    lines.push('- Target bets with 52-58% true probability range');
    lines.push('');
  }

  // Add SGPx explanation if selected
  if (effectiveBetTypes.includes('sgpx')) {
    lines.push('SGPx Definition:');
    lines.push('SGPx combines multiple Same Game Parlays (SGPs) from different games into one large parlay.');
    lines.push('- At least one leg must be an SGP (multiple bets from the same game with correlated outcomes)');
    lines.push('- Can mix SGPs with single-leg bets from other games');
    lines.push('- Cannot combine single bets and SGPs from the same game');
    lines.push('- Available on DraftKings (similar to FanDuel\'s SGP+ or Bet365\'s Bet Builder+)');
    lines.push('- Example: Heat -6 + O239.5 (SGP from Game 1) + Lakers ML (single from Game 2)');
    lines.push('');
  }

  // Add alternate lines explanation if selected
  if (effectiveBetTypes.includes('alternates')) {
    lines.push('Alternate Lines:');
    lines.push('Consider alternate lines that may offer better value than standard lines.');
    lines.push('- Alternate Spreads: Move the spread up/down (e.g., -3.5 standard vs -1.5 or -5.5 alternate)');
    lines.push('- Alternate Totals: Adjust over/under number (e.g., O230.5 standard vs O235.5 or O225.5 alternate)');
    lines.push('- Alternate Props: Different thresholds for player props (e.g., 25.5 pts standard vs 22.5 or 28.5 alternate)');
    lines.push('- Odds typically get worse as alternates become more likely (e.g., -3.5 at -110 vs -1.5 at -200)');
    lines.push('- Useful for building parlays with higher confidence legs or reaching target odds ranges');
    lines.push('- Research current alternate line offerings on the selected sportsbooks');
    lines.push('');
  }

  // Only include parlay calculation instructions for parlay bets
  if (betStyle === 'Parlay') {
    lines.push('IMPORTANT - Calculating Parlay Odds:');
    lines.push('1. Convert each leg\'s American odds to decimal:');
    lines.push('   - Positive odds (+X): decimal = (X / 100) + 1');
    lines.push('   - Negative odds (-X): decimal = (100 / X) + 1');
    lines.push('   Example: -110 = (100 / 110) + 1 = 1.909');
    lines.push('   Example: +150 = (150 / 100) + 1 = 2.500');
    lines.push('2. Multiply all decimal odds together');
    lines.push('3. Convert back to American odds:');
    lines.push('   - If result >= 2.0: American = (decimal - 1) * 100');
    lines.push('   - If result < 2.0: American = -100 / (decimal - 1)');
    lines.push('');
  }

  // Enhanced recommendation format
  lines.push('RECOMMENDATION FORMAT:');
  lines.push('For each bet, provide in this structure:');
  lines.push('');
  lines.push('[BET TYPE] - [TEAM/PLAYER] - [LINE] @ [SPORTSBOOK]');
  lines.push('Odds: [ODDS] | Implied Probability: [%] | True Probability: [%] | EV: [+/-$X.XX]');
  lines.push('Confidence: [★★★★★] | Units: [X]');
  lines.push('');
  lines.push('ANALYSIS:');
  lines.push('- [Key supporting factors with dates/sources]');
  lines.push('- [Matchup advantages]');
  lines.push('- [Recent trends]');
  lines.push('- [Situational factors]');
  lines.push('');
  lines.push('RISKS:');
  lines.push('- [Potential concerns]');
  lines.push('- [What could go wrong]');
  lines.push('');
  lines.push('VALUE RATIONALE:');
  lines.push('- Why this bet has positive expected value');
  lines.push('- Comparison to other sportsbooks');
  lines.push('- Market context');
  lines.push('');

  // Add evidence requirements
  lines.push('EVIDENCE REQUIREMENTS:');
  lines.push('For each recommendation, provide:');
  lines.push('- The specific current facts supporting your pick (with dates when available)');
  lines.push('- Any concerning factors or risks you identified');
  lines.push('- Confidence rating justified by the evidence, not assumptions');
  lines.push('- Expected value calculation showing why it\'s a value bet');
  lines.push('');

  lines.push('Note: For sportsbooks without listed odds, please research current lines and include in analysis.');

  return lines.join('\n');
}

function buildOddsLinesEnhanced(lines, bookmaker, selectedBetTypes, game, oddsComparison) {
  let hasAnyMarkets = false;

  // Moneyline
  if (selectedBetTypes.includes('h2h')) {
    const h2hMarket = bookmaker.markets?.find(m => m.key === 'h2h');
    if (h2hMarket) {
      const homeOdds = h2hMarket.outcomes?.find(o => o.name === game.homeTeam);
      const awayOdds = h2hMarket.outcomes?.find(o => o.name === game.awayTeam);

      if (homeOdds && awayOdds) {
        const awayFormatted = formatOddsWithImplied(awayOdds.price);
        const homeFormatted = formatOddsWithImplied(homeOdds.price);
        lines.push(`    Moneyline: ${game.awayTeam} ${awayFormatted} | ${game.homeTeam} ${homeFormatted}`);
        
        // Track for comparison
        if (!oddsComparison.moneyline) oddsComparison.moneyline = {};
        if (!oddsComparison.moneyline[game.awayTeam]) oddsComparison.moneyline[game.awayTeam] = [];
        if (!oddsComparison.moneyline[game.homeTeam]) oddsComparison.moneyline[game.homeTeam] = [];
        oddsComparison.moneyline[game.awayTeam].push({ odds: awayOdds.price, book: bookmaker.title || bookmaker.key });
        oddsComparison.moneyline[game.homeTeam].push({ odds: homeOdds.price, book: bookmaker.title || bookmaker.key });
        
        hasAnyMarkets = true;
      }
    }
  }

  // Spreads
  if (selectedBetTypes.includes('spreads')) {
    const spreadMarket = bookmaker.markets?.find(m => m.key === 'spreads');
    if (spreadMarket) {
      const homeSpread = spreadMarket.outcomes?.find(o => o.name === game.homeTeam);
      const awaySpread = spreadMarket.outcomes?.find(o => o.name === game.awayTeam);

      if (homeSpread && awaySpread) {
        const awayFormatted = `${formatPoint(awaySpread.point)} (${formatOddsWithImplied(awaySpread.price)})`;
        const homeFormatted = `${formatPoint(homeSpread.point)} (${formatOddsWithImplied(homeSpread.price)})`;
        lines.push(`    Spread: ${game.awayTeam} ${awayFormatted} | ${game.homeTeam} ${homeFormatted}`);
        
        // Track for comparison
        if (!oddsComparison.spread) oddsComparison.spread = {};
        const awayKey = `${game.awayTeam} ${formatPoint(awaySpread.point)}`;
        const homeKey = `${game.homeTeam} ${formatPoint(homeSpread.point)}`;
        if (!oddsComparison.spread[awayKey]) oddsComparison.spread[awayKey] = [];
        if (!oddsComparison.spread[homeKey]) oddsComparison.spread[homeKey] = [];
        oddsComparison.spread[awayKey].push({ odds: awaySpread.price, book: bookmaker.title || bookmaker.key });
        oddsComparison.spread[homeKey].push({ odds: homeSpread.price, book: bookmaker.title || bookmaker.key });
        
        hasAnyMarkets = true;
      }
    }
  }

  // Totals
  if (selectedBetTypes.includes('totals')) {
    const totalMarket = bookmaker.markets?.find(m => m.key === 'totals');
    if (totalMarket) {
      const over = totalMarket.outcomes?.find(o => o.name === 'Over');
      const under = totalMarket.outcomes?.find(o => o.name === 'Under');

      if (over && under) {
        const overFormatted = `O${over.point} (${formatOddsWithImplied(over.price)})`;
        const underFormatted = `U${under.point} (${formatOddsWithImplied(under.price)})`;
        lines.push(`    Total: ${overFormatted} | ${underFormatted}`);
        
        // Track for comparison
        if (!oddsComparison.total) oddsComparison.total = {};
        const overKey = `Over ${over.point}`;
        const underKey = `Under ${under.point}`;
        if (!oddsComparison.total[overKey]) oddsComparison.total[overKey] = [];
        if (!oddsComparison.total[underKey]) oddsComparison.total[underKey] = [];
        oddsComparison.total[overKey].push({ odds: over.price, book: bookmaker.title || bookmaker.key });
        oddsComparison.total[underKey].push({ odds: under.price, book: bookmaker.title || bookmaker.key });
        
        hasAnyMarkets = true;
      }
    }
  }

  if (!hasAnyMarkets) {
    lines.push('    (No markets available)');
  }
}

function buildOutrightOddsLines(lines, bookmaker) {
  const maxContenders = 15;

  for (const market of bookmaker.markets || []) {
    const topContenders = (market.outcomes || [])
      .sort((a, b) => a.price - b.price) // Sort by best odds (most favored)
      .slice(0, maxContenders);

    if (topContenders.length > 0) {
      for (const contender of topContenders) {
        const oddsFormatted = formatOddsWithImplied(contender.price);
        lines.push(`    ${contender.name}: ${oddsFormatted}`);
      }
    } else {
      lines.push('    (No participants available)');
    }
  }
}

function formatOdds(odds) {
  if (odds >= 0) {
    return `+${Math.round(odds)}`;
  }
  return `${Math.round(odds)}`;
}

function formatPoint(point) {
  if (point === null || point === undefined) return '';
  if (point > 0) {
    return `+${point}`;
  }
  return `${point}`;
}

function formatCommenceTime(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString('en-US', {
    timeZone: 'America/New_York',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZoneName: 'short'
  });
}

function formatPlayerPropType(marketKey) {
  const propTypes = {
    player_points: 'Points',
    player_rebounds: 'Rebounds',
    player_assists: 'Assists',
    player_pass_tds: 'Passing TDs',
    player_pass_yds: 'Passing Yards',
    player_rush_yds: 'Rushing Yards',
    batter_hits: 'Hits',
    batter_home_runs: 'Home Runs',
    batter_total_bases: 'Total Bases'
  };

  if (propTypes[marketKey]) {
    return propTypes[marketKey];
  }

  // Default: convert snake_case to Title Case
  return marketKey
    .replace('player_', '')
    .replace('batter_', '')
    .replace(/_/g, ' ')
    .toUpperCase();
}

module.exports = {
  generatePrompt
};


