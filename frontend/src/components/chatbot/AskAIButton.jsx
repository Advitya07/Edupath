import { Sparkles } from 'lucide-react'
import { useState } from 'react'
import ChatWindow from './ChatWindow'
export default function AskAIButton() { const [open,setOpen]=useState(false); return <>{open&&<ChatWindow onClose={()=>setOpen(false)}/>}<button onClick={()=>setOpen(true)} className="fixed bottom-6 right-6 z-20 inline-flex items-center gap-2 rounded-full bg-indigo-400 px-5 py-3 text-sm font-bold text-slate-950 shadow-glow transition hover:bg-indigo-300"><Sparkles size={17}/> Ask AI Mentor</button></> }
