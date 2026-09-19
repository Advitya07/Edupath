import { Bell, GraduationCap, LogOut } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
export default function Navbar() {
  const { user, logout } = useAuthStore()
  return <header className="flex h-16 items-center justify-between border-b border-line bg-slate-950/40 px-5 md:px-8">
    <div className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-xl bg-sky-400 text-slate-950"><GraduationCap size={21}/></div><span className="font-bold tracking-tight">Edu<span className="text-sky-300">Path</span></span></div>
    <div className="flex items-center gap-3"><button className="rounded-lg p-2 text-slate-400 hover:bg-slate-800"><Bell size={18}/></button><div className="hidden text-right text-xs sm:block"><p className="font-semibold text-slate-200">{user?.name || 'Learner'}</p><p className="text-slate-500">{user?.career_target || 'Learning path'}</p></div><button onClick={logout} title="Sign out" className="rounded-lg p-2 text-slate-400 hover:bg-slate-800"><LogOut size={18}/></button></div>
  </header>
}
