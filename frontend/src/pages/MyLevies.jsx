import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

const fmt = (n) =>
  '₦' + Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })

const STATUS_STYLE = {
  PAID:    { pill: 'bg-green-100 text-green-700 border-green-200', dot: 'bg-green-500' },
  PARTIAL: { pill: 'bg-amber-100 text-amber-700 border-amber-200', dot: 'bg-amber-500' },
  UNPAID:  { pill: 'bg-red-100   text-red-700   border-red-200',   dot: 'bg-red-500' },
}

export default function MyLevies() {
  const [filter, setFilter] = useState('ALL')

  const { data = [], isLoading, error } = useQuery({
    queryKey: ['my-levies'],
    queryFn: () => api.get('/api/me/levies/').then((r) => r.data.results ?? r.data),
  })

  const filtered = filter === 'ALL' ? data : data.filter((l) => l.status === filter)

  // Summary totals
  const totalDue  = data.reduce((s, l) => s + parseFloat(l.amount_due  || 0), 0)
  const totalPaid = data.reduce((s, l) => s + parseFloat(l.amount_paid || 0), 0)
  const totalOwed = data.reduce((s, l) => s + parseFloat(l.balance     || 0), 0)

  return (
    <div className="space-y-5 pb-24 lg:pb-6">

      {/* Summary bar */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-2xl border border-gray-200 p-4 text-center shadow-sm">
          <p className="text-xs text-gray-500 mb-1">Total Due</p>
          <p className="text-base font-bold text-gray-900">{fmt(totalDue)}</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-200 p-4 text-center shadow-sm">
          <p className="text-xs text-gray-500 mb-1">Total Paid</p>
          <p className="text-base font-bold text-green-700">{fmt(totalPaid)}</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-200 p-4 text-center shadow-sm">
          <p className="text-xs text-gray-500 mb-1">Outstanding</p>
          <p className={`text-base font-bold ${totalOwed > 0 ? 'text-red-600' : 'text-green-600'}`}>
            {fmt(totalOwed)}
          </p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {['ALL', 'UNPAID', 'PARTIAL', 'PAID'].map((s) => {
          const count = s === 'ALL' ? data.length : data.filter((l) => l.status === s).length
          return (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                filter === s
                  ? 'bg-slate-800 text-white border-slate-800'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
              }`}
            >
              {s} <span className="opacity-60 ml-0.5">({count})</span>
            </button>
          )
        })}
      </div>

      {/* Table / cards */}
      {isLoading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-gray-200 rounded-2xl" />)}
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl p-5 text-sm">
          Could not load levies. Make sure the backend server is running.
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-2xl p-10 text-center text-gray-400 text-sm">
          No levies found for this filter.
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Levy Name', 'Type', 'Period', 'Amount Due', 'Paid', 'Balance', 'Status'].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map((l) => {
                  const s = STATUS_STYLE[l.status] || {}
                  return (
                    <tr key={l.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-5 py-4 font-medium text-gray-800">{l.levy_name}</td>
                      <td className="px-5 py-4 text-gray-500 text-xs capitalize">{l.levy_type?.replace(/_/g, ' ')}</td>
                      <td className="px-5 py-4 text-gray-500">
                        {new Date(l.period + '-01').toLocaleDateString('en-NG', { month: 'short', year: 'numeric' })}
                      </td>
                      <td className="px-5 py-4 font-medium text-gray-700">{fmt(l.amount_due)}</td>
                      <td className="px-5 py-4 text-green-700 font-medium">{fmt(l.amount_paid)}</td>
                      <td className={`px-5 py-4 font-semibold ${parseFloat(l.balance) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {fmt(l.balance)}
                      </td>
                      <td className="px-5 py-4">
                        <span className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full border ${s.pill || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${s.dot || 'bg-gray-400'}`} />
                          {l.status}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {filtered.map((l) => {
              const s = STATUS_STYLE[l.status] || {}
              return (
                <div key={l.id} className="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-semibold text-gray-800 text-sm">{l.levy_name}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {new Date(l.period + '-01').toLocaleDateString('en-NG', { month: 'long', year: 'numeric' })}
                      </p>
                    </div>
                    <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${s.pill || ''}`}>
                      {l.status}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs mt-1">
                    <div className="bg-gray-50 rounded-xl py-2">
                      <p className="font-semibold text-gray-700">{fmt(l.amount_due)}</p>
                      <p className="text-gray-400 mt-0.5">Due</p>
                    </div>
                    <div className="bg-green-50 rounded-xl py-2">
                      <p className="font-semibold text-green-700">{fmt(l.amount_paid)}</p>
                      <p className="text-gray-400 mt-0.5">Paid</p>
                    </div>
                    <div className={`rounded-xl py-2 ${parseFloat(l.balance) > 0 ? 'bg-red-50' : 'bg-green-50'}`}>
                      <p className={`font-semibold ${parseFloat(l.balance) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {fmt(l.balance)}
                      </p>
                      <p className="text-gray-400 mt-0.5">Balance</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
