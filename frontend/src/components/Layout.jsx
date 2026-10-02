import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import api from '../lib/api'
import { useQuery } from '@tanstack/react-query'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '🏠' },
  { to: '/levies', label: 'My Levies', icon: '📋' },
  { to: '/payments', label: 'My Payments', icon: '💳' },
  { to: '/credits', label: 'My Credits', icon: '🏦' },
  { to: '/notifications', label: 'Notifications', icon: '🔔' },
  { to: '/profile', label: 'Profile', icon: '👤' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const { data: notifData } = useQuery({
    queryKey: ['notif-count'],
    queryFn: () => api.get('/api/me/notifications/').then((r) => {
      const items = r.data.results ?? r.data
      return items.filter((n) => !n.is_read).length
    }),
    refetchInterval: 30000,
  })

  const handleLogout = async () => {
    try {
      await api.post('/api/auth/logout/', {
        refresh: localStorage.getItem('refresh_token'),
      })
    } catch {}
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="hidden md:flex flex-col w-60 bg-blue-950 text-white shrink-0">
        <div className="px-6 py-6 border-b border-blue-900">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center font-bold text-sm">
              P
            </div>
            <div>
              <p className="font-bold text-sm leading-none">Peace CDA</p>
              <p className="text-blue-400 text-xs mt-0.5">Member Portal</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-700 text-white'
                    : 'text-blue-200 hover:bg-blue-900 hover:text-white'
                }`
              }
            >
              <span className="text-base">{icon}</span>
              <span>{label}</span>
              {label === 'Notifications' && notifData > 0 && (
                <span className="ml-auto bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                  {notifData}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="px-6 py-4 border-t border-blue-900">
          <p className="text-xs text-blue-400 mb-1">Signed in as</p>
          <p className="text-sm font-semibold text-white truncate">{user?.full_name || user?.username}</p>
          <button
            onClick={handleLogout}
            className="mt-3 text-xs text-blue-400 hover:text-white transition-colors"
          >
            Sign out →
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile top bar */}
        <header className="md:hidden bg-blue-950 text-white px-4 py-3 flex items-center justify-between">
          <p className="font-bold text-sm">Peace CDA</p>
          <button onClick={handleLogout} className="text-xs text-blue-300">Sign out</button>
        </header>

        {/* Mobile nav */}
        <nav className="md:hidden flex overflow-x-auto bg-blue-900 px-2 py-1 gap-1">
          {navItems.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex flex-col items-center px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 transition-colors ${
                  isActive ? 'bg-blue-700 text-white' : 'text-blue-300 hover:text-white'
                }`
              }
            >
              <span>{icon}</span>
              <span>{label.split(' ')[0]}</span>
            </NavLink>
          ))}
        </nav>

        <main className="flex-1 p-6 max-w-4xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
