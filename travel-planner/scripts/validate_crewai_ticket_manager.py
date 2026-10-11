import os,asyncio,ast,socket
from pathlib import Path
import nbformat
os.environ['CREWAI_TELEMETRY_DISABLED']='true';os.environ['CREWAI_TRACING_ENABLED']='false';os.environ['OPENAI_API_KEY']='offline-placeholder'
from crewai import BaseLLM,Process
p=Path(__file__).resolve().parents[2] / 'LCEL-CrewAI-MAF-LangGraph-Ticket-Solver/Google Colab working files/Simple_CrewAI_Ticket_Solver_Manager.ipynb'
n=nbformat.read(p,as_version=4);nbformat.validate(n)
ns={}
for c in n.cells:
 if c.cell_type!='code':continue
 s='\n'.join(l for l in c.source.splitlines() if not l.startswith('%pip'))
 compile(s,str(p),'exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
 if 'def create_crew' in s:exec(s,ns)
trace=[]
class Fixture(BaseLLM):
 def __init__(self,**kw):super().__init__(model='offline')
 def call(self,messages,**kw):
  task=kw['from_task'];trace.append(kw['from_agent'].role)
  if task.output_json:answer='{"summary":"Account locked.","category":"account","urgency":"high"}'
  elif 'Should it be escalated' in task.description:answer='Yes. Urgent access needs human help.'
  else:answer='Please try account recovery.'
  return 'Final Answer: '+answer
 async def acall(self,messages,**kw):return self.call(messages,**kw)
 def supports_function_calling(self):return False
ns['LLM']=Fixture
async def main():
 c=ns['create_crew']('locked')
 assert c.process==Process.hierarchical and c.manager_agent.allow_delegation
 assert c.manager_agent not in c.agents and all(t.agent is None for t in c.tasks)
 assert c.tasks[1].context==[c.tasks[0]]
 r=await ns['solve_ticket']('  locked  ')
 assert r['ticket']=='locked' and r['analysis']['category']=='account'
 assert r['decision'].startswith('Yes') and r['reply'].startswith('Please')
 assert trace==['Support team manager']*3
 try:await ns['solve_ticket'](' ')
 except ValueError:pass
 else:raise AssertionError('empty input accepted')
 print('PASS: schema, syntax, hierarchical Crew configuration, manager executes all tasks, context, structured result and empty input. Offline fixture does not assess live delegation choices.')
socket.socket.connect=lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('Network forbidden'))
asyncio.run(main())
