import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import useAuthStore from '../store/authStore'
import api from '../lib/api'

const fmt = (n) =>
  '₦' + Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })

function StatCard({ label, value, sub, colorClass, icon }) {
  return (
    <div className={`rounded-2xl p-5 ${colorClass}`}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-semibold uppercase tracking-wider opacity-70">{label}</p>
        <span className="text-xl opacity-80">{icon}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      {sub && <p className="text-xs mt-1 opacity-60">{sub}</p>}
    </div>
  )
}

const STATUS_COLORS = {
  PAID:    'bg-green-100 text-green-700 border-green-200',
  PARTIAL: 'bg-amber-100 text-amber-700 border-amber-200',
  UNPAID:  'bg-red-100   text-red-700   border-red-200',
}

export default function Dashboard() {
  const user = useAuthStore((s) => s.user)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/api/me/dashboard/').then((r) => r.data),
  })

  if (isLoading) return <LoadingSkeleton />
  if (error)     return <ErrorBanner msg="Could not load your dashboard. Is the server running?" />

  const { member, recent_levies = [], recent_payments = [], unread_notifications = 0 } = data

  // Build payment bar chart data
  const chartData = [...recent_payments]
    .reverse()
    .map((p) => ({
      label: new Date(p.payment_date).toLocaleDateString('en-NG', { month: 'short', day: 'numeric' }),
      amount: parseFloat(p.amount),
    }))

  // Levy status breakdown
  const statusCount = recent_levies.reduce((acc, l) => {
    acc[l.status] = (acc[l.status] || 0) + 1
    return acc
  }, {})

  return (
    <div className="space-y-6 pb-24 lg:pb-6">

      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            Welcome back, {member.first_name} 👋
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">{member.house_address}</p>
        </div>
        {unread_notifications > 0 && (
          <Link
            to="/notifications"
            className="flex items-center gap-2 bg-blue-50 border border-blue-200 text-blue-700 rounded-xl px-3 py-2 text-xs font-semibold hover:bg-blue-100 transition-colors"
          >
            <span className="w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-[10px] font-bold">
              {unread_notifications}
            </span>
            New alerts
          </Link>
        )}
      </div>

      {/* 4 stat cards */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          label="Total Levied"
          value={fmt(member.total_levy_due)}
          sub="All levies assigned to you"
          icon="📋"
          colorClass="bg-slate-800 text-white"
        />
        <StatCard
          label="Total Paid"
          value={fmt(member.total_levy_paid)}
          sub="Confirmed contributions"
          icon="✅"
          colorClass="bg-green-600 text-white"
        />
        <StatCard
          label="Amount Owed"
          value={fmt(member.outstanding_balance)}
          sub={parseFloat(member.outstanding_balance) > 0 ? 'Please clear this soon' : 'You are up to date!'}
          icon={parseFloat(member.outstanding_balance) > 0 ? '⚠️' : '🎉'}
          colorClass={parseFloat(member.outstanding_balance) > 0 ? 'bg-red-50 border border-red-200 text-red-800' : 'bg-green-50 border border-green-200 text-green-800'}
        />
        <StatCard
          label="Credit Balance"
          value={fmt(member.available_credit)}
          sub="Available for future levies"
          icon="🏦"
          colorClass="bg-blue-50 border border-blue-200 text-blue-800"
        />
      </div>

      {/* Payment trend */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-800">Recent Payments</h2>
            <Link to="/payments" className="text-xs text-blue-600 font-medium hover:underline">
              View all →
            </Link>
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
              <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false}
                tickFormatter={(v) => v >= 1000 ? `₦${(v / 1000).toFixed(0)}k` : `₦${v}`}
              />
              <Tooltip
                formatter={(v) => [fmt(v), 'Amount']}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
              />
              <Bar dataKey="amount" fill="#2563eb" radius={[6, 6, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent levies */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-800">Recent Levies</h2>
          <Link to="/levies" className="text-xs text-blue-600 font-medium hover:underline">
            View all →
          </Link>
        </div>

        {recent_levies.length === 0 ? (
          <EmptyState msg="No levies assigned yet." />
        ) : (
          <div className="divide-y divide-gray-50">
            {recent_levies.map((l) => (
              <div key={l.id} className="flex items-center justify-between px-5 py-3.5">
                <div className="min-w-0 mr-4">
                  <p className="text-sm font-medium text-gray-800 truncate">{l.levy_name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(l.period + '-01').toLocaleDateString('en-NG', { month: 'long', year: 'numeric' })}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-800">{fmt(l.balance)}</p>
                    <p className="text-[10px] text-gray-400">remaining</p>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-1 rounded-full border ${STATUS_COLORS[l.status] || 'bg-gray-100 text-gray-500 border-gray-200'}`}>
                    {l.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Levy status summary pills */}
      {Object.keys(statusCount).length > 0 && (
        <div className="flex gap-3 flex-wrap">
          {Object.entries(statusCount).map(([status, count]) => (
            <div key={status} className={`flex items-center gap-2 px-4 py-2 rounded-full border text-xs font-semibold ${STATUS_COLORS[status] || 'bg-gray-100 text-gray-500 border-gray-200'}`}>
              <span>{count}</span>
              <span>{status}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse pb-24 lg:pb-0">
      <div className="h-8 w-48 bg-gray-200 rounded-xl" />
      <div className="grid grid-cols-2 gap-3">
        {[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-gray-200 rounded-2xl" />)}
      </div>
      <div className="h-48 bg-gray-200 rounded-2xl" />
      <div className="h-64 bg-gray-200 rounded-2xl" />
    </div>
  )
}

function ErrorBanner({ msg }) {
  return (
    <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl p-6 text-sm">
      <p className="font-semibold mb-1">Something went wrong</p>
      <p className="text-red-500">{msg}</p>
    </div>
  )
}

function EmptyState({ msg }) {
  return <p className="text-center text-sm text-gray-400 py-8">{msg}</p>
}
