import { Bell, GraduationCap, LogOut } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
export default function Navbar() {
  const { user, logout } = useAuthStore()
  return <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-line/80 bg-slate-900/80 px-5 md:px-8 backdrop-blur-md">
    <div className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-xl bg-sky-400 text-slate-950 shadow-md shadow-sky-500/20"><GraduationCap size={21}/></div><span className="font-bold tracking-tight text-white">Edu<span className="text-sky-300">Path</span></span></div>
    <div className="flex items-center gap-3"><button className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"><Bell size={18}/></button><div className="hidden text-right text-xs sm:block"><p className="font-semibold text-slate-200">{user?.name || 'Learner'}</p><p className="text-slate-400">{user?.career_target || 'Learning path'}</p></div><button onClick={logout} title="Sign out" className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"><LogOut size={18}/></button></div>
  </header>
}
