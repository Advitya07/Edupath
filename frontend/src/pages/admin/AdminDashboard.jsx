import { useEffect, useState } from 'react'
import DashboardLayout from '../../components/layout/DashboardLayout'
import StatsOverview from '../../components/admin/StatsOverview'
import UserTable from '../../components/admin/UserTable'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
export default function AdminDashboard(){const me=useAuthStore(s=>s.user);const [data,setData]=useState({stats:{learners:0,assessments:0,average_mastery:0,at_risk:0},users:[]}),[error,setError]=useState('');useEffect(()=>{api.get('/admin/overview').then(r=>setData(r.data)).catch(()=>{setError('Demo API is unavailable; showing the signed-in learner.');setData({stats:{learners:1,assessments:0,average_mastery:0,at_risk:0},users:me?[me]:[]})})},[]);return <DashboardLayout><p className="eyebrow">Admin workspace</p><h1 className="mt-2 text-3xl font-bold">Learning health at a glance</h1><p className="mt-2 text-slate-400">Track participation, calibrated mastery, and learners who need an intervention.</p>{error&&<p className="mt-5 rounded-xl bg-amber-400/10 p-3 text-sm text-amber-200">{error}</p>}<div className="mt-7"><StatsOverview stats={data.stats}/></div><div className="mt-5"><UserTable users={data.users}/></div></DashboardLayout>}
