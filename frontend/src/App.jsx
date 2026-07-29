import { useState, useEffect } from 'react'
import { supabase } from './services/supabase'
import { getMe } from './services/api'
import PublicLanding from './components/PublicLanding'
import LoginForm from './components/LoginForm'
import AdminDashboard from './components/AdminDashboard'

function App() {
  const [session, setSession] = useState(null)
  const [view, setView] = useState('public')
  const [adminPlayer, setAdminPlayer] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) setSession(session)
      setLoading(false)
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      if (!session) {
        setAdminPlayer(null)
        if (view === 'admin') setView('public')
      }
    })
    return () => subscription.unsubscribe()
  }, [])

  async function handleAdminClick() {
    if (session) {
      try {
        const player = await getMe(session.access_token)
        setAdminPlayer(player)
        setView('admin')
      } catch {
        await supabase.auth.signOut()
        setSession(null)
        setView('login')
      }
    } else {
      setView('login')
    }
  }

  async function handleLogin(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw new Error('Email o contraseña incorrectos')
    setSession(data.session)
    try {
      const player = await getMe(data.session.access_token)
      setAdminPlayer(player)
      setView('admin')
    } catch {
      await supabase.auth.signOut()
      setSession(null)
      throw new Error('No tienes permisos de administrador')
    }
  }

  async function handleLogout() {
    await supabase.auth.signOut()
    setSession(null)
    setAdminPlayer(null)
    setView('public')
  }

  function goToLanding() {
    setView('public')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-black to-[#712005] flex items-center justify-center">
        <p className="text-white/40 animate-pulse text-sm">Cargando...</p>
      </div>
    )
  }

  if (view === 'login') {
    return <LoginForm onLogin={handleLogin} onBack={() => setView('public')} />
  }

  if (view === 'admin' && adminPlayer) {
    return <AdminDashboard adminPlayer={adminPlayer} session={session} onLogout={handleLogout} onBack={goToLanding} />
  }

  return <PublicLanding onAdminClick={handleAdminClick} />
}

export default App
