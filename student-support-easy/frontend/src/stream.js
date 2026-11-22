// The HTTP reply arrives as little text pieces, not one finished answer.
export async function streamReply(message, history, onText) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history })
  })
  if (!response.ok) throw Error('The chat server could not answer.')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let unfinished = ''
  while (true) {
    const { value, done } = await reader.read()
    unfinished += decoder.decode(value, { stream: !done })
    const packets = unfinished.split('\n\n')
    unfinished = packets.pop()
    for (const packet of packets) {
      if (packet.startsWith('data: ')) {
        onText(JSON.parse(packet.slice(6)).text)
      }
    }
    if (done) break
  }
}
