import { useState, useEffect } from 'react'
import { getTopScorers, getTopYellow, getTopRed, getLastMatch, getUpcomingMatches, getPositions } from '../services/api'
import buenPaloLogo from '../assets/logo.svg'

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('es-AR', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
}

function formatTime(iso) {
  if (!iso || !iso.includes('T')) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
}

export default function PublicLanding({ onAdminClick }) {
  const [scorers, setScorers] = useState([])
  const [yellows, setYellows] = useState([])
  const [reds, setReds] = useState([])
  const [lastMatch, setLastMatch] = useState(null)
  const [upcoming, setUpcoming] = useState([])
  const [positions, setPositions] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      getTopScorers(),
      getTopYellow(),
      getTopRed(),
      getLastMatch(),
      getUpcomingMatches(),
      getPositions(),
    ])
      .then(([s, y, r, lm, up, pos]) => {
        setScorers(s)
        setYellows(y)
        setReds(r)
        setLastMatch(lm)
        setUpcoming(up)
        setPositions(pos)
      })
      .catch(() => setError('Error al cargar datos'))
  }, [])

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-black to-[#712005] flex items-center justify-center">
        <p className="text-red-300">{error}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-black to-[#712005] text-white">
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">

        <div className="flex items-start justify-between">
          <img src={buenPaloLogo} alt="Buen Palo" className="h-32 sm:h-36" />
          <button onClick={onAdminClick} className="text-sm text-white/60 hover:text-white px-3 py-1.5 rounded-lg border border-white/20 hover:border-white/40 transition-colors shrink-0">
            Admin
          </button>
        </div>

        <section>
          <h2 className="text-base font-semibold text-white/80 mb-2">⚡ Goleadores</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 text-white/50">
                <th className="text-left py-2">#</th>
                <th className="text-left py-2">Jugador</th>
                <th className="text-right py-2">Goles</th>
              </tr>
            </thead>
            <tbody>
              {scorers.filter(p => p.goals > 0).map((p, i) => (
                <tr key={p.name} className="border-b border-white/5">
                  <td className="py-2 text-white/50">{i + 1}</td>
                  <td className="py-2 text-sm">{p.name}</td>
                  <td className="py-2 text-right text-amber-400 font-mono">{p.goals}</td>
                </tr>
              ))}
              {scorers.filter(p => p.goals > 0).length === 0 && (
                <tr><td colSpan={3} className="py-4 text-center text-white/40 text-sm">Sin datos</td></tr>
              )}
            </tbody>
          </table>
        </section>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <section>
            <h2 className="text-base font-semibold text-white/80 mb-2">🟡 Tarjetas Amarillas</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-white/50">
                  <th className="text-left py-2">#</th>
                  <th className="text-left py-2">Jugador</th>
                  <th className="text-right py-2">Amarillas</th>
                </tr>
              </thead>
              <tbody>
                {yellows.filter(p => p.yellow_cards > 0).map((p, i) => (
                  <tr key={p.name} className="border-b border-white/5">
                    <td className="py-2 text-white/50">{i + 1}</td>
                    <td className="py-2 text-sm">{p.name}</td>
                    <td className="py-2 text-right text-yellow-400 font-mono">{p.yellow_cards}</td>
                  </tr>
                ))}
                {yellows.filter(p => p.yellow_cards > 0).length === 0 && (
                  <tr><td colSpan={3} className="py-4 text-center text-white/40 text-sm">Sin datos</td></tr>
                )}
              </tbody>
            </table>
          </section>

          <section>
            <h2 className="text-base font-semibold text-white/80 mb-2">🔴 Tarjetas Rojas</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-white/50">
                  <th className="text-left py-2">#</th>
                  <th className="text-left py-2">Jugador</th>
                  <th className="text-right py-2">Rojas</th>
                </tr>
              </thead>
              <tbody>
                {reds.filter(p => p.red_cards > 0).map((p, i) => (
                  <tr key={p.name} className="border-b border-white/5">
                    <td className="py-2 text-white/50">{i + 1}</td>
                    <td className="py-2 text-sm">{p.name}</td>
                    <td className="py-2 text-right text-red-400 font-mono">{p.red_cards}</td>
                  </tr>
                ))}
                {reds.filter(p => p.red_cards > 0).length === 0 && (
                  <tr><td colSpan={3} className="py-4 text-center text-white/40 text-sm">Sin datos</td></tr>
                )}
              </tbody>
            </table>
          </section>
        </div>

        <section>
          <h2 className="text-base font-semibold text-white/80 mb-2">📅 Último Partido</h2>
          {lastMatch ? (
            <table className="w-full text-sm">
              <tbody>
                <tr className="border-b border-white/5">
                  <td className="py-2 text-white/50 w-20">Fecha</td>
                  <td className="py-2">{formatDate(lastMatch.match_date)}</td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-2 text-white/50">Horario</td>
                  <td className="py-2">{formatTime(lastMatch.match_date) || '—'}</td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-2 text-white/50">Rival</td>
                  <td className="py-2">{lastMatch.opponent}</td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-2 text-white/50">Cancha</td>
                  <td className="py-2">{lastMatch.field || '—'}</td>
                </tr>
              </tbody>
            </table>
          ) : (
            <p className="text-white/40 text-sm">Sin partidos jugados</p>
          )}
        </section>

        <section>
          <h2 className="text-base font-semibold text-white/80 mb-2">📅 Próximos Partidos</h2>
          {upcoming.length > 0 ? (
            <div className="divide-y divide-white/5">
              {upcoming.map((m, i) => (
                <div key={i} className="flex items-center justify-between py-2 text-sm">
                  <div>
                    <span className="text-white/60">{formatDate(m.match_date)}</span>
                    <span className="text-white/20 mx-2">|</span>
                    <span className="text-white/60">{formatTime(m.match_date)}</span>
                  </div>
                  <div className="text-right">
                    <span>vs {m.opponent}</span>
                    <span className="text-white/40 ml-2">{m.field ? `— ${m.field}` : ''}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-white/40 text-sm">Sin partidos programados</p>
          )}
        </section>

        <section>
          <h2 className="text-base font-semibold text-white/80 mb-2">🏆 Tabla de Posiciones</h2>
          <div className="overflow-x-auto -mx-4 px-4">
            <table className="w-full text-sm min-w-[500px]">
              <thead>
                <tr className="border-b border-white/10 text-white/50">
                  <th className="text-left py-2 pr-2">#</th>
                  <th className="text-left py-2 pr-4">Equipo</th>
                  <th className="text-right py-2 px-1">Pts</th>
                  <th className="text-right py-2 px-1">PJ</th>
                  <th className="text-right py-2 px-1">G</th>
                  <th className="text-right py-2 px-1">E</th>
                  <th className="text-right py-2 px-1">P</th>
                  <th className="text-right py-2 px-1">GF</th>
                  <th className="text-right py-2 px-1">GC</th>
                  <th className="text-right py-2 pl-1">DG</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((p) => (
                  <tr key={p.position} className={`border-b border-white/5 ${p.team_name === 'Buen Palo' ? 'bg-white/10 font-medium' : ''}`}>
                    <td className="py-2 text-white/50 pr-2">{p.position}</td>
                    <td className="py-2 pr-4">{p.team_name}</td>
                    <td className="py-2 text-right font-mono text-amber-400 px-1">{p.points}</td>
                    <td className="py-2 text-right font-mono text-white/60 px-1">{p.played}</td>
                    <td className="py-2 text-right font-mono text-white/60 px-1">{p.won}</td>
                    <td className="py-2 text-right font-mono text-white/60 px-1">{p.drawn}</td>
                    <td className="py-2 text-right font-mono text-white/60 px-1">{p.lost}</td>
                    <td className="py-2 text-right font-mono text-white/60 px-1">{p.goals_for}</td>
                    <td className="py-2 text-right font-mono text-white/60 px-1">{p.goals_against}</td>
                    <td className="py-2 text-right font-mono text-white/60 pl-1">{p.goal_diff}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

      </div>
    </div>
  )
}
