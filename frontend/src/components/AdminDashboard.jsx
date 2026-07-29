import { useState, useEffect } from 'react'
import { getDebtsSummary } from '../services/api'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

function formatCurrency(n) {
  return '$' + Math.round(n).toLocaleString('es-AR')
}

export default function AdminDashboard({ adminPlayer, session, onLogout, onBack }) {
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getDebtsSummary(session.access_token)
      .then(setSummary)
      .catch(() => setError('Error al cargar datos'))
  }, [])

  const pieData = summary ? [
    { name: 'Impago', value: summary.total_debt, color: '#DC2626' },
    { name: 'Pagado', value: summary.total_paid, color: 'rgba(255,255,255,0.2)' },
  ].filter(d => d.value > 0) : []

  const hasDebts = summary && (summary.total_debt > 0 || summary.total_paid > 0)

  return (
    <div className="min-h-screen bg-gradient-to-b from-black to-[#712005] text-white">
      <div className="max-w-4xl mx-auto px-4 py-6">

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button onClick={onBack} className="text-white/50 hover:text-white text-sm transition-colors">← Inicio</button>
            <div>
              <h1 className="text-lg font-bold">💰 Administración</h1>
              <p className="text-white/50 text-xs">{adminPlayer.name}</p>
            </div>
          </div>
          <button onClick={onLogout} className="text-sm text-white/50 hover:text-white border border-white/20 hover:border-white/40 px-3 py-1.5 rounded-lg transition-colors">
            Salir
          </button>
        </div>

        {error ? (
          <p className="text-red-400 text-sm">{error}</p>
        ) : summary ? (
          <>
            <div className="grid grid-cols-2 gap-3 mb-6">
              <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                <p className="text-white/50 text-xs uppercase tracking-wide">Deuda Total</p>
                <p className="text-2xl font-bold text-red-400 mt-1">{formatCurrency(summary.total_debt)}</p>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                <p className="text-white/50 text-xs uppercase tracking-wide">Total Pagado</p>
                <p className="text-2xl font-bold text-green-400 mt-1">{formatCurrency(summary.total_paid)}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
              <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                <h2 className="text-sm font-semibold text-white/70 mb-3">Deuda vs Pagado</h2>
                {hasDebts ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={40}>
                        {pieData.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v) => formatCurrency(v)} contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-white/40 text-sm text-center py-8">Sin movimientos</p>
                )}
              </div>

              <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                <h2 className="text-sm font-semibold text-white/70 mb-3">Deuda por Jugador</h2>
                {summary.by_player.filter(p => p.total_debt > 0).length > 0 ? (
                  <ResponsiveContainer width="100%" height={Math.max(150, summary.by_player.filter(p => p.total_debt > 0).length * 25)}>
                    <BarChart data={[...summary.by_player].filter(p => p.total_debt > 0).sort((a, b) => a.total_debt - b.total_debt)} layout="vertical" margin={{ top: 0, right: 0, bottom: 0, left: 10 }}>
                      <XAxis type="number" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="last_name" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }} axisLine={false} tickLine={false} width={80} />
                      <Tooltip formatter={(v) => formatCurrency(v)} contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }} />
                      <Bar dataKey="total_debt" fill="#DC2626" radius={[0, 4, 4, 0]} barSize={10} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-white/40 text-sm text-center py-8">Sin deudas</p>
                )}
              </div>
            </div>

            <div className="overflow-x-auto -mx-4 px-4">
              <table className="w-full text-sm min-w-[300px]">
                <thead>
                  <tr className="border-b border-white/10 text-white/50">
                    <th className="text-left py-2 pr-4">Jugador</th>
                    <th className="text-right py-2 px-2">Deuda</th>
                    <th className="text-right py-2 px-2">Pagado</th>
                    <th className="text-center py-2 pl-4">Pago</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.by_player.map(p => (
                    <tr key={p.player_name} className="border-b border-white/5">
                      <td className="py-2 pr-4">{p.player_name}</td>
                      <td className="py-2 text-right font-mono text-red-400 px-2">{p.total_debt > 0 ? formatCurrency(p.total_debt) : '—'}</td>
                      <td className="py-2 text-right font-mono text-green-400 px-2">{p.total_paid > 0 ? formatCurrency(p.total_paid) : '—'}</td>
                      <td className="py-2 text-center pl-4">
                        <div className={`w-3 h-3 rounded-full mx-auto ${p.has_unpaid ? 'bg-red-500' : 'bg-green-500'}`} />
                      </td>
                    </tr>
                  ))}
                  {summary.by_player.length === 0 && (
                    <tr><td colSpan={4} className="py-8 text-center text-white/40 text-sm">No hay jugadores con movimientos</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p className="text-white/40 text-sm animate-pulse">Cargando...</p>
        )}

      </div>
    </div>
  )
}
