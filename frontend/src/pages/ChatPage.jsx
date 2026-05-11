import { useState } from 'react'
import { supabase } from '../services/supabase'
import { sendChatMessage } from '../services/api'

// ChatPage recibe "user" como prop: el objeto del usuario logueado que viene de App.jsx
function ChatPage({ user }) {
    // Lista de mensajes del chat. Cada mensaje es un objeto: { role: 'user' | 'bot', text: '...' }
    const [messages, setMessages] = useState([
        { role: 'bot', text: '¡Hola! Soy Footbot. ¿En qué te puedo ayudar?' }
    ])

    // El texto que el usuario está escribiendo actualmente
    const [input, setInput] = useState('')

    // Para mostrar "..." mientras el bot está pensando
    const [isLoading, setIsLoading] = useState(false)

    // Esta función se ejecuta cuando el usuario envía un mensaje
    async function handleSend(e, textOverride = null) {
        if (e) e.preventDefault()

        const userText = textOverride || input.trim()
        if (userText === '') return

        // Limpiamos el input solo si no es un override
        if (!textOverride) setInput('')

        // Agregamos el mensaje del usuario a la lista
        setMessages(prevMessages => [...prevMessages, { role: 'user', text: userText }])

        setIsLoading(true)

        try {
            // Tomamos los últimos 10 mensajes como historial para el bot
            const history = messages.slice(-10)

            // Llamamos al backend
            const response = await sendChatMessage(userText, user.id, history)

            // Agregamos la respuesta del bot
            setMessages(prevMessages => [...prevMessages, { role: 'bot', text: response.chat }])

        } catch (err) {
            setMessages(prevMessages => [...prevMessages, { role: 'bot', text: '⚠️ Hubo un error al conectar con el servidor.' }])
            console.error(err)
        } finally {
            setIsLoading(false)
        }
    }

    // Acciones rápidas para el usuario
    const QUICK_ACTIONS = [
        { label: '¿Qué puedes hacer?', text: '¿Qué puedes hacer?' },
        { label: 'Próximo partido ⚽', text: '¿Cuándo jugamos?' },
        { label: 'Tabla de posiciones 🏆', text: 'Ver tabla de posiciones' },
        { label: 'Lista de deudas 💸', text: '¿Quién debe plata?' },
    ]

    // Esta función cierra la sesión del usuario
    async function handleLogout() {
        await supabase.auth.signOut()
    }

    return (
        <div className="min-h-screen bg-slate-900 flex flex-col">

            {/* Header */}
            <header className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">⚽</span>
                    <div>
                        <h1 className="text-white font-bold text-lg leading-none">Footbot</h1>
                        <p className="text-slate-400 text-xs">Conectado como: {user.email}</p>
                    </div>
                </div>
                <button
                    onClick={handleLogout}
                    className="text-slate-400 hover:text-white text-sm px-3 py-1 rounded-lg hover:bg-slate-700 transition-colors"
                >
                    Salir
                </button>
            </header>

            {/* Área de mensajes */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap ${msg.role === 'user'
                                ? 'bg-blue-600 text-white rounded-br-sm shadow-lg'
                                : 'bg-slate-700 text-slate-100 rounded-bl-sm shadow-md'
                                }`}
                        >
                            {msg.text}
                        </div>
                    </div>
                ))}

                {/* Indicador de "está escribiendo..." */}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-700 text-slate-400 px-4 py-2 rounded-2xl rounded-bl-sm text-sm animate-pulse">
                            Footbot está pensando...
                        </div>
                    </div>
                )}
            </div>

            {/* Sugerencias y Input */}
            <div className="bg-slate-800 border-t border-slate-700 p-4">
                {/* Quick Actions Chips */}
                <div className="flex gap-2 overflow-x-auto pb-4 no-scrollbar">
                    {QUICK_ACTIONS.map((action, index) => (
                        <button
                            key={index}
                            onClick={() => handleSend(null, action.text)}
                            disabled={isLoading}
                            className="whitespace-nowrap px-3 py-1.5 bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded-full text-slate-300 text-xs font-medium transition-colors disabled:opacity-50"
                        >
                            {action.label}
                        </button>
                    ))}
                </div>

                <form onSubmit={handleSend} className="flex gap-3">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Escribí tu mensaje..."
                        disabled={isLoading}
                        className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition-all"
                    />
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="px-5 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white rounded-xl font-semibold transition-all shadow-lg flex items-center justify-center"
                    >
                        <span className="text-xl">➤</span>
                    </button>
                </form>
            </div>
        </div>
    )
}


export default ChatPage
