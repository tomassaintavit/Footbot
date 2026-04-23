const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// history: array de los últimos mensajes para dar memoria al bot
// Ej: [{ role: 'user', text: '...' }, { role: 'bot', text: '...' }]
export async function sendChatMessage(prompt, auth_id, history = [], model = "llama3") {
    const response = await fetch(`${API_URL}/chat/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt, auth_id, model, history })
    });

    if (!response.ok) {
        const error = await response.json();
        console.error("Error en la API:", error);
        throw new Error(error.detail || "Error en la petición a la API");
    }

    return response.json();
}