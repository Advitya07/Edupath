import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
export default function ProtectedRoute({ children }) { return useAuthStore(s => s.user) ? children : <Navigate to="/login" replace /> }
