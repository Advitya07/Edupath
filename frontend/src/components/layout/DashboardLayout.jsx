import Navbar from './Navbar'
import Sidebar from './Sidebar'
import AskAIButton from '../chatbot/AskAIButton'
export default function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen flex flex-col bg-ink">
      <Navbar />
      <div className="flex flex-1 min-h-[calc(100vh-4rem)]">
        <Sidebar />
        <main className="min-w-0 flex-1 p-5 md:p-8">{children}</main>
      </div>
      <AskAIButton />
    </div>
  )
}
