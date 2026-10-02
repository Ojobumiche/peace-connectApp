import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'

export default function Profile() {
  const qc = useQueryClient()
  const { data: member, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: () => api.get('/api/me/profile/').then((r) => r.data),
  })

  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '' })
  const [pwMsg, setPwMsg] = useState(null)

  const changePw = useMutation({
    mutationFn: (d) => api.post('/api/auth/change-password/', d),
    onSuccess: () => {
      setPwMsg({ ok: true, text: 'Password changed successfully.' })
      setPwForm({ old_password: '', new_password: '' })
    },
    onError: (e) => setPwMsg({ ok: false, text: e.response?.data?.old_password || 'Error.' }),
  })

  if (isLoading) return <div className="text-gray-400 p-6">Loading…</div>

  return (
    <div className="space-y-6 max-w-lg">
      <h1 className="text-xl font-bold text-gray-900">My Profile</h1>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 bg-gray-50 border-b border-gray-100">
          <p className="text-sm font-semibold text-gray-700">Personal Information</p>
        </div>
        <div className="px-5 py-4 space-y-3 text-sm">
          {[
            ['Full Name', member?.full_name],
            ['Phone', member?.phone],
            ['WhatsApp', member?.whatsapp || '—'],
            ['Email', member?.email || '—'],
            ['Address', member?.house_address],
            ['Member Type', member?.member_type],
            ['Status', member?.status],
            ['Date Joined', member?.date_joined],
          ].map(([label, val]) => (
            <div key={label} className="flex justify-between">
              <span className="text-gray-500">{label}</span>
              <span className="font-medium text-gray-800">{val}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Change password */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 bg-gray-50 border-b border-gray-100">
          <p className="text-sm font-semibold text-gray-700">Change Password</p>
        </div>
        <form
          className="px-5 py-4 space-y-4"
          onSubmit={(e) => { e.preventDefault(); changePw.mutate(pwForm) }}
        >
          {pwMsg && (
            <div className={`text-sm px-3 py-2 rounded-lg ${
              pwMsg.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            }`}>{pwMsg.text}</div>
          )}
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Current Password</label>
            <input
              type="password"
              required
              value={pwForm.old_password}
              onChange={(e) => setPwForm({ ...pwForm, old_password: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">New Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={pwForm.new_password}
              onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={changePw.isPending}
            className="w-full py-2.5 bg-blue-700 text-white text-sm font-semibold rounded-lg hover:bg-blue-800 transition-colors disabled:opacity-60"
          >
            {changePw.isPending ? 'Saving…' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
