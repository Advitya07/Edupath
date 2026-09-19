import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './ProtectedRoute'
import Login from '../pages/auth/Login'
import Register from '../pages/auth/Register'
import OnboardingWizard from '../pages/onboarding/OnboardingWizard'
import DiagnosticQuiz from '../pages/assessment/DiagnosticQuiz'
import Dashboard from '../pages/user/Dashboard'
import RoadmapPage from '../pages/user/RoadmapPage'
import AdminDashboard from '../pages/admin/AdminDashboard'
export default function AppRoutes() { return <Routes>
  <Route path="/login" element={<Login />} /><Route path="/register" element={<Register />} />
  <Route path="/onboarding" element={<ProtectedRoute><OnboardingWizard /></ProtectedRoute>} />
  <Route path="/assessment" element={<ProtectedRoute><DiagnosticQuiz /></ProtectedRoute>} />
  <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
  <Route path="/roadmap" element={<ProtectedRoute><RoadmapPage /></ProtectedRoute>} />
  <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
  <Route path="*" element={<Navigate to="/dashboard" replace />} />
</Routes> }
