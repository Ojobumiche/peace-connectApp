import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

const fmt = (n) =>
  '₦' + Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })

const METHOD_STYLE = {
  CASH:          'bg-green-100  text-green-700',
  BANK_TRANSFER: 'bg-blue-100   text-blue-700',
  POS:           'bg-purple-100 text-purple-700',
  ONLINE:        'bg-amber-100  text-amber-700',
}

export default function MyPayments() {
  const { data = [], isLoading, error } = useQuery({
    queryKey: ['my-payments'],
    queryFn: () => api.get('/api/me/payments/').then((r) => r.data.results ?? r.data),
  })

  const total = data.reduce((s, p) => s + parseFloat(p.amount || 0), 0)

  return (
    <div className="space-y-5 pb-24 lg:pb-6">

      {/* Summary */}
      {data.length > 0 && (
        <div className="bg-green-600 rounded-2xl p-5 text-white">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-70 mb-1">
            Total Contributed
          </p>
          <p className="text-3xl font-bold">{fmt(total)}</p>
          <p className="text-xs opacity-60 mt-1">
            Across {data.length} payment{data.length !== 1 ? 's' : ''}
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-gray-200 rounded-2xl" />)}
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl p-5 text-sm">
          Could not load payments. Make sure the backend server is running.
        </div>
      ) : data.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-2xl p-10 text-center">
          <p className="text-gray-400 text-sm">No payments recorded yet.</p>
          <p className="text-gray-300 text-xs mt-1">Payments will appear here once the Financial Secretary records them.</p>
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Reference', 'Amount', 'Method', 'Date', 'Notes'].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-5 py-4 font-mono text-xs text-blue-700 font-semibold">{p.reference}</td>
                    <td className="px-5 py-4 font-bold text-green-700 text-base">{fmt(p.amount)}</td>
                    <td className="px-5 py-4">
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${METHOD_STYLE[p.payment_method] || 'bg-gray-100 text-gray-600'}`}>
                        {p.payment_method?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-gray-500">
                      {new Date(p.payment_date).toLocaleDateString('en-NG', {
                        day: 'numeric', month: 'long', year: 'numeric',
                      })}
                    </td>
                    <td className="px-5 py-4 text-gray-400 text-xs max-w-[180px] truncate">
                      {p.notes || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
              {/* Running total footer */}
              <tfoot className="bg-gray-50 border-t border-gray-200">
                <tr>
                  <td colSpan={2} className="px-5 py-3 text-sm font-bold text-gray-700">
                    Total: <span className="text-green-700">{fmt(total)}</span>
                  </td>
                  <td colSpan={3} className="px-5 py-3 text-xs text-gray-400 text-right">
                    {data.length} payments
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {data.map((p) => (
              <div key={p.id} className="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-mono text-xs text-blue-600 font-semibold">{p.reference}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(p.payment_date).toLocaleDateString('en-NG', {
                        day: 'numeric', month: 'short', year: 'numeric',
                      })}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-green-700">{fmt(p.amount)}</p>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${METHOD_STYLE[p.payment_method] || 'bg-gray-100 text-gray-600'}`}>
                      {p.payment_method?.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
                {p.notes && (
                  <p className="text-xs text-gray-400 border-t border-gray-100 pt-2 mt-2">{p.notes}</p>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
