// Sport-specific analysis factors and display names
const sportFactors = {
  americanfootball_nfl: [
    'Key injuries and player availability',
    'Recent performance and momentum (last 3-5 games)',
    'Head-to-head history and matchup trends',
    'Weather conditions (temperature, wind, precipitation)'
  ],
  americanfootball_ncaaf: [
    'Key injuries and player availability',
    'Recent performance and momentum (last 3-5 games)',
    'Head-to-head history and matchup trends',
    'Weather conditions (temperature, wind, precipitation)',
    'Home field advantage and crowd impact'
  ],
  basketball_nba: [
    'Injuries and player availability',
    'Recent form and momentum (last 5 games)',
    'Home/away splits and performance',
    'Back-to-back games and rest days',
    'Pace and style matchup'
  ],
  basketball_ncaab: [
    'Injuries and player availability',
    'Recent form and momentum (last 5 games)',
    'Home court advantage',
    'Back-to-back games and rest days',
    'Conference strength and matchup'
  ],
  basketball_wncaab: [
    'Injuries and player availability',
    'Recent form and momentum (last 5 games)',
    'Home court advantage',
    'Travel/rest and schedule density',
    'Conference strength and matchup'
  ],
  basketball_wnba: [
    'Injuries and player availability',
    'Recent form and momentum (last 5 games)',
    'Home/away splits and performance',
    'Back-to-back games and rest days',
    'Pace and style matchup'
  ],
  baseball_mlb: [
    'Starting pitcher matchups and recent performance',
    'Key injuries to position players',
    'Recent team form (last 7-10 games)',
    'Weather conditions (wind direction, temperature)',
    'Home/away splits and ballpark factors'
  ],
  icehockey_nhl: [
    'Starting goalie matchups and recent performance',
    'Key injuries to skaters',
    'Recent form and momentum (last 5 games)',
    'Home/away splits',
    'Rest days and back-to-back situations'
  ],
  icehockey_ncaa: [
    'Likely starting goalie and recent performance (if known)',
    'Key injuries and lineup changes',
    'Recent form and momentum (last 5 games)',
    'Special teams (power play / penalty kill) matchup',
    'Rest/travel and back-to-back situations'
  ],
  soccer_usa_mls: [
    'Injuries and lineup changes',
    'Recent form (last 5 matches)',
    'Head-to-head record',
    'Home/away performance splits',
    'Weather conditions (temperature, wind, precipitation)'
  ],
  soccer_epl: [
    'Injuries and lineup changes',
    'Recent form (last 5 matches)',
    'Head-to-head record',
    'Home/away performance splits',
    'European competition schedule impact',
    'Weather conditions (temperature, wind, precipitation)'
  ],
  mma_mixed_martial_arts: [
    'Fighter records and recent performance',
    'Fighting styles matchup (striking vs grappling)',
    'Weight class history and weight cut concerns',
    'Reach and physical advantages'
  ],
  // Tennis - Hard Court
  // NOTE: keys are aligned to frontend/src/data/sports.js
  tennis_atp_aus_open_singles: [
    'Surface: Hard court - favors aggressive baseline players',
    'Head-to-head record and recent matchups',
    'Recent form and tournament momentum',
    'Player ranking, seeding, and current world ranking',
    'Serve statistics (aces, first serve %, break points saved)',
    'Injury status and physical condition',
    'Historical performance at Australian Open'
  ],
  tennis_wta_aus_open_singles: [
    'Surface: Hard court - favors aggressive baseline players',
    'Head-to-head record and recent matchups',
    'Recent form and tournament momentum',
    'Player ranking, seeding, and current world ranking',
    'Serve statistics (aces, first serve %, break points saved)',
    'Injury status and physical condition',
    'Historical performance at Australian Open'
  ],
  tennis_atp_us_open: [
    'Surface: Hard court - favors aggressive baseline players',
    'Head-to-head record and recent matchups',
    'Recent form and tournament momentum',
    'Player ranking, seeding, and current world ranking',
    'Serve statistics (aces, first serve %, break points saved)',
    'Injury status and physical condition',
    'Historical performance at US Open'
  ],
  tennis_wta_us_open: [
    'Surface: Hard court - favors aggressive baseline players',
    'Head-to-head record and recent matchups',
    'Recent form and tournament momentum',
    'Player ranking, seeding, and current world ranking',
    'Serve statistics (aces, first serve %, break points saved)',
    'Injury status and physical condition',
    'Historical performance at US Open'
  ],
  tennis_atp_indian_wells: [
    'Surface: Hard court - favors powerful servers and baseline players',
    'Head-to-head record and recent matchups',
    'Recent form and tournament momentum',
    'Player ranking, seeding, and current world ranking',
    'Serve statistics and return game effectiveness',
    'Injury status and physical condition'
  ],
  tennis_wta_indian_wells: [
    'Surface: Hard court - favors powerful servers and baseline players',
    'Head-to-head record and recent matchups',
    'Recent form and tournament momentum',
    'Player ranking, seeding, and current world ranking',
    'Serve statistics and return game effectiveness',
    'Injury status and physical condition'
  ],
  tennis_atp_miami_open: [
    'Surface: Hard court - favors powerful servers and baseline players',
    'Head-to-head record and recent matchups',
    'Recent form and tournament momentum',
    'Player ranking, seeding, and current world ranking',
    'Serve statistics and return game effectiveness',
    'Injury status and physical condition'
  ],
  tennis_wta_miami_open: [
    'Surface: Hard court - favors powerful servers and baseline players',
    'Head-to-head record and recent matchups',
    'Recent form and tournament momentum',
    'Player ranking, seeding, and current world ranking',
    'Serve statistics and return game effectiveness',
    'Injury status and physical condition'
  ],
  // Tennis - Clay Court
  tennis_atp_french_open: [
    'Surface: Clay court - favors defensive players with strong groundstrokes',
    'Head-to-head record, especially on clay',
    'Recent clay court form and results',
    'Player ranking, seeding, and clay court expertise',
    'Stamina and physical endurance (longer rallies on clay)',
    'Injury status and ability to handle grueling matches',
    'Historical performance at French Open'
  ],
  tennis_wta_french_open: [
    'Surface: Clay court - favors defensive players with strong groundstrokes',
    'Head-to-head record, especially on clay',
    'Recent clay court form and results',
    'Player ranking, seeding, and clay court expertise',
    'Stamina and physical endurance (longer rallies on clay)',
    'Injury status and ability to handle grueling matches',
    'Historical performance at French Open'
  ],
  tennis_atp_madrid_open: [
    'Surface: Clay court (high altitude) - faster than typical clay',
    'Head-to-head record, especially on clay',
    'Recent clay court form and results',
    'Player ranking and clay court expertise',
    'Adaptation to high-altitude conditions',
    'Injury status and physical condition'
  ],
  tennis_wta_madrid_open: [
    'Surface: Clay court (high altitude) - faster than typical clay',
    'Head-to-head record, especially on clay',
    'Recent clay court form and results',
    'Player ranking and clay court expertise',
    'Adaptation to high-altitude conditions',
    'Injury status and physical condition'
  ],
  tennis_atp_italian_open: [
    'Surface: Clay court - favors defensive grinders',
    'Head-to-head record, especially on clay',
    'Recent clay court form (key French Open warm-up)',
    'Player ranking and clay court expertise',
    'Stamina and ability to handle long rallies',
    'Injury status and physical condition'
  ],
  tennis_wta_italian_open: [
    'Surface: Clay court - favors defensive grinders',
    'Head-to-head record, especially on clay',
    'Recent clay court form (key French Open warm-up)',
    'Player ranking and clay court expertise',
    'Stamina and ability to handle long rallies',
    'Injury status and physical condition'
  ],
  // Tennis - Grass Court
  tennis_atp_wimbledon: [
    'Surface: Grass court - heavily favors big servers and net players',
    'Head-to-head record, especially on grass',
    'Recent grass court form (limited grass season)',
    'Player ranking, seeding, and grass court expertise',
    'Serve and volley effectiveness, slice shots',
    'Injury status and movement on grass',
    'Historical performance at Wimbledon'
  ],
  tennis_wta_wimbledon: [
    'Surface: Grass court - heavily favors big servers and net players',
    'Head-to-head record, especially on grass',
    'Recent grass court form (limited grass season)',
    'Player ranking, seeding, and grass court expertise',
    'Serve and volley effectiveness, slice shots',
    'Injury status and movement on grass',
    'Historical performance at Wimbledon'
  ],
  // Golf - Major Championships
  golf_masters_tournament_winner: [
    'Course: Augusta National (par 72) - favors long hitters with exceptional short game',
    'Recent tournament form (last 5-10 events)',
    'Historical performance at Augusta National and The Masters',
    'Current world ranking and major championship experience',
    'Driving distance and accuracy statistics',
    'Greens in regulation (GIR) and putting performance on fast greens',
    'Weather forecast (wind, rain affects scoring significantly)',
    'Track record on par-5 scoring (critical at Augusta)'
  ],
  golf_pga_championship_winner: [
    'Course conditions and setup (varies by venue each year)',
    'Recent tournament form (last 5-10 events)',
    'Historical performance at PGA Championship',
    'Current world ranking and major championship experience',
    'Driving accuracy and distance statistics',
    'Iron play and approach shot accuracy',
    'Weather forecast and course difficulty rating',
    'Performance under pressure in tough conditions'
  ],
  golf_the_open_championship_winner: [
    'Course: Links golf - heavily influenced by wind and weather',
    'Recent links golf experience and performance',
    'Historical performance at The Open Championship',
    'Current world ranking and major championship experience',
    'Wind play ability and shot-shaping skills',
    'Bump-and-run short game proficiency',
    'Weather forecast (wind speed/direction is critical)',
    'Experience playing in British conditions'
  ],
  golf_us_open_winner: [
    'Course: Extremely difficult USGA setup - narrow fairways, thick rough',
    'Recent tournament form (last 5-10 events)',
    'Historical performance at U.S. Open',
    'Current world ranking and major championship experience',
    'Driving accuracy (more important than distance)',
    'Iron precision and ability to hit greens in regulation',
    'Weather forecast and course difficulty',
    'Mental toughness and ability to grind out pars'
  ]
};

const sportNames = {
  americanfootball_nfl: 'NFL',
  americanfootball_ncaaf: 'NCAAF',
  basketball_nba: 'NBA',
  basketball_ncaab: 'NCAAB',
  basketball_wncaab: 'WNCAAB',
  basketball_wnba: 'WNBA',
  baseball_mlb: 'MLB',
  icehockey_nhl: 'NHL',
  icehockey_ncaa: 'NCAA Hockey',
  soccer_usa_mls: 'MLS',
  soccer_epl: 'Premier League',
  mma_mixed_martial_arts: 'UFC/MMA',
  // Tennis - ATP
  tennis_atp_aus_open_singles: 'Tennis - ATP Australian Open',
  tennis_atp_french_open: 'Tennis - ATP French Open',
  tennis_atp_wimbledon: 'Tennis - ATP Wimbledon',
  tennis_atp_us_open: 'Tennis - ATP US Open',
  tennis_atp_indian_wells: 'Tennis - ATP Indian Wells',
  tennis_atp_miami_open: 'Tennis - ATP Miami Open',
  tennis_atp_monte_carlo_masters: 'Tennis - ATP Monte-Carlo Masters',
  tennis_atp_madrid_open: 'Tennis - ATP Madrid Open',
  tennis_atp_italian_open: 'Tennis - ATP Italian Open',
  tennis_atp_canadian_open: 'Tennis - ATP Canadian Open',
  tennis_atp_cincinnati_open: 'Tennis - ATP Cincinnati Open',
  tennis_atp_shanghai_masters: 'Tennis - ATP Shanghai Masters',
  tennis_atp_paris_masters: 'Tennis - ATP Paris Masters',
  tennis_atp_dubai: 'Tennis - ATP Dubai',
  tennis_atp_qatar_open: 'Tennis - ATP Qatar Open',
  tennis_atp_china_open: 'Tennis - ATP China Open',
  // Tennis - WTA
  tennis_wta_aus_open_singles: 'Tennis - WTA Australian Open',
  tennis_wta_french_open: 'Tennis - WTA French Open',
  tennis_wta_wimbledon: 'Tennis - WTA Wimbledon',
  tennis_wta_us_open: 'Tennis - WTA US Open',
  tennis_wta_indian_wells: 'Tennis - WTA Indian Wells',
  tennis_wta_miami_open: 'Tennis - WTA Miami Open',
  tennis_wta_madrid_open: 'Tennis - WTA Madrid Open',
  tennis_wta_italian_open: 'Tennis - WTA Italian Open',
  tennis_wta_canadian_open: 'Tennis - WTA Canadian Open',
  tennis_wta_cincinnati_open: 'Tennis - WTA Cincinnati Open',
  tennis_wta_dubai: 'Tennis - WTA Dubai Championships',
  tennis_wta_qatar_open: 'Tennis - WTA Qatar Open',
  tennis_wta_china_open: 'Tennis - WTA China Open',
  tennis_wta_wuhan_open: 'Tennis - WTA Wuhan Open',
  // Golf - Major Championships
  golf_masters_tournament_winner: 'Golf - Masters Tournament',
  golf_pga_championship_winner: 'Golf - PGA Championship',
  golf_the_open_championship_winner: 'Golf - The Open Championship',
  golf_us_open_winner: 'Golf - U.S. Open'
};

function getFactorsForSport(sportKey) {
  if (sportFactors[sportKey]) {
    return sportFactors[sportKey];
  }
  // Default factors if sport not found
  return [
    'Injuries and player availability',
    'Recent performance and form',
    'Head-to-head history',
    'Home/away splits'
  ];
}

function getSportDisplayName(sportKey) {
  return sportNames[sportKey] || sportKey;
}

module.exports = {
  getFactorsForSport,
  getSportDisplayName
};
