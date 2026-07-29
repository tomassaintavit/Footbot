const API_URL = import.meta.env.VITE_API_URL || '';

export async function getTopScorers() {
  const res = await fetch(`${API_URL}/api/public/players/top-scorers`);
  return res.json();
}

export async function getTopYellow() {
  const res = await fetch(`${API_URL}/api/public/players/top-yellow`);
  return res.json();
}

export async function getTopRed() {
  const res = await fetch(`${API_URL}/api/public/players/top-red`);
  return res.json();
}

export async function getLastMatch() {
  const res = await fetch(`${API_URL}/api/public/matches/last`);
  if (!res.ok) return null;
  return res.json();
}

export async function getUpcomingMatches() {
  const res = await fetch(`${API_URL}/api/public/matches/upcoming`);
  return res.json();
}

export async function getPositions() {
  const res = await fetch(`${API_URL}/api/public/positions`);
  return res.json();
}

async function authFetch(url, token) {
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getMe(token) {
  return authFetch(`${API_URL}/api/admin/me`, token);
}

export async function getDebts(token) {
  return authFetch(`${API_URL}/api/admin/debts`, token);
}

export async function getDebtsSummary(token) {
  return authFetch(`${API_URL}/api/admin/debts/summary`, token);
}
