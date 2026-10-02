import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'

const fmt = (n) => `₦${Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`

export default function Notifications() {
  const qc = useQueryClient()
  const { data = [], isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.get('/api/me/notifications/').then((r) => r.data.results ?? r.data),
  })

  const markRead = useMutation({
    mutationFn: (id) => api.post(`/api/me/notifications/${id}/read/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  if (isLoading) return <div className="text-gray-400 p-6">Loading…</div>

  const unread = data.filter((n) => !n.is_read)
  const read = data.filter((n) => n.is_read)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold text-gray-900">Notifications</h1>
        {unread.length > 0 && (
          <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
            {unread.length} new
          </span>
        )}
      </div>

      {data.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 px-5 py-12 text-center text-gray-400">
          No notifications yet.
        </div>
      )}

      {unread.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">New</p>
          {unread.map((n) => (
            <NotifCard key={n.id} notif={n} onRead={() => markRead.mutate(n.id)} />
          ))}
        </div>
      )}
      {read.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Earlier</p>
          {read.map((n) => <NotifCard key={n.id} notif={n} />)}
        </div>
      )}
    </div>
  )
}

function NotifCard({ notif, onRead }) {
  const TYPE_ICON = {
    PAYMENT_RECEIVED: '💰',
    PAYMENT_RECEIPT: '🧾',
    LEVY_ASSIGNED: '📋',
    LEVY_PAID: '✅',
    DEBT_REMINDER: '⚠️',
    CREDIT_APPROVED: '🏦',
    ANNOUNCEMENT: '📢',
  }
  return (
    <div
      className={`rounded-xl border p-4 transition-colors ${
        notif.is_read ? 'bg-white border-gray-100' : 'bg-blue-50 border-blue-200'
      }`}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl">{TYPE_ICON[notif.notification_type] || '🔔'}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-800">{notif.title}</p>
          <p className="text-sm text-gray-600 mt-0.5 leading-relaxed">{notif.body}</p>
          <p className="text-xs text-gray-400 mt-1">
            {new Date(notif.created_at).toLocaleString('en-NG')}
          </p>
        </div>
        {!notif.is_read && onRead && (
          <button
            onClick={onRead}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium shrink-0"
          >
            Mark read
          </button>
        )}
      </div>
    </div>
  )
}
