# Production stage
FROM node:20-alpine

WORKDIR /app

# Security: create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy package files and install production deps only
COPY package*.json ./
RUN npm install --omit=dev && npm cache clean --force

# Copy source code
COPY --chown=nodejs:nodejs src/ ./src/

# Create data directory
RUN mkdir -p /app/data && chown nodejs:nodejs /app/data

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget -q --spider http://localhost:4000/api/health || exit 1

# Start application
CMD ["node", "src/index.js"]
