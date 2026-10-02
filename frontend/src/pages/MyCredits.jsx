import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

const fmt = (n) => `₦${Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`

export default function MyCredits() {
  const { data = [], isLoading } = useQuery({
    queryKey: ['my-credits'],
    queryFn: () => api.get('/api/me/credits/').then((r) => r.data.results ?? r.data),
  })

  if (isLoading) return <div className="text-gray-400 p-6">Loading…</div>

  const totalCredit = data.reduce((s, c) => s + parseFloat(c.balance || 0), 0)

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-900">My Credit Balance</h1>

      {/* Summary card */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">
          Total Available Credit
        </p>
        <p className="text-3xl font-bold text-blue-800">{fmt(totalCredit)}</p>
        <p className="text-xs text-blue-500 mt-1">
          Credit is applied automatically when you make excess payments.
        </p>
      </div>

      {data.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 px-5 py-10 text-center text-gray-400">
          No credit records yet.
        </div>
      )}

      <div className="space-y-3">
        {data.map((c) => (
          <div key={c.id} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-semibold text-gray-800">
                  Payment: {c.payment_reference}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  Created: {new Date(c.created_at).toLocaleDateString('en-NG')}
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-blue-700">{fmt(c.balance)}</p>
                <p className="text-xs text-gray-400">available</p>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-3 text-center text-xs">
              <div className="bg-gray-50 rounded-lg py-2">
                <p className="font-semibold text-gray-800">{fmt(c.amount)}</p>
                <p className="text-gray-400">Total</p>
              </div>
              <div className="bg-gray-50 rounded-lg py-2">
                <p className="font-semibold text-gray-800">{fmt(c.amount_used_calculated)}</p>
                <p className="text-gray-400">Used</p>
              </div>
              <div className="bg-blue-50 rounded-lg py-2">
                <p className="font-semibold text-blue-700">{fmt(c.balance)}</p>
                <p className="text-blue-400">Balance</p>
              </div>
            </div>
            {c.approved_for_future_use && (
              <div className="mt-2 text-xs text-green-700 font-semibold">
                ✔ Approved for future levy
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
