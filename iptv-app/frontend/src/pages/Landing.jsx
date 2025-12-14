import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LockClosedIcon } from '@heroicons/react/24/outline';

export default function Landing() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="bg-gray-800/50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
          <LockClosedIcon className="h-10 w-10 text-blue-500" />
        </div>

        <h1 className="text-3xl font-bold text-white mb-4">
          Private Access
        </h1>

        <p className="text-gray-400 mb-8">
          This area is restricted to authorized users only.
        </p>

        {isAuthenticated ? (
          <Link
            to="/dashboard"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors"
          >
            Continue
          </Link>
        ) : (
          <Link
            to="/login"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors"
          >
            Sign In
          </Link>
        )}
      </div>
    </div>
  );
}
