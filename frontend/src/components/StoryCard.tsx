import { Bookmark, ExternalLink, Lightbulb, SearchX } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Story } from '../types'
import ScoreBadge from './ScoreBadge'

export default function StoryCard({story, onAction}:{story:Story; onAction?:(action:string, story:Story)=>void}) {
  return <article className="story-card">
    <div className="story-main">
      <div className="meta-line"><span className={`source-pill ${story.source}`}>{story.source}</span>{story.is_demo && <span className="demo-pill">DEMO DATA</span>}<span>@{story.author || 'ẩn danh'}</span><span>·</span><span>{new Date(story.created_at || story.discovered_at).toLocaleString('vi-VN')}</span></div>
      <Link to={`/stories/${story.id}`} className="story-title">{story.title}</Link>
      <p>{story.text.length > 240 ? `${story.text.slice(0,240)}…` : story.text}</p>
      <div className="tag-row"><span>Từ khóa: <b>{story.query}</b></span>{story.tags.slice(0,3).map(tag => <span key={tag}>#{tag}</span>)}</div>
      <div className="card-actions">
        <Link className="btn secondary small" to={`/stories/${story.id}`}>Mở</Link>
        <button className="btn ghost small" onClick={() => onAction?.('save',story)}><Bookmark size={15}/> Lưu</button>
        <button className="btn ghost small danger" onClick={() => onAction?.('reject',story)}><SearchX size={15}/> Loại</button>
        <button className="btn ghost small" onClick={() => onAction?.('idea',story)}><Lightbulb size={15}/> Tạo ý tưởng</button>
        <a className="btn ghost small" href={story.source_url} target="_blank" rel="noreferrer"><ExternalLink size={15}/> Nguồn</a>
      </div>
    </div>
    <div className="story-score"><ScoreBadge score={story.total_score}/><div className="mini-scores"><span>Kinh dị <b>{story.score?.horror_score ?? 0}</b></span><span>Tò mò <b>{story.score?.curiosity_score ?? 0}</b></span><span>Cú lật <b>{story.score?.twist_score ?? 0}</b></span><span>Cảm xúc <b>{story.score?.emotion_score ?? 0}</b></span></div></div>
  </article>
}

