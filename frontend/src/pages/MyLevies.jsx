import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

const fmt = (n) => `₦${Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`

const STATUS_STYLE = {
  PAID: 'bg-green-100 text-green-700',
  PARTIAL: 'bg-amber-100 text-amber-700',
  UNPAID: 'bg-red-100 text-red-700',
}

export default function MyLevies() {
  const { data = [], isLoading } = useQuery({
    queryKey: ['my-levies'],
    queryFn: () => api.get('/api/me/levies/').then((r) => r.data.results ?? r.data),
  })

  if (isLoading) return <div className="text-gray-400 p-6">Loading…</div>

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-900">My Levies</h1>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th className="px-5 py-3 text-left">Levy</th>
              <th className="px-5 py-3 text-left">Period</th>
              <th className="px-5 py-3 text-right">Due</th>
              <th className="px-5 py-3 text-right">Paid</th>
              <th className="px-5 py-3 text-right">Balance</th>
              <th className="px-5 py-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {data.length === 0 && (
              <tr><td colSpan={6} className="px-5 py-8 text-center text-gray-400">No levies yet.</td></tr>
            )}
            {data.map((l) => (
              <tr key={l.id} className="hover:bg-gray-50">
                <td className="px-5 py-3 font-medium text-gray-800">{l.levy_name}</td>
                <td className="px-5 py-3 text-gray-500">{l.period}</td>
                <td className="px-5 py-3 text-right">{fmt(l.amount_due)}</td>
                <td className="px-5 py-3 text-right text-green-700">{fmt(l.amount_paid)}</td>
                <td className="px-5 py-3 text-right font-semibold">{fmt(l.balance)}</td>
                <td className="px-5 py-3 text-center">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_STYLE[l.status] || 'bg-gray-100 text-gray-600'}`}>
                    {l.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
