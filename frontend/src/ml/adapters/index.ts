import { modelConfig } from '../../config/model.config';
import { OllamaAdapter } from './ollama.adapter';
import { OpenaiAdapter } from './openai.adapter';
import { LmstudioAdapter } from './lmstudio.adapter';
import { LocalAdapter } from './local.adapter';

export interface AiAdapter {
  /**
   * Generates a text response from the active AI model.
   * @param prompt The prompt to execute.
   * @param context Additional metadata context (e.g. printer config, CAD parameters).
   */
  generate(prompt: string, context?: any): Promise<string>;

  /**
   * Streams token-by-token text generation from the model.
   * @param prompt The prompt to execute.
   * @param context Additional metadata context.
   * @param onToken Callback executed when a new token is received.
   */
  stream(prompt: string, context: any, onToken: (token: string) => void): Promise<string>;

  /**
   * Generates embeddings for the provided text.
   * @param text The text chunk.
   */
  embed(text: string): Promise<number[]>;

  /**
   * Verifies connection to the LLM backend.
   */
  healthCheck(): Promise<boolean>;
}

export * from './ollama.adapter';
export * from './openai.adapter';
export * from './lmstudio.adapter';
export * from './local.adapter';

export function getActiveAdapter(): AiAdapter {
  const provider = modelConfig.provider;
  switch (provider) {
    case 'openai':
      return new OpenaiAdapter();
    case 'lmstudio':
      return new LmstudioAdapter();
    case 'local':
      return new LocalAdapter();
    case 'ollama':
    default:
      return new OllamaAdapter();
  }
}
