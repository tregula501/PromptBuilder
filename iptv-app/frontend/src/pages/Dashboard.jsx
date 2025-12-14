import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  MagnifyingGlassIcon,
  Bars3Icon,
  XMarkIcon,
  StarIcon,
  TvIcon,
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon,
  UserCircleIcon,
  PlayIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

export default function Dashboard() {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const [channels, setChannels] = useState([]);
  const [categories, setCategories] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [favoriteIds, setFavoriteIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showFavorites, setShowFavorites] = useState(false);
  const [onlineOnly, setOnlineOnly] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, totalPages: 1 });

  // Fetch categories
  useEffect(() => {
    api.get('/channels/categories')
      .then(res => setCategories(res.data.categories))
      .catch(console.error);
  }, []);

  // Fetch favorites
  useEffect(() => {
    api.get('/favorites')
      .then(res => {
        setFavorites(res.data.favorites);
        setFavoriteIds(new Set(res.data.favorites.map(f => f.id)));
      })
      .catch(console.error);
  }, []);

  // Fetch channels
  const fetchChannels = useCallback(async () => {
    setLoading(true);
    try {
      let url = '/channels';
      const params = new URLSearchParams();

      if (searchQuery) {
        url = '/channels/search';
        params.append('q', searchQuery);
      } else if (selectedCategory) {
        url = `/channels/category/${encodeURIComponent(selectedCategory)}`;
      }

      params.append('page', pagination.page);
      params.append('limit', 48);

      if (onlineOnly) {
        params.append('online', 'true');
      }

      const response = await api.get(`${url}?${params}`);
      setChannels(response.data.data);
      setPagination(response.data.pagination);
    } catch (error) {
      console.error('Failed to fetch channels:', error);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedCategory, pagination.page, onlineOnly]);

  useEffect(() => {
    if (!showFavorites) {
      fetchChannels();
    }
  }, [fetchChannels, showFavorites]);

  // Handle search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setPagination(p => ({ ...p, page: 1 }));
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    setShowFavorites(false);
    setSearchQuery('');
    setPagination(p => ({ ...p, page: 1 }));
    setSidebarOpen(false);
  };

  const handleShowFavorites = () => {
    setShowFavorites(true);
    setSelectedCategory(null);
    setSearchQuery('');
    setSidebarOpen(false);
  };

  const toggleFavorite = async (channelId) => {
    try {
      if (favoriteIds.has(channelId)) {
        await api.delete(`/favorites/${channelId}`);
        setFavoriteIds(prev => {
          const next = new Set(prev);
          next.delete(channelId);
          return next;
        });
        setFavorites(prev => prev.filter(f => f.id !== channelId));
      } else {
        await api.post(`/favorites/${channelId}`);
        setFavoriteIds(prev => new Set([...prev, channelId]));
        // Refresh favorites list
        const res = await api.get('/favorites');
        setFavorites(res.data.favorites);
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const displayChannels = showFavorites ? favorites : channels;

  return (
    <div className="min-h-screen bg-gray-900 flex">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-800 transform transition-transform duration-300 lg:translate-x-0 lg:static ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center justify-between">
              <Link to="/" className="flex items-center space-x-2">
                <TvIcon className="h-8 w-8 text-blue-500" />
                <span className="text-xl font-bold text-white">IPTV</span>
              </Link>
              <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-gray-400 hover:text-white">
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-1">
            {/* Favorites */}
            <button
              onClick={handleShowFavorites}
              className={`w-full flex items-center px-3 py-2 text-sm rounded-lg ${showFavorites ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
            >
              <StarIconSolid className="h-5 w-5 mr-3 text-yellow-500" />
              My Favorites
              {favorites.length > 0 && (
                <span className="ml-auto bg-gray-600 px-2 py-0.5 rounded-full text-xs">
                  {favorites.length}
                </span>
              )}
            </button>

            {/* All Channels */}
            <button
              onClick={() => handleCategorySelect(null)}
              className={`w-full flex items-center px-3 py-2 text-sm rounded-lg ${!selectedCategory && !showFavorites ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
            >
              <TvIcon className="h-5 w-5 mr-3" />
              All Channels
            </button>

            {/* Online Only Toggle */}
            <button
              onClick={() => {
                setOnlineOnly(!onlineOnly);
                setPagination(p => ({ ...p, page: 1 }));
              }}
              className={`w-full flex items-center px-3 py-2 text-sm rounded-lg ${onlineOnly ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
            >
              <span className={`w-5 h-5 mr-3 flex items-center justify-center rounded-full ${onlineOnly ? 'bg-green-400' : 'bg-gray-600'}`}>
                <span className={`w-2 h-2 rounded-full ${onlineOnly ? 'bg-white' : 'bg-gray-400'}`} />
              </span>
              Online Only
            </button>

            {/* Categories */}
            <div className="pt-4">
              <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Categories
              </h3>
              {categories.map((cat) => (
                <button
                  key={cat.name}
                  onClick={() => handleCategorySelect(cat.name)}
                  className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded-lg ${selectedCategory === cat.name ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
                >
                  <span className="truncate">{cat.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${selectedCategory === cat.name ? 'bg-blue-500' : 'bg-gray-700'}`}>
                    {selectedCategory === cat.name && cat.onlineCount !== undefined
                      ? `${cat.onlineCount} online`
                      : cat.count}
                  </span>
                </button>
              ))}
            </div>
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-gray-700">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium">
                {user?.username?.[0]?.toUpperCase()}
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-white">{user?.username}</p>
                <p className="text-xs text-gray-400">{user?.role}</p>
              </div>
            </div>
            <div className="space-y-1">
              <Link
                to="/profile"
                className="flex items-center px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded-lg"
              >
                <UserCircleIcon className="h-5 w-5 mr-3" />
                Profile
              </Link>
              {isAdmin && (
                <Link
                  to="/admin"
                  className="flex items-center px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded-lg"
                >
                  <Cog6ToothIcon className="h-5 w-5 mr-3" />
                  Admin Panel
                </Link>
              )}
              <button
                onClick={handleLogout}
                className="w-full flex items-center px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded-lg"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5 mr-3" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0">
        {/* Header */}
        <header className="sticky top-0 z-40 bg-gray-900/95 backdrop-blur border-b border-gray-800 px-4 py-3">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-gray-400 hover:text-white"
            >
              <Bars3Icon className="h-6 w-6" />
            </button>

            {/* Search */}
            <div className="flex-1 max-w-xl relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search channels..."
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </header>

        {/* Channel grid */}
        <div className="p-4">
          {/* Title */}
          <h2 className="text-xl font-semibold text-white mb-4">
            {showFavorites ? 'My Favorites' : selectedCategory || 'All Channels'}
            {!loading && (
              <span className="text-gray-500 font-normal ml-2">
                ({displayChannels.length} {displayChannels.length === 1 ? 'channel' : 'channels'})
              </span>
            )}
          </h2>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="spinner"></div>
            </div>
          ) : displayChannels.length === 0 ? (
            <div className="text-center py-20 text-gray-400">
              {showFavorites ? 'No favorites yet. Star some channels!' : 'No channels found.'}
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                {displayChannels.map((channel) => (
                  <div
                    key={channel.id}
                    className="channel-card bg-gray-800 rounded-lg overflow-hidden group"
                  >
                    <Link to={`/watch/${channel.id}`} className="block">
                      <div className="aspect-video bg-gray-700 relative overflow-hidden">
                        {channel.logo ? (
                          <img
                            src={channel.logo}
                            alt={channel.name}
                            className="w-full h-full object-contain p-2"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <TvIcon className="h-12 w-12 text-gray-600" />
                          </div>
                        )}
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <PlayIcon className="h-12 w-12 text-white" />
                        </div>
                        {channel.health?.status && (
                          <span className={`absolute top-2 right-2 w-2 h-2 rounded-full ${channel.health.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
                        )}
                      </div>
                    </Link>
                    <div className="p-3">
                      <div className="flex items-start justify-between gap-2">
                        <Link to={`/watch/${channel.id}`} className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-white truncate hover:text-blue-400">
                            {channel.name}
                          </h3>
                          <p className="text-xs text-gray-500 truncate">{channel.category}</p>
                        </Link>
                        <button
                          onClick={() => toggleFavorite(channel.id)}
                          className="flex-shrink-0 p-1 hover:bg-gray-700 rounded"
                        >
                          {favoriteIds.has(channel.id) ? (
                            <StarIconSolid className="h-5 w-5 text-yellow-500" />
                          ) : (
                            <StarIcon className="h-5 w-5 text-gray-500 hover:text-yellow-500" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {!showFavorites && pagination.totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-8">
                  <button
                    onClick={() => setPagination(p => ({ ...p, page: p.page - 1 }))}
                    disabled={!pagination.hasPrev}
                    className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700"
                  >
                    Previous
                  </button>
                  <span className="text-gray-400 px-4">
                    Page {pagination.page} of {pagination.totalPages}
                  </span>
                  <button
                    onClick={() => setPagination(p => ({ ...p, page: p.page + 1 }))}
                    disabled={!pagination.hasNext}
                    className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
