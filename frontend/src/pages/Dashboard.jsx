import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'
import useAuthStore from '../store/authStore'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

const fmt = (n) => `₦${Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`

function StatCard({ label, value, sub, color = 'blue' }) {
  const colors = {
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    red: 'bg-red-50 border-red-200 text-red-800',
    amber: 'bg-amber-50 border-amber-200 text-amber-800',
  }
  return (
    <div className={`rounded-xl border p-5 ${colors[color]}`}>
      <p className="text-xs font-semibold uppercase tracking-wide opacity-70 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      {sub && <p className="text-xs mt-1 opacity-60">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const user = useAuthStore((s) => s.user)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/api/me/dashboard/').then((r) => r.data),
  })

  if (isLoading) return (
    <div className="flex items-center justify-center h-64 text-gray-400">Loading…</div>
  )
  if (error) return (
    <div className="text-red-600 p-6">Failed to load dashboard.</div>
  )

  const member = data.member
  const payments = data.recent_payments || []

  const chartData = payments.map((p) => ({
    ref: p.reference?.slice(-6),
    amount: parseFloat(p.amount),
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">
          Welcome, {member.first_name} 👋
        </h1>
        <p className="text-sm text-gray-500">{member.house_address}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Levied" value={fmt(member.total_levy_due)} color="blue" />
        <StatCard label="Total Paid" value={fmt(member.total_levy_paid)} color="green" />
        <StatCard
          label="Amount Owed"
          value={fmt(member.outstanding_balance)}
          color={parseFloat(member.outstanding_balance) > 0 ? 'red' : 'green'}
        />
        <StatCard label="Credit Balance" value={fmt(member.available_credit)} color="amber" />
      </div>

      {/* Unread notifications badge */}
      {data.unread_notifications > 0 && (
        <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-xl px-4 py-3">
          <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold">
            {data.unread_notifications}
          </span>
          <p className="text-sm text-blue-800 font-medium">
            You have {data.unread_notifications} unread notification{data.unread_notifications > 1 ? 's' : ''}.
          </p>
        </div>
      )}

      {/* Recent payments chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Recent Payments</h2>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="ref" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `₦${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(v) => fmt(v)} />
              <Bar dataKey="amount" fill="#1d4ed8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent levies */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Recent Levies</h2>
        </div>
        <div className="divide-y divide-gray-50">
          {data.recent_levies.map((l) => (
            <div key={l.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm font-medium text-gray-800">{l.levy_name}</p>
                <p className="text-xs text-gray-400">{l.period}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-800">{fmt(l.balance)} left</p>
                <StatusPill status={l.status} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatusPill({ status }) {
  const map = {
    PAID: 'bg-green-100 text-green-700',
    PARTIAL: 'bg-amber-100 text-amber-700',
    UNPAID: 'bg-red-100 text-red-700',
  }
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${map[status] || 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}
