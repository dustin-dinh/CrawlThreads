import { BarChart3, BookOpenText, Compass, Database, FlaskConical, History, LayoutDashboard, Lightbulb, Menu, Settings2, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

const nav = [
  ['/', 'Tổng quan', LayoutDashboard],
  ['/discover', 'Khám phá', Compass],
  ['/jobs', 'Lịch sử crawl', History],
  ['/stories', 'Kho truyện', BookOpenText],
  ['/backlog', 'Ý tưởng nội dung', Lightbulb],
  ['/keywords', 'Từ khóa', FlaskConical],
  ['/sources', 'Nguồn dữ liệu', Database],
  ['/analytics', 'Phân tích', BarChart3],
  ['/settings', 'Cài đặt', Settings2],
] as const

export default function Layout() {
  const [open, setOpen] = useState(false)
  return <div className="app-shell">
    <button className="mobile-menu" onClick={() => setOpen(!open)} aria-label="Mở menu">{open ? <X/> : <Menu/>}</button>
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="logo"><span className="brand-mark">LẠ</span><div><strong>TÔI KỂ CHUYỆN LẠ</strong><small>STORY MINER</small></div></div>
      <nav>{nav.map(([path,label,Icon]) => <NavLink key={path} to={path} end={path === '/'} onClick={() => setOpen(false)}><Icon size={18}/><span>{label}</span></NavLink>)}</nav>
      <div className="sidebar-note"><span className="status-dot"/> Local-first · Dữ liệu của bạn</div>
    </aside>
    <main className="main"><Outlet /></main>
  </div>
}

