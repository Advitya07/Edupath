import { Check, FileText, Search, Sparkles, Upload } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { parseResume, saveProfile } from '../../services/authApi'
import { useAuthStore } from '../../store/authStore'

const ALL_ROLES = [
  'Frontend',
  'Backend',
  'Full Stack',
  'Android',
  'DevOps',
  'DevSecOps',
  'Data Analyst',
  'AI Engineer',
  'AI and Data Scientist',
  'Data Engineer',
  'Machine Learning',
  'Product Design',
  'PostgreSQL',
  'iOS',
  'Blockchain',
  'QA',
  'Software Architect',
  'Cyber Security',
  'UX Design',
  'Technical Writer',
  'Game Developer',
  'Server Side Game Developer',
  'MLOps',
  'Product Manager',
  'Engineering Manager',
  'Developer Relations',
  'BI Analyst',
  'Network Engineer',
  'Forward Deployed Engineer',
]

export default function OnboardingWizard() {
  const user = useAuthStore(s => s.user)
  const updateUser = useAuthStore(s => s.updateUser)
  const nav = useNavigate()
  const fileRef = useRef()

  const [career, setCareer] = useState('Data Engineer')
  const [roleSearch, setRoleSearch] = useState('')
  const [experience, setExperience] = useState('Early career')
  const [resume, setResume] = useState(null)
  const [parsed, setParsed] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const filteredRoles = useMemo(() => {
    if (!roleSearch.trim()) return ALL_ROLES
    return ALL_ROLES.filter(r => r.toLowerCase().includes(roleSearch.toLowerCase()))
  }, [roleSearch])

  const upload = async file => {
    if (!file) return
    setResume(file)
    setError('')
    try {
      setParsed(await parseResume(file, { user_id: user?.id, career_target: career }))
    } catch (e) {
      setError(e.response?.data?.detail || 'Could not parse that file')
    }
  }

  const continuePath = async () => {
    setBusy(true)
    try {
      const profile = await saveProfile(user.id, {
        career_target: career,
        experience_level: experience,
        resume_text: parsed?.resume_text || '',
        skills: parsed?.skills || [],
      })
      updateUser({ ...user, career_target: career, skills: profile.skills || parsed?.skills || [] })
      nav('/assessment')
    } catch {
      updateUser({ ...user, career_target: career, skills: parsed?.skills || [] })
      nav('/assessment')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#172c4d,_#07111f_48%)] p-5">
      <div className="mx-auto max-w-3xl py-8">
        <div className="flex items-center gap-2 text-sky-300">
          <Sparkles size={18} />
          <b>EduPath setup</b>
        </div>
        <div className="mt-7">
          <p className="eyebrow">Step 1 of 2</p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Tell us where you’re headed.</h1>
          <p className="mt-3 text-slate-400">
            Select your target career from roadmap.sh's official 29 role roadmaps.
          </p>
        </div>

        <section className="card mt-8 p-5 sm:p-7">
          <div className="flex items-center justify-between gap-4">
            <label className="text-sm font-semibold text-slate-200">
              Career destination ({ALL_ROLES.length} roles)
            </label>
            <div className="relative w-48 sm:w-64">
              <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Filter roles..."
                value={roleSearch}
                onChange={e => setRoleSearch(e.target.value)}
                className="w-full rounded-lg border border-line bg-slate-900 py-1.5 pl-8 pr-3 text-xs text-slate-200 focus:border-sky-400 focus:outline-none"
              />
            </div>
          </div>

          <div className="mt-4 grid max-h-72 gap-2 overflow-y-auto sm:grid-cols-2 md:grid-cols-3 pr-1">
            {filteredRoles.map(track => (
              <button
                key={track}
                onClick={() => setCareer(track)}
                className={`flex items-center justify-between rounded-xl border p-3 text-left text-xs font-semibold transition-colors ${
                  career === track
                    ? 'border-sky-300 bg-sky-400/10 text-sky-200 shadow-md shadow-sky-500/10'
                    : 'border-line text-slate-400 hover:border-slate-500 hover:text-slate-200'
                }`}
              >
                <span>{track}</span>
                {career === track && <Check className="text-sky-300 shrink-0" size={15} />}
              </button>
            ))}
            {filteredRoles.length === 0 && (
              <p className="col-span-full py-6 text-center text-xs text-slate-500">
                No matching roles found.
              </p>
            )}
          </div>

          <label className="mt-6 block text-sm font-semibold">Experience level</label>
          <select className="field mt-2" value={experience} onChange={e => setExperience(e.target.value)}>
            <option>Early career</option>
            <option>1–3 years</option>
            <option>3–5 years</option>
            <option>5+ years</option>
          </select>
        </section>

        <section className="card mt-4 p-5 sm:p-7">
          <div className="flex items-start gap-3">
            <FileText className="mt-1 text-indigo-300" />
            <div>
              <h2 className="font-semibold">Make it sharper with your résumé</h2>
              <p className="mt-1 text-sm text-slate-400">
                Optional · PDF or TXT · your file is parsed and not retained.
              </p>
            </div>
          </div>

          <button
            onClick={() => fileRef.current.click()}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-sky-400/50 bg-sky-400/5 px-4 py-6 text-sm font-semibold text-sky-200 hover:bg-sky-400/10"
          >
            <Upload size={18} />
            {resume ? resume.name : 'Upload résumé'}
          </button>
          <input
            ref={fileRef}
            className="hidden"
            type="file"
            accept=".pdf,.txt"
            onChange={e => upload(e.target.files?.[0])}
          />

          {parsed && (
            <div className="mt-4 rounded-xl bg-emerald-400/10 p-4 text-sm">
              <p className="font-semibold text-emerald-300">Found {parsed.skills.length} relevant skills</p>
              <p className="mt-1 text-slate-400">
                {parsed.skills.join(' · ') || 'We’ll calibrate your profile through the diagnostic.'}
              </p>
            </div>
          )}

          {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
        </section>

        <button
          onClick={continuePath}
          disabled={busy}
          className="btn-primary mt-6 w-full sm:w-auto"
        >
          {busy ? 'Saving profile…' : 'Continue to diagnostic'} <Sparkles size={17} />
        </button>
      </div>
    </main>
  )
}
