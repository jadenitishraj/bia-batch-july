// SDK transport test only. This stand-in does not interpret natural language.
const http = require('http');
http.createServer(async (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  if (req.method !== 'POST' || !req.url.endsWith('/converse')) {
    res.writeHead(501);
    return res.end(JSON.stringify({message: 'Unmodeled endpoint'}));
  }
  const body = req.body;
  if (!Array.isArray(body.messages) || body.toolConfig?.tools.length !== 3) {
    res.writeHead(400);
    return res.end(JSON.stringify({message: 'Expected messages and three tools'}));
  }
  const user = body.messages.filter(item => item.role === 'user' && item.content[0]?.text).at(-1).content[0].text;
  if (user === 'throttle-test') {
    res.setHeader('x-amzn-errortype', 'ThrottlingException');
    res.writeHead(429);
    return res.end(JSON.stringify({message: 'Simulated throttling'}));
  }
  let content = [{text: 'Trip action completed in the simulation.'}];
  let stopReason = 'end_turn';
  if (!body.messages.at(-1).content[0].toolResult) {
    let name = 'create_trip';
    let input = {title: 'Simulated Jaipur', destination: 'Jaipur', days: 3,
      travelers: 2, budget: 20000, plan: 'Day 1 — Explore the old city.'};
    const context = body.system[0].text.split('saved trips (up to 50):\n')[1];
    const trips = JSON.parse(context);
    if (user === 'update-test') {name = 'update_trip'; input = {trip_id: trips[0].id, budget: 25000};}
    if (user === 'delete-test') {name = 'delete_trip'; input = {trip_id: trips[0].id};}
    content = [{toolUse: {toolUseId: 'simulated-call', name, input}}];
    stopReason = 'tool_use';
  }
  res.writeHead(200);
  res.end(JSON.stringify({output: {message: {role: 'assistant', content}}, stopReason,
    usage: {inputTokens: 1, outputTokens: 1, totalTokens: 2}, metrics: {latencyMs: 1}}));
}).listen(process.env.PORT || 4519);
