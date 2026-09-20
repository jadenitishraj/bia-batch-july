// These diagrams mirror the current Python functions; update them when those functions change.
const diagrams = [
 {id:'overall', title:'The complete RAG journey', file:'pipeline.py · retriever.py · app/document_answers.py', intro:'Two separate flows: prepare evidence when a file is uploaded, then retrieve evidence when a question arrives.', code:`flowchart LR
 A["Upload file"] --> B["Parse<br/>Read content"] --> C["Chunk<br/>Split text"]
 C --> V[("Vector DB")]
 C --> K[("BM25 corpus")]
 C --> G[("Graph store")]
 Q["Ask a question"] --> P["Prepare search<br/>Rephrase · HyDE<br/>Query variants"]
 V --> R["Search all three<br/>Vector + BM25 + graph"]
 K --> R
 G --> R
 P --> R
 R --> F["Combine results<br/>Rank fusion + dedup"] --> L["LLM rerank<br/>Top 3 by default"]
 L --> AN["Answer from evidence"] --> UI["Trip planner"]
 class V,G,K store
 class A,Q,UI endpoint`, note:'HyDE text helps search; it is not evidence. Graph results have no original filename in the stored graph and are labeled separately. Ragas runs separately from chat.'},

 {id:'parser', title:'Parser: read and classify', file:'rag_v2/parser.py · rag_v2/image_parser.py', intro:'Read the file, extract its content, and choose how to split it.', code:`flowchart LR
 A["Uploaded file"] --> R["Choose reader<br/>PDF: pypdf · JSON: JSONReader<br/>Captions: pysubs2 · PNG: vision<br/>Other files: read text"]
 R --> T["Readable text"] --> S["Choose chunking strategy<br/>Markdown · HTML · token<br/>Transcript · image Markdown · semantic"]
 S --> OUT["Parsed document<br/>Text + strategy + source metadata"]
 class A,OUT endpoint`, note:'File type selects the reader and usually the strategy. Table-heavy text uses Markdown; text with sparse punctuation uses token splitting; remaining text uses semantic splitting. Missing files, empty text and unreadable PNGs are rejected.'},
 {id:'chunker', title:'Chunker: create the pieces', file:'rag_v2/chunker.py', intro:'Choose one LlamaIndex splitter, then use one shared call to turn the document into nodes.', code:`flowchart LR
 A["Parsed document"] --> S{"Strategy"}
 S -->|markdown / image_markdown| MD["MarkdownNodeParser"]
 S -->|html| HTML["HTMLNodeParser"]
 S -->|token / transcript| TOK["TokenTextSplitter<br/>512 tokens · overlap 50"]
 S -->|semantic| SEM["SemanticSplitterNodeParser<br/>buffer 1 · percentile 90<br/>Embedding model"]
 S -->|Other| SENT["SentenceSplitter<br/>768 tokens · overlap 80"]
 MD --> DOC["One Document<br/>Text + metadata"]
 HTML --> DOC
 TOK --> DOC
 SEM --> DOC
 SENT --> DOC
 DOC --> N["get_nodes_from_documents"] --> OUT["Chunk list<br/>id · text · metadata"]
 class A,OUT endpoint`, note:'The sentence splitter is a fallback for unrecognized strategies. Transcript text is chunked as one document, not one document per caption.'},
 {id:'indexer', title:'Indexer: one upload, three stores', file:'rag_v2/indexer.py', intro:'Prepare the chunks, then follow how each storage destination represents the same information.', code:`flowchart LR
 A["Document chunks<br/>ID · text · metadata"] --> SET["Prepare storage<br/>Open Chroma collection<br/>Load or create graph store"]
 SET --> N["Create TextNodes<br/>Preserve chunk IDs and metadata"]
 N --> V["VectorStoreIndex<br/>Generate embeddings"] --> VS[("ChromaDB<br/>global_knowledge")]
 N --> G["KnowledgeGraphIndex<br/>Extract up to 2 triplets per chunk<br/>Include embeddings"] --> GS[("SimpleGraphStore<br/>Persist relationships")]
 N --> B["BM25 corpus<br/>Append original chunk text"] --> BS[("bm25_index.json")]
 VS --> OUT["Knowledge available<br/>for retrieval"]
 GS --> OUT
 BS --> OUT
 class VS,GS,BS store
 class A,OUT endpoint`, note:'Branches show data flow. Actual writes run sequentially: vectors, graph extraction, storage persistence, then BM25 JSON. Graph extraction errors are logged and ingestion continues. Repeated uploads can duplicate chunks.'},
 {id:'multiagent', title:'Multi-agent travel planner', file:'app/graph.py · app/nodes.py · app/agents.py', intro:'Five agents, seven graph nodes. Only selected specialists run; the manager also handles synthesis and revision.', code:`flowchart LR
 A["Travel request"] --> M["Manager<br/>Extract requirements<br/>Choose workers"]
 M -->|Selected| F["Flight agent"]
 M -->|Selected| H["Hotel agent"]
 M -->|Selected| AC["Activity agent"]
 F --> S["Manager: synthesis<br/>Combine worker reports"]
 H --> S
 AC --> S
 S --> C["Critic<br/>Review draft against requirements"]
 C --> R{"No issues found?"}
 R -->|Yes| KEEP["Keep draft"]
 R -->|No| FIX["Manager: revision<br/>Fix listed issues once"]
 KEEP --> OUT["Final plan"]
 FIX --> OUT
 OUT --> DOC{"Also a document question?"}
 DOC -->|Yes| RAG["Run RAG<br/>Append document answer"] --> UI["Show in planner"]
 DOC -->|No| UI
 class A,OUT,UI endpoint`, note:'Selected specialists run in parallel. If the manager returns no valid worker names, all three are selected. There is one critic/revision pass, not a repeated review loop. Document-only requests bypass this travel graph. Tools use sample travel data.'},
 {id:'manager', title:'Manager: coordinate and write', file:'app/nodes.py · app/agents.py', intro:'The same manager agent is reused in three graph nodes. It has no tools.', code:`flowchart LR
 Q["Request"] --> REQ["Extract requirements<br/>Origin, destination, days, travellers<br/>Budget, interests, rules, missing info"]
 REQ --> PICK["Choose specialist names"] --> VALID{"Any valid names?"}
 VALID -->|Yes| WORK["Run selected workers"]
 VALID -->|No| ALL["Run all three workers"]
 WORK --> REPORTS["Worker reports"]
 ALL --> REPORTS
 REPORTS --> SYN["Synthesis<br/>Write draft from reports only"] --> CRIT["Critic reviews"]
 CRIT --> OK{"NO ISSUES FOUND?"}
 OK -->|Yes| FINAL["Return draft as final_plan"]
 OK -->|No| REV["Fix listed problems<br/>Return plan and WHAT CHANGED"] --> END["final_plan"]
 class Q,FINAL,END endpoint`, note:'Requirements and chosen_workers are saved in shared travel state. Missing worker reports are shown as not requested during synthesis. The manager does not search travel data itself.'},
 {id:'flights', title:'Flight specialist', file:'app/nodes.py · app/agents.py · app/registry.py', intro:'The flight node passes the manager’s requirements to the flight agent.', code:`flowchart LR
 REQ["Trip requirements"] --> A["Flight agent"]
 A <-->|Available tool| F["search_flights"]
 A <-->|Available tool| FX["convert_currency"]
 A --> REPORT["Top 3 options<br/>Recommendation<br/>Trade-offs and assumptions"] --> STATE["flight_report"] --> S["Manager synthesis"]
 class REQ,STATE endpoint`, note:'The agent decides which available tools to call. Tool availability does not mean every tool runs. Flights are sample data, not live airline inventory.'},
 {id:'hotels', title:'Hotel specialist', file:'app/nodes.py · app/agents.py · app/registry.py', intro:'The hotel node passes the requirements to the hotel agent, including the full-stay budget.', code:`flowchart LR
 REQ["Trip requirements"] --> A["Hotel agent"]
 A <-->|Available tool| H["search_hotels"]
 A <-->|Available tool| FX["convert_currency"]
 A <-->|Available tool| T["get_travel_tips"]
 A --> REPORT["Top 3 options<br/>Nightly and full-stay cost<br/>Recommendation and trade-offs<br/>Assumptions"] --> STATE["hotel_report"] --> S["Manager synthesis"]
 class REQ,STATE endpoint`, note:'The agent is instructed to check the total stay cost. Tool calls are chosen by the agent; hotel options and prices come from sample data.'},
 {id:'activities', title:'Activity specialist', file:'app/nodes.py · app/agents.py · app/registry.py', intro:'The activity node asks the agent to plan the days from the manager’s requirements.', code:`flowchart LR
 REQ["Trip requirements"] --> A["Activity agent"]
 A <-->|Available tool| ACT["search_activities"]
 A <-->|Available tool| FOOD["search_restaurants"]
 A <-->|Available tool| W["get_weather"]
 A --> REPORT["Day-by-day suggestions<br/>Morning, afternoon, evening and meals<br/>Weather note and assumptions"] --> STATE["activity_report"] --> S["Manager synthesis"]
 class REQ,STATE endpoint`, note:'The prompt asks for two or three activities plus one meal per day. This is an instruction to the model, not a hard-coded limit. Available tools use demo data.'},
 {id:'critic', title:'Critic: review, then hand back', file:'app/nodes.py · app/agents.py', intro:'The critic lists specific problems. The manager performs any required rewrite.', code:`flowchart LR
 D["Draft plan + requirements"] --> C["Critic agent<br/>No tools"] --> CHECK["Check budget<br/>Daily workload<br/>Traveller interests<br/>Honest assumptions"]
 CHECK --> RESULT{"Any problems?"}
 RESULT -->|No| OK["NO ISSUES FOUND"] --> KEEP["Revision node keeps draft"]
 RESULT -->|Yes| ISSUES["Numbered list of specific fixes"] --> FIX["Manager fixes listed issues"]
 KEEP --> FINAL["Final plan"]
 FIX --> FINAL
 class D,FINAL endpoint`, note:'The graph always runs the revision node. That node skips the rewrite when the critique contains NO ISSUES FOUND. The revised plan is not sent through another critic pass.'},

];
let rendered = false;
const diagramLabels = {overall:'Overall RAG', parser:'Parser', chunker:'Chunker', indexer:'Indexer', multiagent:'Multi-agent', manager:'Manager', flights:'Flights', hotels:'Hotels', activities:'Activities', critic:'Critic'};
export function createArchitecture() {
 const panel=document.createElement('section');panel.className='documents-panel architecture-panel';panel.hidden=true;
 panel.innerHTML=`<div class="eyebrow">THE CODE, MADE VISIBLE</div><h1>Inside your travel planner.</h1><p class="documents-intro">Explore document retrieval and the travel-agent team. Choose a tab to see one complete flow.</p><nav class="architecture-tabs" role="tablist" aria-label="Architecture diagrams">${diagrams.map((d,i)=>`<button type="button" role="tab" id="diagram-tab-${d.id}" aria-controls="architecture-${d.id}" aria-selected="${i===0}" tabindex="${i===0?0:-1}" data-diagram-tab="${d.id}">${diagramLabels[d.id]}</button>`).join('')}</nav>${diagrams.map((d,i)=>`<section class="architecture-flow" id="architecture-${d.id}" role="tabpanel" aria-labelledby="diagram-tab-${d.id}" ${i?'hidden':''}><div class="architecture-heading"><span>0${i+1}</span><div><h2>${d.title}</h2><p>${d.file}</p></div></div><p class="architecture-intro">${d.intro}</p><div class="diagram-controls"><button type="button" data-zoom="out" aria-label="Zoom out ${d.id} diagram">−</button><button type="button" data-zoom="reset">Fit</button><button type="button" data-zoom="in" aria-label="Zoom in ${d.id} diagram">+</button><span><output class="diagram-zoom">100%</output> · Fit shows the whole diagram</span></div><div class="mermaid-viewport" tabindex="0" role="region" aria-label="${d.title} diagram"><div class="mermaid-canvas" data-diagram="${d.id}">Loading diagram…</div></div><p class="architecture-caption">${d.note}</p></section>`).join('')}`;
 const tabs=[...panel.querySelectorAll('[data-diagram-tab]')];
 function selectDiagram(tab) {
  tabs.forEach(button=>{
   const selected=button===tab;
   button.setAttribute('aria-selected',String(selected));button.tabIndex=selected?0:-1;
   panel.querySelector(`#architecture-${button.dataset.diagramTab}`).hidden=!selected;
  });
  const canvas=panel.querySelector(`#architecture-${tab.dataset.diagramTab} .mermaid-canvas`);
  sizeDiagram(canvas);
 }
 tabs.forEach((tab,index)=>{
  tab.onclick=()=>selectDiagram(tab);
  tab.onkeydown=event=>{
   let next;
   if(event.key==='ArrowRight')next=(index+1)%tabs.length;
   if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;
   if(event.key==='Home')next=0;
   if(event.key==='End')next=tabs.length-1;
   if(next!==undefined){event.preventDefault();tabs[next].focus();selectDiagram(tabs[next]);}
  };
 });
 panel.querySelectorAll('.diagram-controls button').forEach(button=>button.onclick=()=>{
  const canvas=button.closest('section').querySelector('.mermaid-canvas');
  const current=Number(canvas.dataset.zoom || 1);
  const zoom=button.dataset.zoom==='reset'?1:Math.max(.25,Math.min(3,current+(button.dataset.zoom==='in'?.25:-.25)));
  canvas.dataset.zoom=zoom;sizeDiagram(canvas);
 });
 const resizeObserver=new ResizeObserver(()=>panel.querySelectorAll('.mermaid-canvas').forEach(sizeDiagram));
 resizeObserver.observe(panel);
 return panel;
}
function sizeDiagram(canvas) {
 const svg=canvas.querySelector('svg');
 if(!svg || !canvas.closest('section').getBoundingClientRect().width)return;
 const viewport=canvas.parentElement;
 const box=svg.viewBox.baseVal;
 const fit=Math.min((viewport.clientWidth-24)/box.width,(viewport.clientHeight-24)/box.height);
 const zoom=Number(canvas.dataset.zoom || 1);
 canvas.style.width=`${box.width*fit*zoom}px`;
 canvas.style.height=`${box.height*fit*zoom}px`;
 canvas.closest('section').querySelector('.diagram-zoom').textContent=`${Math.round(zoom*100)}%`;
}
export async function renderArchitecture(panel) {
 if(rendered)return;
 rendered=true;
 try {
  const {default:mermaid}=await import('mermaid');
  mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'base',fontFamily:'DM Sans, sans-serif',themeVariables:{primaryColor:'#f2ecdf',primaryTextColor:'#37372f',primaryBorderColor:'#bc9d80',lineColor:'#ab7357',secondaryColor:'#edf0e5',tertiaryColor:'#fffefa',clusterBkg:'#faf8f2',clusterBorder:'#ddd4c4',fontSize:'15px'},flowchart:{htmlLabels:false,curve:'basis',nodeSpacing:25,rankSpacing:40,useMaxWidth:true}});
  for(const d of diagrams){
   const {svg}=await mermaid.render(`rag-diagram-${d.id}`,`${d.code}\nclassDef store fill:#e5eddf,stroke:#8b9c78,color:#34402b\nclassDef endpoint fill:#b56c51,stroke:#a05c44,color:#fff\nclassDef warning fill:#f6e4dd,stroke:#be8974,color:#693d2d`);
   const canvas=panel.querySelector(`[data-diagram="${d.id}"]`);
   canvas.innerHTML=svg;
   sizeDiagram(canvas);
  }
 } catch(error) {
  rendered=false;
  panel.querySelectorAll('.mermaid-canvas').forEach(canvas=>{if(!canvas.querySelector('svg'))canvas.textContent='Diagram could not load. Reopen Architecture to retry.';});
  console.error('Architecture rendering failed',error);
 }
}
