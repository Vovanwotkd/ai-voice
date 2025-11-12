import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import ChatPage from './pages/ChatPage'
import PromptsPage from './pages/PromptsPage'
import HistoryPage from './pages/HistoryPage'
import DashboardPage from './pages/DashboardPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/chat" replace />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="prompts" element={<PromptsPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
      </Route>
    </Routes>
  )
}

export default App
