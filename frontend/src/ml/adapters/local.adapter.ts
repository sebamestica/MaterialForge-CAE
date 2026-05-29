import { AiAdapter } from './index';
import { modelConfig } from '../../config/model.config';

export class LocalAdapter implements AiAdapter {
  private endpoint = modelConfig.endpoints.local;

  async generate(prompt: string, context?: any): Promise<string> {
    const response = await fetch(`${this.endpoint}/api/copilot/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: prompt }],
        config: context || {}
      }),
    });

    if (!response.ok) {
      throw new Error(`Local backend generation failed: ${response.status}`);
    }

    // In our backend, the chat endpoint is a streaming response of JSON lines
    const text = await response.text();
    const lines = text.split('\n');
    let accumulatedText = "";

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const parsed = JSON.parse(line);
        if (parsed.type === 'token') {
          accumulatedText += parsed.content;
        } else if (parsed.type === 'final') {
          accumulatedText = parsed.response?.analysis?.text || accumulatedText;
        }
      } catch {
        // Fallback for parsing chunks
      }
    }
    return accumulatedText;
  }

  async stream(prompt: string, context: any, onToken: (token: string) => void): Promise<string> {
    const response = await fetch(`${this.endpoint}/api/copilot/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: prompt }],
        config: context || {}
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Local backend stream setup failed: ${response.status}`);
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
          if (parsed.type === 'token') {
            accumulatedText += parsed.content;
            onToken(parsed.content);
          } else if (parsed.type === 'final') {
            const finalContent = parsed.response?.analysis?.text || accumulatedText;
            accumulatedText = finalContent;
          }
        } catch {
          // JSON parsing chunk fallback
        }
      }
    }
    return accumulatedText;
  }

  async embed(text: string): Promise<number[]> {
    // Forward embed request to local RAG ingestion endpoints if available
    return [];
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.endpoint}/api/copilot/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000)
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}
