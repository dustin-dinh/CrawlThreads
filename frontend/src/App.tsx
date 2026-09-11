import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { api } from './services/api'
import Layout from './components/Layout'
import Setup from './pages/Setup'
import Dashboard from './pages/Dashboard'
import Discover from './pages/Discover'
import SearchJobs from './pages/SearchJobs'
import Inbox from './pages/Inbox'
import StoryDetail from './pages/StoryDetail'
import Backlog from './pages/Backlog'
import Keywords from './pages/Keywords'
import Sources from './pages/Sources'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'

type Bootstrap = {setup_complete:boolean; demo_mode:boolean; sources:unknown[]; notice:string}

export default function App() {
  const [bootstrap, setBootstrap] = useState<Bootstrap | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { api.get<Bootstrap>('/bootstrap').then(setBootstrap).catch(e => setError(e.message)) }, [])
  if (error) return <div className="fatal"><h1>Không thể khởi động</h1><p>{error}</p><code>Hãy kiểm tra logs/app.log</code></div>
  if (!bootstrap) return <div className="boot"><span className="brand-mark">LẠ</span><p>Đang mở kho chuyện…</p></div>
  if (!bootstrap.setup_complete) return <Setup onComplete={() => setBootstrap({...bootstrap, setup_complete:true})} />
  return <Routes>
    <Route element={<Layout />}>
      <Route index element={<Dashboard />} />
      <Route path="discover" element={<Discover />} />
      <Route path="jobs" element={<SearchJobs />} />
      <Route path="stories" element={<Inbox />} />
      <Route path="stories/:id" element={<StoryDetail />} />
      <Route path="backlog" element={<Backlog />} />
      <Route path="keywords" element={<Keywords />} />
      <Route path="sources" element={<Sources />} />
      <Route path="analytics" element={<Analytics />} />
      <Route path="settings" element={<Settings />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Route>
  </Routes>
}

