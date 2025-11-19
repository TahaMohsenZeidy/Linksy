import { motion } from 'framer-motion'
import { Home, Users, Video, Bell, Menu, LogOut } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuth()

  const navItems = [
    { icon: Home, label: 'Home', path: '/posts', color: 'from-blue-400 to-cyan-400' },
    { icon: Users, label: 'Friends', path: '/friends', color: 'from-yellow-400 to-orange-400' },
    { icon: Video, label: 'Reels', path: '/reels', color: 'from-pink-400 to-red-400' },
    { icon: Bell, label: 'Notifications', path: '/notifications', color: 'from-purple-400 to-pink-400' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-white/5 border-b border-white/10"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top Row: Logo, Navigation Icons, Menu/Logout */}
        <div className="flex items-center justify-between h-14 py-2">
          {/* Logo */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/posts')}
            className="flex items-center gap-2 cursor-pointer"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 via-pink-400 to-orange-400 flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">L</span>
            </div>
            <span className="text-white font-bold text-xl hidden sm:block">Linksy</span>
          </motion.div>

          {/* Navigation Items - Always visible */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = isActive(item.path)
              return (
                <motion.button
                  key={item.path}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => navigate(item.path)}
                  className={`relative p-2.5 rounded-xl transition-all ${
                    active
                      ? `bg-gradient-to-r ${item.color} text-white shadow-lg`
                      : 'text-white/60 hover:text-white hover:bg-white/10'
                  }`}
                >
                  <Icon className="w-5 h-5 relative z-10" />
                </motion.button>
              )
            })}
          </div>

          {/* Right Side - Menu & Logout */}
          <div className="flex items-center gap-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/profile')}
              className="p-2 glass rounded-xl text-white/60 hover:text-white hover:bg-white/10 transition-all"
              title="Profile"
            >
              <Menu className="w-5 h-5" />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={logout}
              className="p-2 glass rounded-xl text-white/60 hover:text-red-400 hover:bg-red-500/10 transition-all"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </motion.button>
          </div>
        </div>
      </div>
    </motion.nav>
  )
}

export default Navbar

