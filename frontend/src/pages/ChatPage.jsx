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
    async function handleSend(e) {
        e.preventDefault()

        // TODO: Validar que "input" no esté vacío antes de continuar.
        // Tip: usa un "if" para verificar que input.trim() no sea ''.
        // Si está vacío, simplemente haz un "return" para salir de la función.
        if (input.trim() == '') {
            return
        }

        // Guardamos el texto y limpiamos el input inmediatamente
        const userText = input.trim()
        setInput('')

        // TODO: Agregar el mensaje del usuario a la lista "messages".
        // Tip: usa setMessages con la función de actualización de estado.
        // El nuevo mensaje debe tener esta forma: { role: 'user', text: userText }
        // Recuerda usar el spread operator (...prevMessages) para no perder los mensajes anteriores.
        setMessages(prevMessages => [...prevMessages, { role: 'user', text: userText }])

        setIsLoading(true)

        try {
            // Tomamos los últimos 10 mensajes como historial para el bot
            // (los mensajes ya incluyen el que acabamos de agregar)
            const history = messages.slice(-10)

            // Llamamos al backend con el mensaje y el historial
            const response = await sendChatMessage(userText, user.id, history)

            // TODO: Agregar la respuesta del bot a la lista "messages".
            // Tip: el texto de la respuesta viene en response.chat
            // El nuevo mensaje debe tener esta forma: { role: 'bot', text: response.chat }
            setMessages(prevMessages => [...prevMessages, { role: 'bot', text: response.chat }])

        } catch (err) {
            // TODO: Si hay un error, agregar un mensaje de error a la lista.
            // Tip: { role: 'bot', text: '⚠️ Hubo un error al conectar con el servidor.' }
            setMessages(prevMessages => [...prevMessages, { role: 'bot', text: '⚠️ Hubo un error al conectar con el servidor.' }])
            console.error(err)
        } finally {
            setIsLoading(false)
        }
    }

    // Esta función cierra la sesión del usuario
    async function handleLogout() {
        await supabase.auth.signOut()
        // App.jsx detectará el cambio de sesión automáticamente y volverá al Login
    }

    return (
        <div className="min-h-screen bg-slate-900 flex flex-col">

            {/* Header */}
            <header className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">⚽</span>
                    <div>
                        <h1 className="text-white font-bold text-lg leading-none">Footbot</h1>
                        {/* TODO: Mostrar el email del usuario logueado aquí. */}
                        {/* Tip: el email está en user.email */}
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
                    // TODO: Acá usamos el componente <ChatMessage> que crearemos después.
                    // Por ahora, mostramos los mensajes con un div simple.

                    <div
                        key={index}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl text-sm ${msg.role === 'user'
                                ? 'bg-blue-600 text-white rounded-br-sm'
                                : 'bg-slate-700 text-slate-100 rounded-bl-sm'
                                }`}
                        >
                            {msg.text}
                        </div>
                    </div>
                ))}

                {/* Indicador de "está escribiendo..." */}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-700 text-slate-400 px-4 py-2 rounded-2xl rounded-bl-sm text-sm">
                            Footbot está pensando...
                        </div>
                    </div>
                )}
            </div>

            {/* Input de mensaje */}
            <div className="bg-slate-800 border-t border-slate-700 p-4">
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
                        className="px-5 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white rounded-xl font-semibold transition-all"
                    >
                        {/* TODO: cambiar el texto del botón por un ícono de avión de papel: ➤ */}
                        <span className="text-2xl">➤</span>
                    </button>
                </form>
            </div>
        </div>
    )
}

export default ChatPage
