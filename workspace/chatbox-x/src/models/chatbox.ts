export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export const OLLAMA_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_OLLAMA_URL || 'http://localhost:11434',
  model: 'gemma4:e2b',
};

/**
 * Stream responses directly from the local Ollama instance
 */
export async function* streamOllamaChat(
  messages: ChatMessage[],
  signal?: AbortSignal
): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${OLLAMA_CONFIG.baseUrl}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: OLLAMA_CONFIG.model,
      messages: messages,
      stream: true,
    }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Ollama connection failed: ${response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const json = JSON.parse(line);
        if (json.message && json.message.content) {
          yield json.message.content;
        }
      } catch (e) {
        // partial chunk handling
      }
    }
  }
}
