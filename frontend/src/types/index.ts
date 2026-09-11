export type Score = {
  hook_score: number; curiosity_score: number; horror_score: number; twist_score: number;
  emotion_score: number; story_structure_score: number; short_video_fit_score: number;
  source_quality_score: number; penalties: string[]; reasons: string[]
}

export type Story = {
  id: number; external_id: string; source: string; source_url: string; author?: string;
  author_url?: string; text: string; title: string; created_at?: string; discovered_at: string;
  language?: string; query: string; tags: string[]; reply_count?: number; like_count?: number;
  share_count?: number; view_count?: number; media_type?: string; status: string; is_demo: boolean;
  duplicate_of_id?: number; duplicate_similarity?: number; notes: string; total_score: number; score?: Score
}

export type ContentIdea = {
  id: number; source_story_id: number; working_title: string; premise: string; hook_1: string;
  hook_2: string; hook_3: string; story_outline: string; suggested_video_length: number;
  ending_question: string; visual_background: string; story_type: string; category: string;
  status: string; notes: string; created_at: string; source?: string; source_url?: string;
  story_score?: number; is_demo?: boolean
}

export type Keyword = {id:number; phrase:string; category:string; language:string; enabled:boolean; queries_run:number; stories_found:number; saved_rate:number; average_score:number}

