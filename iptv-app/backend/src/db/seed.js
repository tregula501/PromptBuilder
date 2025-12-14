const bcrypt = require('bcrypt');
const logger = require('../utils/logger');

const SALT_ROUNDS = 12;

async function seedAdmin(db) {
  const username = process.env.ADMIN_USERNAME || 'admin';
  const password = process.env.ADMIN_PASSWORD;

  if (!password) {
    logger.warn('ADMIN_PASSWORD not set, skipping admin seed');
    return;
  }

  // Check if admin already exists
  const existing = db.prepare('SELECT id FROM users WHERE username = ?').get(username);
  if (existing) {
    logger.info(`Admin user '${username}' already exists`);
    return;
  }

  // Hash password and create admin
  const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

  db.prepare(`
    INSERT INTO users (username, password_hash, role)
    VALUES (?, ?, 'admin')
  `).run(username, passwordHash);

  logger.info(`Admin user '${username}' created successfully`);
}

module.exports = { seedAdmin };
