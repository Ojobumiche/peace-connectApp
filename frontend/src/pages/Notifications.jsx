import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'

const TYPE_ICON = {
  PAYMENT_RECEIVED: '💰',
  PAYMENT_RECEIPT:  '🧾',
  LEVY_ASSIGNED:    '📋',
  LEVY_PAID:        '✅',
  DEBT_REMINDER:    '⚠️',
  CREDIT_APPROVED:  '🏦',
  ANNOUNCEMENT:     '📢',
}

const TYPE_COLOR = {
  PAYMENT_RECEIVED: 'border-green-200  bg-green-50',
  PAYMENT_RECEIPT:  'border-green-200  bg-green-50',
  LEVY_ASSIGNED:    'border-blue-200   bg-blue-50',
  LEVY_PAID:        'border-green-200  bg-green-50',
  DEBT_REMINDER:    'border-red-200    bg-red-50',
  CREDIT_APPROVED:  'border-blue-200   bg-blue-50',
  ANNOUNCEMENT:     'border-purple-200 bg-purple-50',
}

export default function Notifications() {
  const qc = useQueryClient()

  const { data = [], isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.get('/api/me/notifications/').then((r) => r.data.results ?? r.data),
  })

  const markRead = useMutation({
    mutationFn: (id) => api.post(`/api/me/notifications/${id}/read/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notif-count'] })
    },
  })

  const markAllRead = async () => {
    const unread = data.filter((n) => !n.is_read)
    await Promise.all(unread.map((n) => markRead.mutateAsync(n.id)))
  }

  const unread = data.filter((n) => !n.is_read)
  const read   = data.filter((n) =>  n.is_read)

  return (
    <div className="space-y-4 pb-24 lg:pb-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {unread.length > 0 && (
            <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {unread.length} new
            </span>
          )}
        </div>
        {unread.length > 1 && (
          <button
            onClick={markAllRead}
            className="text-xs text-blue-600 font-semibold hover:text-blue-800"
          >
            Mark all as read
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-gray-200 rounded-2xl" />)}
        </div>
      ) : data.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-2xl p-12 text-center">
          <p className="text-3xl mb-3">🔔</p>
          <p className="text-gray-500 font-medium text-sm">No notifications yet</p>
          <p className="text-gray-300 text-xs mt-1">You'll be notified here when payments are recorded or levies are assigned.</p>
        </div>
      ) : (
        <>
          {unread.length > 0 && (
            <section>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 px-1">New</p>
              <div className="space-y-2">
                {unread.map((n) => (
                  <NotifCard key={n.id} notif={n} onRead={() => markRead.mutate(n.id)} />
                ))}
              </div>
            </section>
          )}
          {read.length > 0 && (
            <section>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2 px-1 mt-4">Earlier</p>
              <div className="space-y-2">
                {read.map((n) => <NotifCard key={n.id} notif={n} />)}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}

function NotifCard({ notif, onRead }) {
  const icon  = TYPE_ICON[notif.notification_type]  || '🔔'
  const color = TYPE_COLOR[notif.notification_type] || 'border-gray-200 bg-white'

  return (
    <div className={`rounded-2xl border p-4 transition-all ${notif.is_read ? 'bg-white border-gray-100' : `${color} border`}`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl leading-none mt-0.5 shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={`text-sm font-semibold ${notif.is_read ? 'text-gray-700' : 'text-gray-900'}`}>
              {notif.title}
            </p>
            {!notif.is_read && onRead && (
              <button
                onClick={onRead}
                className="text-[10px] text-blue-600 hover:text-blue-800 font-semibold shrink-0 mt-0.5"
              >
                Mark read
              </button>
            )}
          </div>
          <p className="text-sm text-gray-600 mt-1 leading-relaxed">{notif.body}</p>
          <p className="text-[10px] text-gray-400 mt-2">
            {new Date(notif.created_at).toLocaleString('en-NG', {
              day: 'numeric', month: 'short', year: 'numeric',
              hour: '2-digit', minute: '2-digit',
            })}
          </p>
        </div>
      </div>
    </div>
  )
}
