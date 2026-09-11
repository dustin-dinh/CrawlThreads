export function Loading() { return <div className="state-box"><div className="spinner"/><p>Đang tải dữ liệu…</p></div> }
export function Empty({title='Chưa có dữ liệu', detail='Hãy bắt đầu một lượt khám phá mới.'}:{title?:string;detail?:string}) { return <div className="state-box"><span className="empty-glyph">◇</span><h3>{title}</h3><p>{detail}</p></div> }
export function ErrorBox({message}:{message:string}) { return <div className="alert error">{message}</div> }

