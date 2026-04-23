import { useState } from 'react'
import { supabase } from '../services/supabase'

// LoginPage recibe "onLogin" como prop: una función que se llama
// cuando el usuario se loguea con éxito. La usaremos en App.jsx.
function LoginPage({ onLogin }) {
  // useState guarda el valor del input mientras el usuario escribe.
  // "email" es el valor actual, "setEmail" es la función para cambiarlo.
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  // Estado para mostrar errores o mensajes de carga
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  // Esta función se ejecuta cuando el usuario hace click en "Iniciar sesión"
  async function handleLogin(e) {
    // Evita que el formulario recargue la página (comportamiento default de HTML)
    e.preventDefault()

    setLoading(true) // Mostramos el spinner
    setError(null)   // Limpiamos errores anteriores

    // Le pedimos a Supabase que compruebe email y contraseña
    const { data, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    setLoading(false)

    if (authError) {
      // Si Supabase devuelve un error, lo mostramos en pantalla
      setError('Email o contraseña incorrectos. Intenta de nuevo.')
      return
    }

    // Si todo salió bien, llamamos a onLogin pasando el usuario
    // Esto le avisará a App.jsx que ya puede mostrar el Chat
    onLogin(data.user)
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      {/* Tarjeta central de login */}
      <div className="w-full max-w-md bg-slate-800 rounded-2xl shadow-2xl border border-slate-700 p-8">

        {/* Logo / Título */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">⚽</div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Footbot
          </h1>
          <p className="text-slate-400 mt-2 text-sm">
            Ingresá con tu cuenta del equipo
          </p>
        </div>

        {/* Formulario de login */}
        {/* onSubmit llama a handleLogin cuando el usuario presiona Enter o el botón */}
        <form onSubmit={handleLogin} className="space-y-4">

          {/* Campo Email */}
          <div>
            <label htmlFor="email" className="block text-sm text-slate-400 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              // onChange actualiza el estado "email" cada vez que el usuario escribe
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu@email.com"
              required
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          {/* Campo Contraseña */}
          <div>
            <label htmlFor="password" className="block text-sm text-slate-400 mb-1">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          {/* Mensaje de error (solo se muestra si "error" no es null) */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3">
              <p className="text-red-400 text-sm text-center">{error}</p>
            </div>
          )}

          {/* Botón de submit - se deshabilita mientras carga */}
          <button
            id="login-btn"
            type="submit"
            disabled={loading}
            className="w-full py-3 mt-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {loading ? 'Ingresando...' : 'Iniciar sesión'}
          </button>
        </form>

        {/* Footer */}
        <p className="text-center text-slate-500 text-xs mt-6">
          ¿No tenés cuenta? Pedile al admin que te la cree.
        </p>
      </div>
    </div>
  )
}

export default LoginPage
