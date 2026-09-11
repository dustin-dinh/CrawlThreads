export default function ScoreBadge({score, label}:{score:number; label?:string}) {
  const tone = score >= 70 ? 'high' : score >= 45 ? 'mid' : 'low'
  return <span className={`score-badge ${tone}`}><strong>{score}</strong>{label && <small>{label}</small>}</span>
}

