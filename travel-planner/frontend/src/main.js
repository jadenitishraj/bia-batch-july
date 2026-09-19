import { setupDocuments } from './documents';
import './style.css';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const icons = {
 plus: '<path d="M12 5v14M5 12h14"/>',
 arrow: '<path d="M12 19V5m-6 6 6-6 6 6"/>',
 compass: '<circle cx="12" cy="12" r="9"/><path d="m16 8-3 5-5 3 3-5z"/>',
 plane: '<path d="m22 2-7 20-4-9-9-4 20-7ZM11 13 22 2"/>',
 bed: '<path d="M3 18V7m18 11V9H3m0 5h18M7 9V5h10v4"/>',
 sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1"/>',
 document: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
 check: '<path d="m5 12 4 4L19 6"/>',
};
const icon = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] || icons.compass}</svg>`;
const examples = [
 ['The Singapore long weekend', 'Four days of food, culture & city views', 'Plan a 4-day Singapore trip from Mumbai for two people. Mid-budget. Avoid red-eye flights. Prefer food, city views and cultural sites. Keep hotel budget under 45000 rupees.', 'plane'],
 ['A trip for your taste buds', 'Local flavours, without the big budget', 'Plan a 3-day Singapore trip from Bangalore for one person. Focus on food and culture. Choose the cheapest flight and a budget hotel.', 'sun'],
 ['Just find me a flight', 'A simpler way to get there', 'I only need flights from Delhi to Singapore under 32000 rupees.', 'compass'],
 ['Check the meeting details', 'Find a fact in the demo document', 'According to travel-planner-demo.md, where and when does the demo walking group meet, and what is its reference code? Cite the source filename.', 'document', true],
 ['Who made the glass clocks?', 'Explore the Veridia document', 'According to the_glass_clocks_of_veridia.pdf, who carved the glass clocks of Veridia? Answer using only the uploaded document and cite the source filename.', 'document', true],
 ['A flight, plus my document notes', 'Try travel planning and RAG together', 'Find flights only from Delhi to Singapore under 32000 rupees. Also append the walking group meeting details and recommendations from my uploaded travel-planner-demo.md document, with the source filename.', 'document', true],
];
let busy = false;
let controller;
let lastAnswer = '';
const labels = {documents:'Finding answers in your documents',manager:'Understanding your trip', flight_agent:'Finding your flight', hotel_agent:'Finding your stay', activity_agent:'Planning your days', synthesis:'Putting it all together', critic:'Checking the details', revision:'Adding the finishing touches'};
const names = {documents:'Document excerpts',manager:'Trip manager',flight_agent:'Flight specialist',hotel_agent:'Hotel specialist',activity_agent:'Activity specialist',synthesis:'First draft',critic:'Plan review',revision:'Final revision'};

document.querySelector('#app').innerHTML = `
<aside class="sidebar">
 <a class="brand" href="/">${icon('compass')}<span>travel planner<span class="brand-dot">.</span></span></a>
 <button class="new-trip">${icon('plus')}<span>New trip</span><kbd>↗</kbd></button>
 <div class="sidebar-label">YOUR TRAVEL STUDIO</div>
 <div class="nav-active">${icon('compass')} Trip planner</div>
 <div class="side-note"><span class="little-star">✳</span><h3>Good trips start<br>with a little curiosity.</h3><p>You bring the idea.<br>Your agent team handles the details.</p></div>
 <div class="sidebar-bottom"><span class="avatar">Y</span><div>Your personal travel studio<small>Powered by a team of AI agents</small></div></div>
</aside>
<main>
 <header><span>Trip planner <span class="header-slash">/</span> <span class="muted">A world of possibilities</span></span><span class="demo-badge"><i></i> Notebook demo</span></header>
 <div class="workspace">
  <section class="welcome"><div class="eyebrow"><span>✳</span> LESS PLANNING. MORE POSSIBILITY.</div><h1>Where shall we go?</h1><p>A rough idea is all you need. Let’s turn it into a thoughtful trip.</p></section>

  <div class="composer-dock"><form id="composer"><label class="sr-only" for="request">Describe your trip</label><textarea id="request" rows="3" maxlength="4000" placeholder="I’m thinking of 4 days in Singapore. Great food, city views, and somewhere lovely to stay…"></textarea><div class="composer-bottom"><span>${icon('compass')} Tell us your destination, budget & what you love</span><button type="submit" id="send" aria-label="Plan my trip">${icon('arrow')}</button></div></form>
  <div class="under-composer"><span>Five specialists. One thoughtful plan.</span><span>Enter to send <kbd>↵</kbd></span></div>
  </div>
  <section id="conversation" hidden><div class="request-bubble"></div><div class="response-heading"><span class="answer-star">✳</span><span>Your travel team</span><span class="working-label"></span></div><div id="progress" aria-live="polite"></div><div id="error" role="alert" hidden></div><article id="answer"></article><div class="answer-actions" hidden><button id="copy">Copy plan</button><span>Generated from your request and the selected tools.</span></div><details id="trace" hidden><summary>Behind the plan <span>Agent notes & review</span></summary><div id="trace-content"></div></details></section>
  <section class="inspiration"><div class="section-label">A LITTLE INSPIRATION</div><div class="example-grid">${examples.map(([title,sub,,ico],i)=>`<button class="example" data-example="${i}"><span class="example-icon">${icon(ico)}</span><strong>${title}</strong><span>${sub}</span><b>${examples[i][4] ? 'Run ↗' : '↗'}</b></button>`).join('')}</div></section>
  <section class="team"><span>YOUR TEAM, WORKING TOGETHER</span><div><span>Manager</span><i>·</i><span>Flights</span><i>·</i><span>Hotels</span><i>·</i><span>Activities</span><i>·</i><span>Critic</span></div></section>
  <footer>Built from the LangGraph travel notebook. Flights, hotels and prices use sample data.<br>Currently best for Singapore trips from Mumbai, Delhi or Bangalore.</footer>
 </div>
</main>`;
const $ = (s) => document.querySelector(s);
const markdown = (s) => DOMPurify.sanitize(marked.parse(s));
function setBusy(value) {
 busy=value; $('#send').disabled=value; $('#request').disabled=value;
 $('.working-label').textContent=value?'Working on your trip…':'';
 document.querySelectorAll('.example').forEach(b=>b.disabled=value);
}
function reset() {
 controller?.abort(); setBusy(false); lastAnswer='';
 $('#conversation').hidden=true; $('.welcome').hidden=false; $('.inspiration').hidden=false; $('.team').hidden=false;
 $('#request').value=''; $('#request').focus();
}
$('.new-trip').onclick=reset;
document.querySelectorAll('.example').forEach(b=>b.onclick=()=>{if(busy)return; const example=examples[Number(b.dataset.example)]; $('#request').value=example[2]; $('#request').focus(); if(example[4])$('#composer').requestSubmit();});
$('#request').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();$('#composer').requestSubmit();}});
$('#copy').onclick=async()=>{try{await navigator.clipboard.writeText(lastAnswer);$('#copy').textContent='Copied';setTimeout(()=>$('#copy').textContent='Copy plan',1800);}catch{$('#copy').textContent='Select the plan to copy';}};
function receive(data) {
 if(data.type==='status')$('.working-label').textContent=data.message;
 if(data.type==='step') {
  const row=document.createElement('div'); row.className='progress-step';
  row.innerHTML=`<span>${icon('check')}</span><span>${labels[data.node] || 'Step completed'}</span>`; $('#progress').append(row);
  const detail=document.createElement('details'); const summary=document.createElement('summary'); summary.textContent=names[data.node] || data.node; detail.append(summary);
  const body=document.createElement('div');body.className='trace-body';
  for(const [key,value] of Object.entries(data.state)) {const part=document.createElement('div');part.innerHTML=markdown(Array.isArray(value)?value.join(', '):String(value));body.append(part);}
  detail.append(body);$('#trace-content').append(detail);$('#trace').hidden=false;
 }
 if(data.type==='result') {lastAnswer=data.answer;$('#answer').innerHTML=markdown(data.answer);$('.answer-actions').hidden=false;$('#progress').classList.add('complete');}
 if(data.type==='error') throw new Error(data.message);
}
$('#composer').onsubmit=async(e)=>{
 e.preventDefault(); if(busy)return; const request=$('#request').value.trim();if(!request){$('#request').focus();return;}
 $('#request').value='';
 controller=new AbortController(); const activeController=controller;
 $('.welcome').hidden=true;$('.inspiration').hidden=true;$('.team').hidden=true;$('#conversation').hidden=false;
 $('.request-bubble').textContent=request;$('#answer').innerHTML='';$('#progress').innerHTML='';$('#progress').classList.remove('complete');$('#trace-content').innerHTML='';$('#trace').hidden=true;$('#error').hidden=true;$('.answer-actions').hidden=true;lastAnswer='';setBusy(true);
 try {
  const response=await fetch('/api/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({request}),signal:controller.signal});
  if(!response.ok){const data=await response.json();throw new Error(typeof data.detail==='string'?data.detail:'Please check your trip request and try again.');}
  const reader=response.body.getReader(); const decoder=new TextDecoder();let buffer='';
  while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let line;while((line=buffer.indexOf('\n'))>=0){const text=buffer.slice(0,line);buffer=buffer.slice(line+1);if(text)receive(JSON.parse(text));}}
  if(!lastAnswer)throw new Error('The connection ended before your plan was ready. Please try again.');
 } catch(error){if(error.name!=='AbortError'){$('#error').textContent=error.message||'Unable to connect. Please try again.';$('#error').hidden=false;}}
 finally{if(controller===activeController){setBusy(false); $('#request').focus();}}
};

setupDocuments();
