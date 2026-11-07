
export type PageStatus = 'DRAFT' | 'GENERATING_DESCRIPTION' | 'DESCRIPTION_GENERATED' | 'QUEUED' | 'GENERATING' | 'COMPLETED' | 'FAILED';


export type ProjectStatus = 'DRAFT' | 'OUTLINE_GENERATED' | 'DESCRIPTIONS_GENERATED' | 'COMPLETED';


export interface OutlineContent {
  title: string;
  points: string[];
}


export type DescriptionContent =
  | {
      
      text: string;
      extra_fields?: Record<string, string>;
      layout_suggestion?: string; 
    }
  | {
      
      title: string;
      text_content: string[];
      extra_fields?: Record<string, string>;
      layout_suggestion?: string; 
    };


export interface ImageVersion {
  version_id: string;
  page_id: string;
  image_path: string;
  image_url?: string;
  version_number: number;
  is_current: boolean;
  created_at?: string;
}


export type TemplateMode = 'single' | 'multi';


export type TemplateSelectionSource = 'manual' | 'auto' | 'batch_apply';


export type TemplateAnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed';


export interface TemplateRegion {
  name: string;
  position: string;
  size: string;
}


export interface TemplateAnalysis {
  template_role: string;
  layout_structure: string;
  content_capacity: 'low' | 'medium' | 'high';
  text_regions: TemplateRegion[];
  image_regions: TemplateRegion[];
  visual_density: 'low' | 'medium' | 'high';
  style_keywords: string[];
  color_palette: string[];
  notes: string;
}


export interface TemplateAsset {
  id: string;
  image_url: string;
  thumb_url: string | null;
  analysis_status: TemplateAnalysisStatus;
  analysis_json: TemplateAnalysis | null;
  analysis_notes: string | null;
  analysis_error: string | null;
  user_label: string | null;
  user_edited_analysis: boolean;
  source: 'upload' | 'pdf_split' | 'system_preset';
  sort_order: number;
  referenced_page_ids?: string[];
}


export interface Page {
  page_id: string;  
  id?: string;      
  order_index: number;
  part?: string; 
  outline_content: OutlineContent | null;
  description_content?: DescriptionContent;
  narration_text?: string; 
  generated_image_url?: string; 
  generated_image_path?: string; 
  status: PageStatus;
  created_at?: string;
  updated_at?: string;
  image_versions?: ImageVersion[]; 
  
  template_asset_id?: string | null;
  template_style_text?: string | null;
  template_selection_source?: TemplateSelectionSource | null;
  template_match_reason?: string | null;
  template_match_confidence?: number | null;
}

export interface NarrationConfig {
  speaker_persona: string;
  target_audience: string;
  speech_tone: string;
  presentation_topic: string;
  min_words: number;
  max_words: number;
}


export type ExportExtractorMethod = 'mineru' | 'hybrid';


export type ExportInpaintMethod = 'generative' | 'baidu' | 'hybrid';


export interface Project {
  project_id: string;  
  id?: string;         
  project_title?: string;
  idea_prompt: string;
  outline_text?: string;  
  description_text?: string;  
  extra_requirements?: string; 
  outline_requirements?: string; 
  description_requirements?: string; 
  creation_type?: string;
  template_image_url?: string; 
  template_image_path?: string; 
  template_style?: string; 
  template_mode?: TemplateMode; 
  
  export_extractor_method?: ExportExtractorMethod; 
  export_inpaint_method?: ExportInpaintMethod; 
  export_allow_partial?: boolean; 
  enable_icon_subject_extraction?: boolean; 
  image_aspect_ratio?: string; 
  status: ProjectStatus;
  pages: Page[];
  created_at: string;
  updated_at: string;
}

/**
 * 
 */
export interface Material {
  id: string;
  project_id?: string | null;
  filename: string;
  url: string;
  relative_path: string;
  created_at: string;
  updated_at: string;
  prompt?: string;
  original_filename?: string | null;
  source_filename?: string;
  name?: string;
  caption?: string | null;
}


export type TaskStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';


export interface Task {
  task_id: string;
  id?: string; 
  task_type?: string;
  status: TaskStatus;
  progress?: {
    total: number;
    completed: number;
    failed?: number;
    [key: string]: any; 
  };
  error_message?: string;
  result?: any;
  error?: string; 
  created_at?: string;
  completed_at?: string;
}


export interface CreateProjectRequest {
  creation_type?: 'idea' | 'outline' | 'descriptions' | 'blank';
  idea_prompt?: string;
  outline_text?: string;
  description_text?: string;
  template_image?: File;
  template_style?: string;
  image_aspect_ratio?: string;
}


export interface ApiResponse<T = any> {
  success?: boolean;
  data?: T;
  task_id?: string;
  message?: string;
  error?: string;
}


export interface Settings {
  id: number;
  ai_provider_format: string;
  api_base_url?: string;
  api_key_length: number;
  image_resolution: string;
  image_quality?: string;
  image_aspect_ratio: string;
  max_description_workers: number;
  max_image_workers: number;
  text_model?: string;
  image_model?: string;
  mineru_api_base?: string;
  mineru_token_length: number;
  image_caption_model?: string;
  output_language: 'zh' | 'en' | 'ja' | 'auto';
  
  description_generation_mode: 'streaming' | 'parallel';
  
  description_extra_fields?: string[];
  image_prompt_extra_fields?: string[];
  
  enable_text_reasoning: boolean;
  text_max_output_tokens: number;
  text_thinking_budget: number;
  enable_image_reasoning: boolean;
  image_thinking_budget: number;
  enable_image_quality_control: boolean;
  baidu_api_key_length: number;
  
  text_model_source?: string;
  image_model_source?: string;
  image_caption_model_source?: string;
  lazyllm_api_keys_info?: Record<string, number>;  // {vendor: key_length}
  // Per-model API credentials (for gemini/openai per-model overrides)
  text_api_key_length: number;
  text_api_base_url?: string;
  image_api_key_length: number;
  image_api_base_url?: string;
  image_caption_api_key_length: number;
  image_caption_api_base_url?: string;
  // OpenAI image API protocol
  openai_image_api_protocol?: string;
  // OpenAI Codex OAuth
  openai_oauth_connected: boolean;
  openai_oauth_account_id?: string | null;
  // ElevenLabs TTS
  elevenlabs_enabled: boolean;
  elevenlabs_api_key_length: number;
  elevenlabs_voice_id?: string;
  created_at?: string;
  updated_at?: string;
}