const samples = [
 {file:'rag-ingestion-diagram.png', type:'PNG · Diagram', title:'From upload to answer', description:'Follow the arrows through parsing, chunks, storage and retrieval.', question:'According to rag-ingestion-diagram.png, what happens after chunks are created?'},
 {file:'rainy-day-decision.png', type:'PNG · Diagram', title:'The rainy-day plan', description:'Explore a travel decision diagram with indoor and outdoor alternatives.', question:'According to rainy-day-decision.png, what should the group do when rain is forecast?'},
 {file:'singapore-student-guide.pdf', type:'PDF · 3 pages', title:'Singapore learning weekend', description:'A fictional itinerary with budgets, meeting details and a rainy-day plan.', question:'According to singapore-student-guide.pdf, what is the four-day allowance for all four students, and where do they meet on day one?'},
 {file:'rag-classroom-handbook.pdf', type:'PDF · 3 pages', title:'The RAG classroom handbook', description:'Chunking, three storage destinations and grounded-answer exercises.', question:'According to rag-classroom-handbook.pdf, how do vector storage, BM25 and a graph differ?'},
 {file:'singapore-student-guide-lesson.vtt', type:'VTT · 20-minute script', title:'Planning with evidence', description:'A long, original YouTube-style lesson with 24 timestamped captions.', question:'According to singapore-student-guide-lesson.vtt, what changes when rain interrupts the walk?'},
 {file:'rag-classroom-handbook-lesson.vtt', type:'VTT · 20-minute script', title:'RAG, explained step by step', description:'A long, original classroom script to demonstrate token splitting.', question:'According to rag-classroom-handbook-lesson.vtt, why does saving a graph not prove it is used for answers?'},
];

export function createDownloads(showView) {
 const panel=document.createElement('section');
 panel.className='documents-panel downloads-panel';panel.hidden=true;
 panel.innerHTML=`<div class="eyebrow">READY FOR YOUR NEXT EXPERIMENT</div><h1>A little library to learn with.</h1><p class="documents-intro">Download a sample, add it in Upload documents, then ask a question in Trip planner.</p><p class="sample-note">All samples are fictional teaching material. The VTT files are original YouTube-style scripts, not transcripts from real videos.</p><div class="download-grid">${samples.map((sample,i)=>`<article class="download-card">${sample.file.endsWith('.png')?`<img src="/samples/${sample.file}" alt="${sample.title} diagram" loading="lazy"/>`:''}<span class="download-type">${sample.type}</span><h2>${sample.title}</h2><p>${sample.description}</p><a class="download-link" href="/samples/${sample.file}" download>Download ${sample.file.split('.').pop().toUpperCase()} ↓</a><details><summary>A question to try after uploading</summary><p>${sample.question}</p><button type="button" data-sample-question="${i}">Use this question ↗</button></details></article>`).join('')}</div><button type="button" class="samples-upload">Go to Upload documents ↗</button>`;
 panel.querySelector('.samples-upload').onclick=()=>showView('documents');
 panel.querySelectorAll('[data-sample-question]').forEach(button=>button.onclick=()=>{
  showView('planner');
  const input=document.querySelector('#request');input.value=samples[Number(button.dataset.sampleQuestion)].question;input.focus();
 });
 return panel;
}
