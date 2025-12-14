const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const rateLimit = require('express-rate-limit');
const cron = require('node-cron');

const { initDatabase } = require('./config/database');
const { seedAdmin } = require('./db/seed');
const logger = require('./utils/logger');

// Routes
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const channelRoutes = require('./routes/channels');
const streamRoutes = require('./routes/stream');
const healthRoutes = require('./routes/health');
const favoriteRoutes = require('./routes/favorites');

// Services
const PlaylistManager = require('./services/playlistManager');
const HealthChecker = require('./services/healthChecker');
const VPNHealth = require('./services/vpnHealth');

const app = express();
const PORT = process.env.PORT || 4000;

// Trust proxy (for running behind nginx)
app.set('trust proxy', 1);

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"],
      mediaSrc: ["'self'", "blob:"],
    }
  },
  crossOriginEmbedderPolicy: false
}));

// CORS configuration
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'https://iptv.regulaplex.net',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Rate limiting
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: { error: 'Too many requests, please try again later' },
  standardHeaders: true,
  legacyHeaders: false
});

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

// Apply rate limiting to API routes
app.use('/api', apiLimiter);

// Initialize services
let playlistManager;
let healthChecker;
let vpnHealth;

async function initServices() {
  // Initialize database
  const db = initDatabase();

  // Seed admin user
  await seedAdmin(db);

  // Initialize playlist manager
  playlistManager = new PlaylistManager(process.env.M3U_URL);
  await playlistManager.initialize();

  // Initialize VPN health checker
  vpnHealth = new VPNHealth();

  // Initialize stream health checker
  healthChecker = new HealthChecker(playlistManager, db);

  // Store in app locals for route access
  app.locals.db = db;
  app.locals.playlistManager = playlistManager;
  app.locals.healthChecker = healthChecker;
  app.locals.vpnHealth = vpnHealth;

  logger.info('Services initialized successfully');
}

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/channels', channelRoutes);
app.use('/api/stream', streamRoutes);
app.use('/api/health', healthRoutes);
app.use('/api/favorites', favoriteRoutes);

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Start server
async function start() {
  try {
    await initServices();

    // Clear stale health data on startup (rate-limited data is unreliable)
    try {
      const db = app.locals.db;
      db.prepare('DELETE FROM health_checks').run();
      logger.info('Cleared stale health check data on startup');
    } catch (err) {
      logger.warn('Could not clear health data:', err.message);
    }

    // Run health check every 30 minutes, checking 50 channels each time
    // With 1924 channels, full coverage takes ~19 hours (spread throughout day)
    cron.schedule('*/30 * * * *', async () => {
      logger.info('Starting scheduled health check');
      await healthChecker.runHealthCheck();
    });

    // Initial health check after 5 minutes (give VPN time to stabilize)
    setTimeout(() => {
      healthChecker.runHealthCheck();
    }, 5 * 60 * 1000);

    app.listen(PORT, () => {
      logger.info(`IPTV Backend running on port ${PORT}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

start();
