export const modelConfig = {
  // Provider can be: 'ollama' | 'openai' | 'lmstudio' | 'local'
  provider: (process.env.NEXT_PUBLIC_AI_PROVIDER || 'ollama') as 'ollama' | 'openai' | 'lmstudio' | 'local',
  
  // Model name matching target provider (e.g. qwen2.5-coder:3b, gpt-4, etc.)
  modelName: process.env.NEXT_PUBLIC_AI_MODEL || 'qwen2.5-coder:3b',
  
  // Temperature settings for materials calculations (low value for engineering precision)
  temperature: 0.1,
  
  // Maximum response tokens to avoid overflow
  maxTokens: 2048,
  
  // API endpoints
  endpoints: {
    ollama: process.env.NEXT_PUBLIC_OLLAMA_API_URL || 'http://127.0.0.1:11434',
    openai: process.env.NEXT_PUBLIC_OPENAI_API_URL || 'https://api.openai.com/v1',
    lmstudio: process.env.NEXT_PUBLIC_LMSTUDIO_API_URL || 'http://127.0.0.1:1234',
    local: process.env.NEXT_PUBLIC_LOCAL_API_URL || 'http://127.0.0.1:8000',
  },
  
  // Optional authorization keys
  keys: {
    openai: process.env.NEXT_PUBLIC_OPENAI_API_KEY || '',
  }
};
