import { AiAdapter } from './index';
import { modelConfig } from '../../config/model.config';

export class OllamaAdapter implements AiAdapter {
  private endpoint = modelConfig.endpoints.ollama;

  async generate(prompt: string, context?: any): Promise<string> {
    const response = await fetch(`${this.endpoint}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: modelConfig.modelName,
        prompt: prompt,
        stream: false,
        options: { temperature: modelConfig.temperature }
      }),
    });

    if (!response.ok) {
      throw new Error(`Ollama generation failed with status: ${response.status}`);
    }

    const data = await response.json();
    return data.response;
  }

  async stream(prompt: string, context: any, onToken: (token: string) => void): Promise<string> {
    const response = await fetch(`${this.endpoint}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: modelConfig.modelName,
        prompt: prompt,
        stream: true,
        options: { temperature: modelConfig.temperature }
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Ollama stream setup failed with status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let accumulatedText = "";
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const parsed = JSON.parse(line);
          if (parsed.response) {
            accumulatedText += parsed.response;
            onToken(parsed.response);
          }
        } catch (e) {
          // JSON line buffer parsing fallback
        }
      }
    }
    return accumulatedText;
  }

  async embed(text: string): Promise<number[]> {
    const response = await fetch(`${this.endpoint}/api/embeddings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: modelConfig.modelName,
        prompt: text,
      }),
    });

    if (!response.ok) {
      throw new Error(`Ollama embedding generation failed: ${response.status}`);
    }

    const data = await response.json();
    return data.embedding;
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.endpoint}/api/tags`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000) // 3 seconds timeout
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}
