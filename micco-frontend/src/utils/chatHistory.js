/** Only completed question/answer pairs belong in the next model request. */
export function buildChatHistory(messages, limit = 10) {
  const pairs = [];
  let question = null;

  for (const message of messages) {
    if (message.role === 'user') {
      question = !message.streaming && !message.streamError && message.content?.trim()
        ? { role: 'user', content: message.content }
        : null;
    } else if (message.role === 'assistant') {
      if (question && !message.streaming && !message.streamError && message.content?.trim()) {
        pairs.push(question, { role: 'assistant', content: message.content });
      }
      question = null;
    }
  }

  const turnCount = 2 * Math.floor(limit / 2);
  return turnCount > 0 ? pairs.slice(-turnCount) : [];
}
