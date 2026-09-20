import { createDownloads } from './downloads';
import { createArchitecture, renderArchitecture } from './architecture';


export function setupDocuments() {
 const workspace = document.querySelector('.workspace');
 const panel = document.createElement('section');
 panel.className = 'documents-panel'; panel.hidden = true;
 panel.innerHTML = `<div class="eyebrow">YOUR PERSONAL KNOWLEDGE BASE</div><h1>A little local knowledge.</h1><p class="documents-intro">Bring your guides, notes and documents along for the trip.</p>
 <form id="upload-form" class="upload-card"><div class="upload-symbol">↥</div><h2>Add a document</h2><p>Documents, PNG charts, or JSON / SRT / VTT transcripts · up to 20 MB</p><label class="sr-only" for="document-file">Choose a document</label><input id="document-file" type="file" accept=".pdf,.txt,.md,.png,.json,.srt,.vtt,.html,.htm,.log,.trace,.py" required/><button id="upload-submit" type="submit">Upload to knowledge base <span>↗</span></button></form>
 <div id="upload-feedback" role="status" aria-live="polite" hidden></div>
 <section id="upload-trace" hidden><h2>Inside your upload</h2><ol id="upload-stages" aria-live="polite"></ol><div id="upload-strategy"></div><div id="upload-chunks"></div><div id="upload-storage"></div></section>
 <div class="library-heading"><h2>Your library</h2><span id="library-count"></span></div><div id="document-library"></div>
 <div class="document-hint"><strong>Ask about your documents in Trip planner</strong><p>Try “What does my uploaded guide recommend?” or “Plan my Singapore trip and append the recommendations from my documents.”</p><button id="ask-documents" type="button">Ask a question ↗</button></div>
 <p class="storage-note">Uploads are added to the shared knowledge base. The original pipeline stores vectors, extracts graph relationships when possible, and saves a BM25 corpus.</p>`;
 workspace.after(panel);
 const downloads=createDownloads(showView);panel.after(downloads);
 const architecture=createArchitecture();downloads.after(architecture);
 const tabs = document.createElement('nav');tabs.className='view-tabs';tabs.setAttribute('aria-label','Planner views');
 tabs.innerHTML='<button id="planner-tab" class="active" type="button" aria-pressed="true">Trip planner</button><button id="documents-tab" type="button" aria-pressed="false">Upload documents</button><button id="downloads-tab" type="button" aria-pressed="false">Downloads</button><button id="architecture-tab" type="button" aria-pressed="false">Architecture</button>';
 document.querySelector('header').after(tabs);
 function showView(view) {
  workspace.hidden=view!=='planner';panel.hidden=view!=='documents';downloads.hidden=view!=='downloads';architecture.hidden=view!=='architecture';
  for(const name of ['planner','documents','downloads','architecture']) {
   const button=document.querySelector(`#${name}-tab`);
   button.classList.toggle('active',name===view);
   button.setAttribute('aria-pressed',String(name===view));
  }
  if(view==='documents')loadLibrary();
  if(view==='architecture')renderArchitecture(architecture);
 }
 document.querySelector('#planner-tab').onclick=()=>showView('planner');
 document.querySelector('#documents-tab').onclick=()=>showView('documents');
 document.querySelector('#downloads-tab').onclick=()=>showView('downloads');
 document.querySelector('#architecture-tab').onclick=()=>showView('architecture');
 document.querySelector('.new-trip').addEventListener('click',()=>showView('planner'));
 document.querySelector('#ask-documents').onclick=()=>{showView('planner');document.querySelector('#request').value='What do my uploaded documents say about ';document.querySelector('#request').focus();};
 async function loadLibrary(){
  const library=document.querySelector('#document-library');
  try{const response=await fetch('/api/documents');if(!response.ok)throw new Error();const data=await response.json();
   document.querySelector('#library-count').textContent=`${data.sources.length} sources · ${data.chunks} chunks`;
   library.replaceChildren();
   for(const source of data.sources){const item=document.createElement('div');item.className='library-item';item.textContent=source;library.append(item);}
   if(!data.sources.length)library.textContent='No documents yet. Add your first file above.';
  }catch{library.textContent='Could not load the document library. Check that the backend is running.';}
 }
 document.querySelector('#upload-form').onsubmit=async event=>{
  event.preventDefault();const input=document.querySelector('#document-file');const file=input.files[0];if(!file)return;
  const status=document.querySelector('#upload-feedback');const button=document.querySelector('#upload-submit');
  status.hidden=false;status.className='';
  if(file.size>20*1024*1024){status.textContent='Please choose a file smaller than 20 MB.';return;}
  button.disabled=true;input.disabled=true;button.textContent='Indexing your document…';status.textContent='Reading, chunking and indexing. Larger documents can take a few minutes.';
  document.querySelector('#upload-trace').hidden=false;
  for(const id of ['upload-stages','upload-strategy','upload-chunks','upload-storage'])document.getElementById(id).replaceChildren();
  let finished=false;
  function text(parent,tag,value){const element=document.createElement(tag);element.textContent=value;parent.append(element);return element;}
  function handle(data){
   const stages=document.querySelector('#upload-stages');
   if(data.type==='stage'){status.textContent=data.message;text(stages,'li',data.message);}
   if(data.type==='parsed'){
    const block=document.querySelector('#upload-strategy');
    text(block,'h3',`Strategy: ${data.strategy}`);text(block,'p',`Parser: ${data.parser}`);
    text(block,'p',data.description);text(block,'small',`${data.filename} · ${data.characters.toLocaleString()} extracted characters`);
   }
   if(data.type==='chunks'){
    text(stages,'li',`Created ${data.chunks.length} chunks`);
    const block=document.querySelector('#upload-chunks');text(block,'h3',`Actual chunks (${data.chunks.length})`);
    data.chunks.forEach((chunk,i)=>{const detail=document.createElement('details');detail.className='chunk-card';
     text(detail,'summary',`Chunk ${i+1} · ${chunk.text.length.toLocaleString()} characters`);
     text(detail,'small',`ID: ${chunk.id}`);text(detail,'pre',chunk.text);
     text(detail,'small',`Metadata: ${JSON.stringify(chunk.metadata)}`);block.append(detail);
    });
   }
   if(data.type==='storage'){
    const block=document.querySelector('#upload-storage');text(block,'h3','Saved storage');
    text(block,'p',`ChromaDB: ${data.vector_saved}/${data.expected} chunk IDs verified`);
    text(block,'p',`BM25 corpus: ${data.bm25_saved}/${data.expected} chunk IDs verified`);
    text(block,'p',data.graph_file ? `Graph file present: ${data.graph_relationships} relationships in the whole knowledge base.` : 'Graph file not found.');
    text(block,'small','The graph count is for all documents; it does not confirm new relationships for this upload.');
   }
   if(data.type==='done'){finished=true;status.textContent=`Done! ${data.chunks} chunks indexed from ${data.filename}.`;status.className='upload-success';text(stages,'li','Done — your document is ready to query.');}
   if(data.type==='error')throw new Error(data.message);
  }
  try{
   const body=new FormData();body.append('file',file);
   const response=await fetch('/api/documents/upload?trace=true',{method:'POST',body});
   if(!response.ok){const data=await response.json();throw new Error(typeof data.detail==='string'?data.detail:'Upload failed.');}
   const reader=response.body.getReader();const decoder=new TextDecoder();let buffer='';
   while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let index;while((index=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,index);buffer=buffer.slice(index+1);if(line)handle(JSON.parse(line));}}
   if(buffer.trim())handle(JSON.parse(buffer));
   if(!finished)throw new Error('The connection ended before indexing completed. Check the stages above before retrying.');
   input.value='';await loadLibrary();
  }
  catch(error){status.textContent=error.message;status.className='upload-error';}
  finally{button.disabled=false;input.disabled=false;button.textContent='Upload to knowledge base ↗';}
 };
}
