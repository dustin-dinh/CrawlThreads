import { ArrowRight, Download } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import StoryCard from '../components/StoryCard'
import { Empty, ErrorBox, Loading } from '../components/States'
import { api } from '../services/api'
import type { Story } from '../types'

type Data={counts:Record<string,number>;top_stories:Story[];top_keywords:{name:string;count:number;average_score:number}[];top_sources:{name:string;count:number;average_score:number}[]}
const labels:Record<string,string>={stories_today:'Truyện hôm nay',unreviewed:'Chưa duyệt',saved:'Đã lưu',rejected:'Đã loại',high_potential:'Tiềm năng cao',content_ideas:'Ý tưởng'}

export default function Dashboard(){
  const [data,setData]=useState<Data|null>(null);const[error,setError]=useState('')
  const load=()=>api.get<Data>('/dashboard').then(setData).catch(e=>setError(e.message));useEffect(load,[])
  const action=async(a:string,s:Story)=>{if(a==='idea')await api.post(`/stories/${s.id}/idea`);else await api.patch(`/stories/${s.id}`,{status:a==='save'?'SAVED':'REJECTED'});load()}
  if(!data&&!error)return <Loading/>; if(error)return <ErrorBox message={error}/>
  return <><PageHeader eyebrow="Trung tâm nghiên cứu" title="Tổng quan" description="Những tín hiệu đáng chú ý nhất trong kho truyện của bạn." actions={<a className="btn ghost" href="/api/export/stories.csv"><Download size={16}/> Xuất CSV</a>}/>
    <div className="grid stats-grid">{Object.entries(data!.counts).map(([key,value])=><div className="stat-card" key={key}><span>{labels[key]}</span><strong>{value}</strong></div>)}</div>
    <div className="grid dashboard-grid"><section><div className="panel-title"><h2>Top 10 ứng viên hôm nay</h2><Link to="/stories">Xem tất cả <ArrowRight size={13}/></Link></div><div className="story-list">{data!.top_stories.length?data!.top_stories.map(s=><StoryCard key={s.id} story={s} onAction={action}/>):<Empty/>}</div></section>
      <aside className="grid"><div className="panel"><div className="panel-title"><h3>Từ khóa hiệu quả</h3><span>điểm TB</span></div><div className="rank-list">{data!.top_keywords.map((k,i)=><div className="rank-item" key={k.name}><div><span>{i+1}. {k.name}</span><small>{k.count} kết quả</small></div><b>{k.average_score}</b></div>)}{!data!.top_keywords.length&&<Empty detail="Chạy demo search để tạo thống kê."/>}</div></div>
      <div className="panel"><div className="panel-title"><h3>Nguồn nổi bật</h3><span>điểm TB</span></div><div className="rank-list">{data!.top_sources.map(k=><div className="rank-item" key={k.name}><div><span>{k.name}</span><small>{k.count} câu chuyện</small></div><b>{k.average_score}</b></div>)}</div></div></aside>
    </div></>
}

