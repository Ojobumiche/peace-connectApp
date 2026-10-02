import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

const fmt = (n) =>
  '₦' + Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })

export default function MyCredits() {
  const { data = [], isLoading, error } = useQuery({
    queryKey: ['my-credits'],
    queryFn: () => api.get('/api/me/credits/').then((r) => r.data.results ?? r.data),
  })

  const totalAvailable = data.reduce((s, c) => s + parseFloat(c.balance || 0), 0)
  const totalCredit    = data.reduce((s, c) => s + parseFloat(c.amount  || 0), 0)
  const totalUsed      = data.reduce((s, c) => s + parseFloat(c.amount_used_calculated || 0), 0)

  return (
    <div className="space-y-5 pb-24 lg:pb-6">

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-blue-600 rounded-2xl p-4 text-white text-center">
          <p className="text-[10px] font-semibold uppercase tracking-wide opacity-70 mb-1">Total Credit</p>
          <p className="text-lg font-bold">{fmt(totalCredit)}</p>
        </div>
        <div className="bg-orange-500 rounded-2xl p-4 text-white text-center">
          <p className="text-[10px] font-semibold uppercase tracking-wide opacity-70 mb-1">Used</p>
          <p className="text-lg font-bold">{fmt(totalUsed)}</p>
        </div>
        <div className="bg-green-600 rounded-2xl p-4 text-white text-center">
          <p className="text-[10px] font-semibold uppercase tracking-wide opacity-70 mb-1">Available</p>
          <p className="text-lg font-bold">{fmt(totalAvailable)}</p>
        </div>
      </div>

      {/* Info banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-2xl px-4 py-3 text-xs text-blue-700">
        <strong>What is credit?</strong> When you pay more than your levy amount, the excess becomes credit.
        The Financial Secretary can approve this credit to cover future levies.
      </div>

      {isLoading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(2)].map((_, i) => <div key={i} className="h-32 bg-gray-200 rounded-2xl" />)}
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl p-5 text-sm">
          Could not load credits. Make sure the backend is running.
        </div>
      ) : data.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-2xl p-10 text-center">
          <p className="text-gray-400 text-sm">No credit records yet.</p>
          <p className="text-gray-300 text-xs mt-1">Credits appear when you overpay a levy.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data.map((c) => {
            const pct = totalCredit > 0 ? (parseFloat(c.amount_used_calculated) / parseFloat(c.amount)) * 100 : 0
            return (
              <div key={c.id} className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <p className="text-xs text-gray-400 mb-0.5">Payment Reference</p>
                    <p className="font-mono text-sm font-semibold text-blue-700">{c.payment_reference}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(c.created_at).toLocaleDateString('en-NG', {
                        day: 'numeric', month: 'long', year: 'numeric',
                      })}
                    </p>
                  </div>
                  <div className="text-right">
                    {c.approved_for_future_use ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-green-100 text-green-700 border border-green-200 px-2.5 py-1 rounded-full">
                        ✓ Approved
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-amber-100 text-amber-700 border border-amber-200 px-2.5 py-1 rounded-full">
                        Pending
                      </span>
                    )}
                  </div>
                </div>

                {/* Breakdown */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs mb-4">
                  <div className="bg-gray-50 rounded-xl py-2.5">
                    <p className="font-bold text-gray-800 text-sm">{fmt(c.amount)}</p>
                    <p className="text-gray-400 mt-0.5">Total</p>
                  </div>
                  <div className="bg-orange-50 rounded-xl py-2.5">
                    <p className="font-bold text-orange-700 text-sm">{fmt(c.amount_used_calculated)}</p>
                    <p className="text-gray-400 mt-0.5">Used</p>
                  </div>
                  <div className="bg-green-50 rounded-xl py-2.5">
                    <p className="font-bold text-green-700 text-sm">{fmt(c.balance)}</p>
                    <p className="text-gray-400 mt-0.5">Available</p>
                  </div>
                </div>

                {/* Progress bar */}
                <div>
                  <div className="flex justify-between text-[10px] text-gray-400 mb-1">
                    <span>Used</span>
                    <span>{Math.round(pct)}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all"
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    />
                  </div>
                </div>

                {c.approval_note && (
                  <p className="text-xs text-gray-500 mt-3 pt-3 border-t border-gray-100">
                    <strong>Note:</strong> {c.approval_note}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
