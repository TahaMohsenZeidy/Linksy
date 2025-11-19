import { motion } from 'framer-motion'
import { Home, Users, Plus, Bell, Menu } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'

function Footer({ onCreatePost }) {
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { icon: Home, label: 'Home', path: '/posts' },
    { icon: Users, label: 'Friends', path: '/friends' },
    { icon: Plus, label: 'Create', path: null, action: onCreatePost },
    { icon: Bell, label: 'Notifications', path: '/notifications' },
    { icon: Menu, label: 'Profile', path: '/profile' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <motion.footer
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      className="fixed bottom-0 left-0 right-0 z-50 backdrop-blur-xl bg-white/5 border-t border-white/10"
    >
      <div className="flex items-center justify-around h-20 px-2 py-2">
        {navItems.map((item, index) => {
          const Icon = item.icon
          const active = item.path ? isActive(item.path) : false
          return (
            <motion.button
              key={item.path || `action-${index}`}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => {
                if (item.action) {
                  item.action()
                } else if (item.path) {
                  navigate(item.path)
                }
              }}
              className={`relative flex flex-col items-center justify-center gap-1.5 px-3 py-2 rounded-xl transition-all ${
                active
                  ? 'text-white'
                  : 'text-white/50 hover:text-white/80'
              }`}
            >
              {active && (
                <motion.div
                  layoutId="activeFooterTab"
                  className="absolute inset-0 bg-gradient-to-t from-purple-500/40 to-pink-500/40 rounded-xl"
                />
              )}
              <Icon className={`w-6 h-6 relative z-10 ${active ? 'scale-110' : ''}`} />
              <span className="text-xs font-medium relative z-10">{item.label}</span>
            </motion.button>
          )
        })}
      </div>
    </motion.footer>
  )
}

export default Footer

