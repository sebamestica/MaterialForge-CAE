import { AiAdapter } from './index';
import { modelConfig } from '../../config/model.config';

export class LmstudioAdapter implements AiAdapter {
  private endpoint = modelConfig.endpoints.lmstudio;

  async generate(prompt: string, context?: any): Promise<string> {
    const response = await fetch(`${this.endpoint}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: prompt }],
        temperature: modelConfig.temperature,
        max_tokens: modelConfig.maxTokens
      }),
    });

    if (!response.ok) {
      throw new Error(`LMStudio generation failed: ${response.status}`);
    }

    const data = await response.json();
    return data.choices?.[0]?.message?.content || "";
  }

  async stream(prompt: string, context: any, onToken: (token: string) => void): Promise<string> {
    const response = await fetch(`${this.endpoint}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: prompt }],
        temperature: modelConfig.temperature,
        max_tokens: modelConfig.maxTokens,
        stream: true
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`LMStudio stream setup failed: ${response.status}`);
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
        const cleanLine = line.replace(/^data: /, "").trim();
        if (!cleanLine || cleanLine === "[DONE]") continue;

        try {
          const parsed = JSON.parse(cleanLine);
          const content = parsed.choices?.[0]?.delta?.content;
          if (content) {
            accumulatedText += content;
            onToken(content);
          }
        } catch {
          // JSON line buffer parsing fallback
        }
      }
    }
    return accumulatedText;
  }

  async embed(text: string): Promise<number[]> {
    const response = await fetch(`${this.endpoint}/v1/embeddings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input: text
      }),
    });

    if (!response.ok) {
      throw new Error(`LMStudio embedding failed: ${response.status}`);
    }

    const data = await response.json();
    return data.data?.[0]?.embedding || [];
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.endpoint}/v1/models`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000)
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}
