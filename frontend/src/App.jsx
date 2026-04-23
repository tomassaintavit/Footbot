import { useState, useEffect } from 'react'
import { supabase } from './services/supabase'
import LoginPage from './pages/LoginPage'
import ChatPage from './pages/ChatPage'

function App() {
  // "user" guarda al usuario logueado. Si es null, no hay sesión.
  const [user, setUser] = useState(null)

  // "loading" evita mostrar el Login por un flash mientras Supabase verifica la sesión
  const [loading, setLoading] = useState(true)

  // useEffect se ejecuta UNA SOLA VEZ cuando el componente se monta.
  // Es el lugar ideal para verificar si ya existe una sesión activa
  // (por ejemplo, si el usuario ya había ingresado antes y no cerró sesión).
  useEffect(() => {
    // 1. Verificamos si ya hay una sesión activa al cargar la página
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null) // Si hay sesión, guardamos el usuario. Si no, null.
      setLoading(false)              // Ya terminamos de verificar, ocultamos el spinner
    })

    // 2. Escuchamos cambios de sesión en tiempo real.
    // Esto se dispara cuando el usuario hace login O cuando hace logout.
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null)
      }
    )

    // Cleanup: cuando App se desmonta, cancelamos el listener para evitar memory leaks
    return () => subscription.unsubscribe()
  }, []) // El [] significa "ejecutar esto solo una vez al montar"

  // Mientras Supabase verifica la sesión, mostramos una pantalla de carga
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">⚽</div>
          <p className="text-slate-400 text-sm animate-pulse">Cargando...</p>
        </div>
      </div>
    )
  }

  // Si hay usuario logueado → mostramos el Chat, pasando el usuario como prop
  // Si no hay usuario → mostramos el Login, pasando onLogin para cuando el usuario se loguee
  return user
    ? <ChatPage user={user} />
    : <LoginPage onLogin={setUser} />
}

export default App
