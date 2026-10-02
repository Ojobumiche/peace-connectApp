import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import api from '../lib/api'

export default function Profile() {
  const { data: member, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: () => api.get('/api/me/profile/').then((r) => r.data),
  })

  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', confirm: '' })
  const [pwMsg, setPwMsg]   = useState(null)
  const [showPw, setShowPw] = useState(false)

  const changePw = useMutation({
    mutationFn: (d) => api.post('/api/auth/change-password/', d),
    onSuccess: () => {
      setPwMsg({ ok: true, text: 'Password changed successfully. Use the new password next time you log in.' })
      setPwForm({ old_password: '', new_password: '', confirm: '' })
    },
    onError: (e) => {
      const msg = e.response?.data?.old_password || e.response?.data?.detail || 'Could not change password.'
      setPwMsg({ ok: false, text: msg })
    },
  })

  const handlePwSubmit = (e) => {
    e.preventDefault()
    if (pwForm.new_password !== pwForm.confirm) {
      setPwMsg({ ok: false, text: 'New passwords do not match.' })
      return
    }
    setPwMsg(null)
    changePw.mutate({ old_password: pwForm.old_password, new_password: pwForm.new_password })
  }

  if (isLoading) return (
    <div className="space-y-4 animate-pulse">
      <div className="h-24 bg-gray-200 rounded-2xl" />
      <div className="h-64 bg-gray-200 rounded-2xl" />
    </div>
  )

  const INFO_ROWS = [
    ['Full Name',    member?.full_name],
    ['Phone',        member?.phone],
    ['WhatsApp',     member?.whatsapp || '—'],
    ['Email',        member?.email    || '—'],
    ['House Address', member?.house_address],
    ['Member Type',  member?.member_type?.replace(/_/g, ' ')],
    ['Status',       member?.status],
    ['Date Joined',  new Date(member?.date_joined).toLocaleDateString('en-NG', { day: 'numeric', month: 'long', year: 'numeric' })],
  ]

  return (
    <div className="space-y-5 pb-24 lg:pb-6 max-w-lg">

      {/* Avatar card */}
      <div className="bg-gradient-to-br from-slate-800 to-blue-900 rounded-2xl p-6 text-white flex items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-blue-500 flex items-center justify-center text-2xl font-bold shrink-0">
          {member?.full_name?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() || 'M'}
        </div>
        <div>
          <p className="text-lg font-bold">{member?.full_name}</p>
          <p className="text-blue-300 text-sm">{member?.member_type?.replace(/_/g, ' ')}</p>
          <div className={`inline-flex items-center gap-1.5 mt-2 text-xs font-semibold px-2.5 py-1 rounded-full ${
            member?.status === 'ACTIVE' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${member?.status === 'ACTIVE' ? 'bg-green-400' : 'bg-red-400'}`} />
            {member?.status}
          </div>
        </div>
      </div>

      {/* Personal info */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
          <p className="text-sm font-semibold text-gray-700">Personal Information</p>
        </div>
        <div className="divide-y divide-gray-50">
          {INFO_ROWS.map(([label, val]) => (
            <div key={label} className="flex items-start justify-between px-5 py-3.5">
              <span className="text-sm text-gray-500 min-w-[120px] shrink-0">{label}</span>
              <span className="text-sm font-medium text-gray-800 text-right">{val}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Change password */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
          <p className="text-sm font-semibold text-gray-700">Change Password</p>
        </div>
        <form onSubmit={handlePwSubmit} className="px-5 py-5 space-y-4">
          {pwMsg && (
            <div className={`rounded-xl px-4 py-3 text-sm ${
              pwMsg.ok
                ? 'bg-green-50 border border-green-200 text-green-700'
                : 'bg-red-50   border border-red-200   text-red-700'
            }`}>
              {pwMsg.text}
            </div>
          )}
          {[
            { name: 'old_password',  label: 'Current Password' },
            { name: 'new_password',  label: 'New Password',     min: 8 },
            { name: 'confirm',       label: 'Confirm New Password' },
          ].map(({ name, label, min }) => (
            <div key={name}>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5">{label}</label>
              <input
                type={showPw ? 'text' : 'password'}
                required
                minLength={min}
                value={pwForm[name]}
                onChange={(e) => setPwForm({ ...pwForm, [name]: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition-all"
              />
            </div>
          ))}
          <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer select-none">
            <input type="checkbox" checked={showPw} onChange={() => setShowPw(!showPw)} className="rounded" />
            Show passwords
          </label>
          <button
            type="submit"
            disabled={changePw.isPending}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition-colors disabled:opacity-60"
          >
            {changePw.isPending ? 'Saving…' : 'Update Password'}
          </button>
        </form>
      </div>

      {/* Contact info */}
      <p className="text-center text-xs text-gray-400">
        To update your personal information, contact the Financial Secretary.
      </p>
    </div>
  )
}
