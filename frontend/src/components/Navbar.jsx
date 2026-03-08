// frontend/src/components/Navbar.jsx
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'

export default function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()

  // Use state so navbar re-renders when user changes
  const [user, setUser] = useState(
    JSON.parse(localStorage.getItem('user') || 'null')
  )

  // Re-read user from localStorage every time the route changes
  useEffect(() => {
    const readUser = () => {
      const stored = JSON.parse(localStorage.getItem('user') || 'null')
      setUser(stored)
    }

    readUser() // run on route change
    window.addEventListener('storage', readUser) // run on login/logout

    return () => window.removeEventListener('storage', readUser)
  }, [location.pathname])

  const isAdmin   = user?.role === 'admin'
  const isAuthPage = location.pathname === '/login' ||
                     location.pathname === '/register'

  function logout() {
    localStorage.clear()
    setUser(null)
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="container">
        <Link to="/" className="navbar-brand">
          ⛽ Gas<span>Predictor</span>
        </Link>

        <div className="navbar-links">
          {isAuthPage ? (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register" className="btn-nav-active">Register</Link>
            </>
          ) : user ? (
            <>
              {isAdmin && (
                <Link to="/station">📊 Station Dashboard</Link>
              )}
              {!isAdmin && (
                <Link to="/household">🏠 My Gas</Link>
              )}
              <span style={{
                color: '#94a3b8', fontSize: '0.85rem',
                display: 'flex', alignItems: 'center', gap: 6
              }}>
                {isAdmin ? '🔑' : '👤'} {user.name}
                {isAdmin && (
                  <span style={{
                    background: '#2563eb', color: 'white',
                    fontSize: '0.7rem', padding: '1px 7px',
                    borderRadius: 20, fontWeight: 700,
                  }}>
                    ADMIN
                  </span>
                )}
              </span>
              <button onClick={logout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register" className="btn-nav-active">Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}