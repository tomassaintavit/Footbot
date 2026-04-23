function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-800 p-8 rounded-2xl shadow-2xl border border-slate-700">
        <h1 className="text-3xl font-bold text-center mb-4 bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Footbot Assistant
        </h1>
        <p className="text-slate-400 text-center mb-6">
          Backend conectado y listo para recibir órdenes.
        </p>
        <button className="w-full py-3 bg-blue-600 hover:bg-blue-500 transition-colors rounded-lg font-semibold">
          Comenzar Chat
        </button>
      </div>
    </div>
  )
}

export default App

