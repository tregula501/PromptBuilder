export const sports = [
  { key: 'basketball_nba', title: 'NBA', description: 'National Basketball Association', active: true },
  { key: 'baseball_mlb', title: 'MLB', description: 'Major League Baseball', active: true },
  { key: 'icehockey_nhl', title: 'NHL', description: 'National Hockey League', active: true },
  { key: 'icehockey_ncaa', title: 'NCAA Hockey', description: 'College Hockey (manual research)', active: true, manualOnly: true },
  { key: 'americanfootball_nfl', title: 'NFL', description: 'National Football League', active: true },
  { key: 'americanfootball_ncaaf', title: 'NCAAF', description: 'College Football', active: true },
  { key: 'basketball_ncaab', title: 'NCAAB', description: 'College Basketball', active: true },
  { key: 'basketball_wncaab', title: 'WNCAAB', description: "Women's College Basketball (NCAA)", active: true },
  { key: 'basketball_wnba', title: 'WNBA', description: "Women's National Basketball Association", active: true },
  { key: 'soccer_usa_mls', title: 'MLS', description: 'Major League Soccer', active: true },
  { key: 'soccer_epl', title: 'Premier League', description: 'English Premier League', active: true },
  { key: 'mma_mixed_martial_arts', title: 'UFC/MMA', description: 'Mixed Martial Arts', active: true },
  {
    key: 'tennis_group',
    title: 'Tennis',
    description: 'All Tennis Tournaments',
    isGroup: true,
    children: [
      // ATP Grand Slams
      { key: 'tennis_atp_aus_open_singles', title: 'ATP Australian Open', description: "Men's Singles", active: true },
      { key: 'tennis_atp_french_open', title: 'ATP French Open', description: "Men's Singles", active: true },
      { key: 'tennis_atp_wimbledon', title: 'ATP Wimbledon', description: "Men's Singles", active: true },
      { key: 'tennis_atp_us_open', title: 'ATP US Open', description: "Men's Singles", active: true },
      // ATP Masters 1000
      { key: 'tennis_atp_indian_wells', title: 'ATP Indian Wells', description: "Men's Singles", active: true },
      { key: 'tennis_atp_miami_open', title: 'ATP Miami Open', description: "Men's Singles", active: true },
      { key: 'tennis_atp_monte_carlo_masters', title: 'ATP Monte-Carlo Masters', description: "Men's Singles", active: true },
      { key: 'tennis_atp_madrid_open', title: 'ATP Madrid Open', description: "Men's Singles", active: true },
      { key: 'tennis_atp_italian_open', title: 'ATP Italian Open', description: "Men's Singles", active: true },
      { key: 'tennis_atp_canadian_open', title: 'ATP Canadian Open', description: "Men's Singles", active: true },
      { key: 'tennis_atp_cincinnati_open', title: 'ATP Cincinnati Open', description: "Men's Singles", active: true },
      { key: 'tennis_atp_shanghai_masters', title: 'ATP Shanghai Masters', description: "Men's Singles", active: true },
      { key: 'tennis_atp_paris_masters', title: 'ATP Paris Masters', description: "Men's Singles", active: true },
      // ATP Other
      { key: 'tennis_atp_dubai', title: 'ATP Dubai', description: "Men's Singles", active: true },
      { key: 'tennis_atp_qatar_open', title: 'ATP Qatar Open', description: "Men's Singles", active: true },
      { key: 'tennis_atp_china_open', title: 'ATP China Open', description: "Men's Singles", active: true },
      // WTA Grand Slams
      { key: 'tennis_wta_aus_open_singles', title: 'WTA Australian Open', description: "Women's Singles", active: true },
      { key: 'tennis_wta_french_open', title: 'WTA French Open', description: "Women's Singles", active: true },
      { key: 'tennis_wta_wimbledon', title: 'WTA Wimbledon', description: "Women's Singles", active: true },
      { key: 'tennis_wta_us_open', title: 'WTA US Open', description: "Women's Singles", active: true },
      // WTA 1000
      { key: 'tennis_wta_indian_wells', title: 'WTA Indian Wells', description: "Women's Singles", active: true },
      { key: 'tennis_wta_miami_open', title: 'WTA Miami Open', description: "Women's Singles", active: true },
      { key: 'tennis_wta_madrid_open', title: 'WTA Madrid Open', description: "Women's Singles", active: true },
      { key: 'tennis_wta_italian_open', title: 'WTA Italian Open', description: "Women's Singles", active: true },
      { key: 'tennis_wta_canadian_open', title: 'WTA Canadian Open', description: "Women's Singles", active: true },
      { key: 'tennis_wta_cincinnati_open', title: 'WTA Cincinnati Open', description: "Women's Singles", active: true },
      // WTA Other
      { key: 'tennis_wta_dubai', title: 'WTA Dubai Championships', description: "Women's Singles", active: true },
      { key: 'tennis_wta_qatar_open', title: 'WTA Qatar Open', description: "Women's Singles", active: true },
      { key: 'tennis_wta_china_open', title: 'WTA China Open', description: "Women's Singles", active: true },
      { key: 'tennis_wta_wuhan_open', title: 'WTA Wuhan Open', description: "Women's Singles", active: true }
    ]
  },
  {
    key: 'golf_group',
    title: 'Golf',
    description: 'Golf Major Championships',
    isGroup: true,
    children: [
      { key: 'golf_masters_tournament_winner', title: 'Masters Tournament', description: 'The Masters at Augusta National', active: true },
      { key: 'golf_pga_championship_winner', title: 'PGA Championship', description: 'PGA Championship', active: true },
      { key: 'golf_the_open_championship_winner', title: 'The Open Championship', description: 'The Open Championship (British Open)', active: true },
      { key: 'golf_us_open_winner', title: 'US Open', description: 'U.S. Open Championship', active: true }
    ]
  }
]

function flattenSports(list) {
  const out = []
  for (const s of list) {
    if (s && Array.isArray(s.children)) {
      for (const child of s.children) out.push(child)
    } else {
      out.push(s)
    }
  }
  return out
}

export function getSportByKey(key) {
  if (!key) return null
  return flattenSports(sports).find(s => s.key === key) || null
}

export function isManualOnlySport(key) {
  return Boolean(getSportByKey(key)?.manualOnly)
}
