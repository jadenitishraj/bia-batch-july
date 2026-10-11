import os, asyncio, importlib.util, socket
os.environ['CREWAI_TELEMETRY_DISABLED']='true'
os.environ['CREWAI_TRACING_ENABLED']='false'
os.environ['OPENAI_API_KEY']='offline-placeholder'
from crewai import BaseLLM, Process
from pathlib import Path
import nbformat
p=Path(__file__).resolve().parents[2] / 'LCEL-CrewAI-MAF-LangGraph-Ticket-Solver/Simple_CrewAI_Ticket_Solver_Crew.py'
spec=importlib.util.spec_from_file_location('ticket_crew',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
trace=[]
class Fixture(BaseLLM):
 def __init__(self,**kw):super().__init__(model='offline')
 def call(self,messages,**kw):
  task=kw['from_task'];trace.append(task.agent.role)
  if task.agent.role=='Ticket analyst':answer='{"summary":"Account locked.","category":"account","urgency":"high"}'
  elif task.agent.role=='Escalation reviewer':answer='Yes. Urgent account access needs human help.'
  else:answer='Please use account recovery or contact support.'
  return 'Final Answer: '+answer
 async def acall(self,messages,**kw):return self.call(messages,**kw)
 def supports_function_calling(self):return False
m.LLM=Fixture
async def main():
 c=m.create_crew('Account locked')
 assert c.process==Process.sequential and len(c.tasks)==3
 assert c.tasks[1].context==[c.tasks[0]] and c.tasks[2].context==c.tasks[:2]
 r=await m.solve_ticket('  Account locked  ')
 assert trace==['Ticket analyst','Escalation reviewer','Support reply writer']
 assert r['ticket']=='Account locked' and r['analysis']['category']=='account'
 assert r['decision'].startswith('Yes') and r['reply'].startswith('Please')
 try:await m.solve_ticket('  ')
 except ValueError:pass
 else:raise AssertionError('Empty input accepted')
 nb=nbformat.read(p.with_suffix('.ipynb'),as_version=4);nbformat.validate(nb)
 for cell in nb.cells:
  if cell.cell_type=='code':
   code='\n'.join(line for line in cell.source.splitlines() if not line.startswith(('%pip','!pip')))
   compile(code,str(p),'exec',flags=__import__('ast').PyCF_ALLOW_TOP_LEVEL_AWAIT)
 print('PASS: real sequential Crew, three agent tasks in order, explicit context, structured analysis, result shape, empty input and notebook schema/syntax.')
socket.socket.connect=lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('Network forbidden'))
asyncio.run(main())
