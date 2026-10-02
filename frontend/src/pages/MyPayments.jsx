import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

const fmt = (n) => `₦${Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`

export default function MyPayments() {
  const { data = [], isLoading } = useQuery({
    queryKey: ['my-payments'],
    queryFn: () => api.get('/api/me/payments/').then((r) => r.data.results ?? r.data),
  })

  if (isLoading) return <div className="text-gray-400 p-6">Loading…</div>

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-900">My Payments</h1>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th className="px-5 py-3 text-left">Reference</th>
              <th className="px-5 py-3 text-right">Amount</th>
              <th className="px-5 py-3 text-left">Method</th>
              <th className="px-5 py-3 text-left">Date</th>
              <th className="px-5 py-3 text-left">Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {data.length === 0 && (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-gray-400">No payments recorded yet.</td></tr>
            )}
            {data.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-5 py-3 font-mono text-xs text-blue-700 font-semibold">{p.reference}</td>
                <td className="px-5 py-3 text-right font-semibold text-green-700">{fmt(p.amount)}</td>
                <td className="px-5 py-3 text-gray-500">{p.payment_method}</td>
                <td className="px-5 py-3 text-gray-500">
                  {new Date(p.payment_date).toLocaleDateString('en-NG')}
                </td>
                <td className="px-5 py-3 text-gray-400 text-xs">{p.notes || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
