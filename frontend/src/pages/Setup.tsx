import { Check, ChevronLeft, ChevronRight, Database, KeyRound, Reddit, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../services/api'

type Settings = {threads_configured:boolean;reddit_configured:boolean;ai_enabled:boolean;database_url:string}
const steps = [
  {title:'Cơ sở dữ liệu', icon:Database, body:'SQLite sẽ lưu toàn bộ từ khóa, kết quả, đánh giá và ý tưởng ngay trên máy. Không cần máy chủ bên ngoài.'},
  {title:'Threads API', icon:KeyRound, body:'Tìm kiếm công khai cần THREADS_ACCESS_TOKEN với quyền threads_basic và threads_keyword_search. Bạn có thể thêm sau trong file .env.'},
  {title:'Reddit API', icon:Reddit, body:'Tạo Reddit script app để lấy REDDIT_CLIENT_ID và REDDIT_CLIENT_SECRET. Ứng dụng chỉ dùng OAuth API chính thức.'},
  {title:'Phân tích AI', icon:Sparkles, body:'AI hoàn toàn tùy chọn. Mặc định ứng dụng dùng bộ chấm điểm minh bạch chạy cục bộ.'},
  {title:'Hoàn tất', icon:Check, body:'Demo mode đã sẵn sàng. Bạn có thể chạy lượt tìm kiếm thử mà không cần bất kỳ khóa API nào.'},
]

export default function Setup({onComplete}:{onComplete:()=>void}) {
  const [step,setStep] = useState(0); const [settings,setSettings] = useState<Settings|null>(null); const [busy,setBusy] = useState(false)
  useEffect(()=>{api.get<Settings>('/settings').then(setSettings)},[])
  const finish = async()=>{setBusy(true);await api.patch('/settings',{setup_complete:true,demo_mode:true});onComplete()}
  const CurrentIcon=steps[step].icon
  return <div className="setup-shell"><div className="setup-card">
    <div className="setup-brand"><span className="brand-mark">LẠ</span><h1>Tôi Kể Chuyện Lạ</h1><p>Thiết lập Story Miner lần đầu</p></div>
    <div className="steps">{steps.map((_,i)=><span key={i} className={`step ${i<=step?'done':''}`}/>)}</div>
    <section className="setup-content"><CurrentIcon size={32} color="#c7a462"/><span className="eyebrow">Bước {step+1} / {steps.length}</span><h2>{steps[step].title}</h2><p>{steps[step].body}</p>
      {step===0&&<div className="notice">Vị trí: <code>{settings?.database_url || '…/story_miner.db'}</code></div>}
      {step===1&&<div className={settings?.threads_configured?'alert success':'notice'}>{settings?.threads_configured?'Threads đã được cấu hình.':'Threads chưa được cấu hình — ứng dụng vẫn chạy bình thường.'}</div>}
      {step===2&&<div className={settings?.reddit_configured?'alert success':'notice'}>{settings?.reddit_configured?'Reddit đã được cấu hình.':'Reddit chưa được cấu hình — có thể bỏ qua.'}</div>}
      {step===3&&<div className="notice">Trạng thái AI: {settings?.ai_enabled?'Đang bật':'Đang tắt (khuyến nghị khi mới dùng)'}</div>}
      {step===4&&<div className="copyright-note">Luôn kiểm tra nguồn và viết lại nội dung trước khi xuất bản. Story Miner không tự động đăng nội dung.</div>}
    </section>
    <div className="setup-actions"><button className="btn ghost" disabled={step===0} onClick={()=>setStep(step-1)}><ChevronLeft size={16}/> Quay lại</button>{step<4?<button className="btn primary" onClick={()=>setStep(step+1)}>Tiếp tục <ChevronRight size={16}/></button>:<button className="btn primary" disabled={busy} onClick={finish}><Check size={16}/> {busy?'Đang lưu…':'Vào ứng dụng'}</button>}</div>
  </div></div>
}

