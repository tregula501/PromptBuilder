import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import mpegts from 'mpegts.js';
import api from '../services/api';
import {
  ArrowLeftIcon,
  StarIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  ShieldExclamationIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

const MAX_RETRIES = 5;
const RETRY_DELAYS = [3000, 6000, 10000, 15000, 20000]; // Longer delays for rate limiting

// Parse error to determine type
const getErrorInfo = (errorCode, errorDetail) => {
  const detail = String(errorDetail || '').toLowerCase();

  // 404 - Stream not found (don't retry)
  if (errorCode === 404 || detail.includes('404') || detail.includes('not found')) {
    return {
      type: 'not_found',
      title: 'Stream Not Available',
      message: 'This stream is no longer available. The event may have ended or the channel is offline.',
      icon: 'error',
      shouldRetry: false
    };
  }

  // 429 - Rate limited (retry with delays)
  if (errorCode === 429 || detail.includes('429') || detail.includes('rate limit') || detail.includes('too many')) {
    return {
      type: 'rate_limited',
      title: 'Rate Limited',
      message: 'Too many requests to the stream provider. Retrying automatically...',
      icon: 'clock',
      shouldRetry: true
    };
  }

  // 403 - Forbidden (don't retry)
  if (errorCode === 403 || detail.includes('403') || detail.includes('forbidden') || detail.includes('access denied')) {
    return {
      type: 'forbidden',
      title: 'Access Denied',
      message: 'The stream provider is blocking access. Try a different VPN region.',
      icon: 'error',
      shouldRetry: false
    };
  }

  // 502 - Bad Gateway (retry - could be temporary)
  if (errorCode === 502 || detail.includes('502') || detail.includes('bad gateway')) {
    return {
      type: 'unavailable',
      title: 'Stream Temporarily Unavailable',
      message: 'The stream is temporarily unavailable. Retrying automatically...',
      icon: 'clock',
      shouldRetry: true
    };
  }

  // Network errors (retry)
  if (detail.includes('network') || detail.includes('timeout') || detail.includes('connection')) {
    return {
      type: 'network',
      title: 'Network Error',
      message: 'Connection issue. Retrying automatically...',
      icon: 'clock',
      shouldRetry: true
    };
  }

  // Unknown errors (retry a few times)
  return {
    type: 'unknown',
    title: 'Stream Error',
    message: errorDetail || 'An unexpected error occurred.',
    icon: 'error',
    shouldRetry: true
  };
};

export default function Watch() {
  const { channelId } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const playerRef = useRef(null);

  const [channel, setChannel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [errorInfo, setErrorInfo] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCountdown, setRetryCountdown] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [playerSupported, setPlayerSupported] = useState(true);
  const [vpnStatus, setVpnStatus] = useState({ connected: false, ip: null, location: null });

  // Check if mpegts.js is supported
  useEffect(() => {
    if (!mpegts.isSupported()) {
      setPlayerSupported(false);
      setError('Your browser does not support MPEG-TS playback. Please use Chrome or Firefox.');
    }
  }, []);

  // Fetch VPN status
  useEffect(() => {
    api.get('/health/vpn')
      .then(res => {
        setVpnStatus({
          connected: res.data.connected,
          ip: res.data.ip,
          location: res.data.location
        });
      })
      .catch(() => {
        setVpnStatus({ connected: false, ip: null, location: null });
      });
  }, []);

  // Fetch channel info
  useEffect(() => {
    api.get(`/channels/${channelId}`)
      .then(res => {
        setChannel(res.data.channel);
        setLoading(false);
      })
      .catch(err => {
        setError('Channel not found');
        setLoading(false);
      });

    // Check favorite status
    api.get(`/favorites/${channelId}/check`)
      .then(res => setIsFavorite(res.data.isFavorite))
      .catch(() => {});
  }, [channelId]);

  // Initialize mpegts.js player
  const initPlayer = useCallback(() => {
    if (!videoRef.current || !channel || !playerSupported) return;

    // Dispose existing player
    if (playerRef.current) {
      playerRef.current.destroy();
      playerRef.current = null;
    }

    // Use absolute URL for web worker compatibility
    const streamUrl = `${window.location.origin}/api/stream/${channelId}`;

    try {
      playerRef.current = mpegts.createPlayer({
        type: 'mpegts',
        isLive: true,
        url: streamUrl,
      }, {
        enableWorker: false,
        enableStashBuffer: true,
        stashInitialSize: 1024 * 1024, // 1MB initial buffer
        autoCleanupSourceBuffer: true,
        autoCleanupMaxBackwardDuration: 60,
        autoCleanupMinBackwardDuration: 30,
        liveBufferLatencyChasing: false, // Disable latency chasing for smoother playback
        liveBufferLatencyMaxLatency: 10.0, // Allow more buffer
        liveBufferLatencyMinRemain: 3.0, // Keep more buffer
        lazyLoad: false,
        lazyLoadMaxDuration: 300,
        deferLoadAfterSourceOpen: false,
        fixAudioTimestampGap: true,
      });

      playerRef.current.attachMediaElement(videoRef.current);
      playerRef.current.load();
      playerRef.current.play();

      // Handle errors with auto-retry
      playerRef.current.on(mpegts.Events.ERROR, (errorType, errorDetail, errorInfoData) => {
        console.error('Player error:', errorType, errorDetail, errorInfoData);

        // Parse error code from errorInfo or error detail string
        const errorCode = errorInfoData?.code ||
          (errorDetail?.includes('404') ? 404 :
           errorDetail?.includes('429') ? 429 :
           errorDetail?.includes('403') ? 403 :
           errorDetail?.includes('502') ? 502 : null);

        const info = getErrorInfo(errorCode, errorDetail);
        setErrorInfo(info);

        // Only retry if the error type allows it and we haven't exceeded max retries
        if (info.shouldRetry && retryCount < MAX_RETRIES) {
          setIsRetrying(true);
          const delay = RETRY_DELAYS[retryCount];
          const delaySeconds = Math.ceil(delay / 1000);

          // Start countdown
          setRetryCountdown(delaySeconds);
          const countdownInterval = setInterval(() => {
            setRetryCountdown(prev => {
              if (prev <= 1) {
                clearInterval(countdownInterval);
                return 0;
              }
              return prev - 1;
            });
          }, 1000);

          setTimeout(() => {
            clearInterval(countdownInterval);
            setRetryCount(prev => prev + 1);
            setIsRetrying(false);
            setRetryCountdown(0);
            initPlayer();
          }, delay);
        } else {
          // Don't retry - show final error
          setError(info.message);
          setIsRetrying(false);
        }
      });

      // Handle loading errors
      playerRef.current.on(mpegts.Events.LOADING_COMPLETE, () => {
        console.log('Loading complete - stream may have ended');
      });

      // Reset retry count on successful media info
      playerRef.current.on(mpegts.Events.MEDIA_INFO, (mediaInfo) => {
        console.log('Media info received:', mediaInfo);
        console.log('Video codec:', mediaInfo.videoCodec);
        console.log('Audio codec:', mediaInfo.audioCodec);
        console.log('Video element dimensions:', videoRef.current?.videoWidth, 'x', videoRef.current?.videoHeight);
        setRetryCount(0);
        setError(null);
      });

      // Debug: Log statistics periodically
      playerRef.current.on(mpegts.Events.STATISTICS_INFO, (stats) => {
        if (stats.decodedFrames && stats.decodedFrames % 100 === 0) {
          console.log('Stats - Decoded frames:', stats.decodedFrames, 'Dropped:', stats.droppedFrames);
        }
      });

      // Debug: Check video element state after a delay
      setTimeout(() => {
        const video = videoRef.current;
        if (video) {
          console.log('Video state check:');
          console.log('- readyState:', video.readyState);
          console.log('- paused:', video.paused);
          console.log('- videoWidth:', video.videoWidth);
          console.log('- videoHeight:', video.videoHeight);
          console.log('- currentTime:', video.currentTime);
          console.log('- buffered:', video.buffered.length > 0 ? `${video.buffered.start(0)} - ${video.buffered.end(0)}` : 'none');
        }
      }, 3000);

    } catch (err) {
      console.error('Failed to create player:', err);
      setError('Failed to initialize video player');
    }

  }, [channel, channelId, retryCount, playerSupported]);

  useEffect(() => {
    if (channel && playerSupported) {
      initPlayer();
    }

    return () => {
      if (playerRef.current) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
    };
  }, [channel, initPlayer, playerSupported]);

  const handleManualRetry = () => {
    setError(null);
    setErrorInfo(null);
    setRetryCount(0);
    initPlayer();
  };

  const toggleFavorite = async () => {
    try {
      if (isFavorite) {
        await api.delete(`/favorites/${channelId}`);
        setIsFavorite(false);
      } else {
        await api.post(`/favorites/${channelId}`);
        setIsFavorite(true);
      }
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!channel) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Channel Not Found</h2>
          <p className="text-gray-400 mb-4">The channel you're looking for doesn't exist.</p>
          <Link
            to="/dashboard"
            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center">
            <button
              onClick={() => navigate(-1)}
              className="text-gray-400 hover:text-white mr-4"
            >
              <ArrowLeftIcon className="h-6 w-6" />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-white">{channel.name}</h1>
              <p className="text-sm text-gray-400">{channel.category}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* VPN Status Indicator */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium ${
                vpnStatus.connected
                  ? 'bg-green-900/50 text-green-400 border border-green-700'
                  : 'bg-red-900/50 text-red-400 border border-red-700'
              }`}
              title={vpnStatus.connected ? `VPN: ${vpnStatus.ip} (${vpnStatus.location})` : 'VPN Disconnected'}
            >
              {vpnStatus.connected ? (
                <ShieldCheckIcon className="h-4 w-4" />
              ) : (
                <ShieldExclamationIcon className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">
                {vpnStatus.connected ? vpnStatus.location || 'VPN' : 'No VPN'}
              </span>
            </div>

            <button
              onClick={toggleFavorite}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              {isFavorite ? (
                <StarIconSolid className="h-6 w-6 text-yellow-500" />
              ) : (
                <StarIcon className="h-6 w-6 text-gray-400 hover:text-yellow-500" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Video Player */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="video-container bg-black rounded-lg overflow-hidden relative" style={{ aspectRatio: '16/9', minHeight: '360px' }}>
          {/* Video element */}
          <video
            ref={videoRef}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              backgroundColor: '#000'
            }}
            controls
            autoPlay
            muted={false}
            playsInline
          />

          {/* Retry overlay */}
          {isRetrying && (
            <div className="absolute inset-0 bg-black/80 flex items-center justify-center z-10">
              <div className="text-center max-w-md px-4">
                {errorInfo?.type === 'rate_limited' ? (
                  <ClockIcon className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
                ) : (
                  <div className="spinner mx-auto mb-4"></div>
                )}
                <h3 className="text-xl font-semibold text-white mb-2">
                  {errorInfo?.title || 'Connecting...'}
                </h3>
                <p className="text-gray-400 mb-4">
                  {errorInfo?.message || 'Attempting to connect to stream...'}
                </p>
                <div className="flex items-center justify-center gap-2 text-gray-300">
                  <ArrowPathIcon className="h-5 w-5 animate-spin" />
                  <span>
                    Retry {retryCount + 1} of {MAX_RETRIES}
                    {retryCountdown > 0 && ` in ${retryCountdown}s`}
                  </span>
                </div>
                {errorInfo?.type === 'rate_limited' && (
                  <p className="text-xs text-gray-500 mt-3">
                    Rate limiting usually clears after 1-2 minutes
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Error overlay */}
          {error && !isRetrying && (
            <div className="absolute inset-0 bg-black/80 flex items-center justify-center z-10">
              <div className="text-center max-w-md px-4">
                {errorInfo?.type === 'rate_limited' ? (
                  <ClockIcon className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
                ) : (
                  <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
                )}
                <h3 className="text-xl font-semibold text-white mb-2">
                  {errorInfo?.title || 'Stream Error'}
                </h3>
                <p className="text-gray-400 mb-4">{error}</p>
                {errorInfo?.type === 'rate_limited' && (
                  <p className="text-sm text-yellow-500 mb-4">
                    Wait a moment before retrying to avoid further rate limiting.
                  </p>
                )}
                {errorInfo?.type === 'forbidden' && (
                  <p className="text-sm text-yellow-500 mb-4">
                    Try changing VPN region in settings and restart.
                  </p>
                )}
                <button
                  onClick={handleManualRetry}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                >
                  <ArrowPathIcon className="h-5 w-5 mr-2" />
                  Try Again
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Channel info */}
        <div className="mt-6 bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-4">
            {channel.logo && (
              <img
                src={channel.logo}
                alt={channel.name}
                className="w-16 h-16 object-contain bg-gray-700 rounded-lg p-2"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            )}
            <div>
              <h2 className="text-xl font-semibold text-white">{channel.name}</h2>
              <p className="text-gray-400">{channel.category}</p>
              {channel.health && (
                <p className={`text-sm ${channel.health.status === 'online' ? 'text-green-500' : 'text-red-500'}`}>
                  Status: {channel.health.status}
                  {channel.health.latency && ` (${channel.health.latency}ms)`}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
