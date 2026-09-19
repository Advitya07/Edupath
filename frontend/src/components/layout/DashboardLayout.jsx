import Navbar from './Navbar'
import Sidebar from './Sidebar'
import AskAIButton from '../chatbot/AskAIButton'
export default function DashboardLayout({ children }) { return <div className="min-h-screen"><Navbar/><div className="flex"><Sidebar/><main className="min-w-0 flex-1 p-5 md:p-8">{children}</main></div><AskAIButton/></div> }
