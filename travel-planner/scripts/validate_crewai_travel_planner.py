"""Developer-only validation. Run with CrewAI 1.15.27 and nbformat, no API calls."""
import os, asyncio, socket
from pathlib import Path
os.environ['CREWAI_TELEMETRY_DISABLED']='true'
os.environ['CREWAI_TRACING_ENABLED']='false'
os.environ['OPENAI_API_KEY']='offline-placeholder'
import nbformat
from crewai import BaseLLM
ROOT=Path(__file__).resolve().parents[2]
TRACE=[]
WORKERS='flight_agent, hotel_agent, activity_agent'
CRITIQUE='1. Clarify one-way fares.'
class FixtureLLM(BaseLLM):
    def __init__(self, **kwargs):super().__init__(model='offline-fixture')
    def call(self, messages, **kwargs):
        direct = kwargs.get('from_task') is None
        prompt = messages if direct else kwargs['from_task'].description
        TRACE.append(prompt)
        if 'Read this travel request' in prompt:answer='FROM: Mumbai\nTO: Singapore\nDAYS: 4\nTRAVELLERS: 2\nBUDGET: hotel under 45000\nINTERESTS: food, city views, culture\nHARD RULES: avoid red-eye\nMISSING INFO: dates'
        elif 'Which specialists' in prompt:answer=WORKERS
        elif prompt.startswith('Find flights'):answer='TOP 3 OPTIONS: MH-199, 6E-1071, SQ-421\nRECOMMENDED: 6E-1071 INR 21900\nTRADE-OFFS: MH-199 has a stop\nASSUMPTIONS: one-way per person.'
        elif prompt.startswith('Find hotels'):answer='TOP 3 OPTIONS: The Sultan, Hotel Mono, Village Hotel Bugis\nRECOMMENDED: Hotel Mono INR 31500 for three nights\nASSUMPTIONS: shared room.'
        elif prompt.startswith('Plan the days'):answer='DAY BY DAY: Gardens by the Bay and Maxwell Food Centre\nWEATHER NOTE: afternoon rain\nASSUMPTIONS: dates missing.'
        elif 'Review this plan' in prompt:answer=CRITIQUE
        elif 'Fix ONLY' in prompt:answer='Corrected plan: 6E-1071, Hotel Mono. WHAT CHANGED: one-way fares clarified.'
        elif 'Summarize this support ticket' in prompt:answer='Customer needs urgent account access.'
        elif 'Return only one category' in prompt:answer='account'
        elif 'Return only one urgency' in prompt:answer='high'
        elif 'Give the final decision' in prompt:answer='Yes. Urgent account access needs human help.'
        elif 'customer-support assistant' in prompt:answer='Please use account recovery. Contact support if it fails.'
        else:answer='CHOSEN FLIGHT: 6E-1071\nCHOSEN HOTEL: Hotel Mono\nDAY BY DAY PLAN: Gardens by the Bay\nTOTAL COST: unpriced items excluded\nWHY THESE CHOICES: fit request\nASSUMPTIONS: three nights.'
        return answer if direct else 'Final Answer: '+answer
    async def acall(self,messages,**kwargs):
        await asyncio.sleep(.01)
        return self.call(messages,**kwargs)
    def supports_function_calling(self):return False

def load(path):
    nb=nbformat.read(path,as_version=4);nbformat.validate(nb)
    ns={"__name__": "__main__"}
    exec("import os, asyncio\nfrom crewai import Agent, Task, Crew, Process, LLM\nfrom crewai.tools import tool\nfrom crewai.flow.flow import Flow, start, listen",ns)
    for c in nb.cells:
        if c.cell_type!='code':continue
        s=c.source
        if '%pip' in s or 'read_openai_key()' in s or s.startswith('result =') or 'await plan_trip(demo_request)' in s or 'input(' in s or s.startswith('# Check that'):continue
        compile(s,str(path),'exec')
        exec(s,ns)
    ns['LLM']=FixtureLLM
    return ns
async def main():
    global WORKERS,CRITIQUE
    travel=load(ROOT/'travel-planner/notebooks/travel_planner_crewai.ipynb')
    travel['MODEL']='gpt-4o-mini'
    # Direct tool checks exercise actual CrewAI wrappers and preserved filters.
    assert [x['id'] for x in travel['search_flights'].run(origin='Mumbai',destination='Singapore',avoid_red_eye=True)]==['MH-199','6E-1071','SQ-421']
    assert travel['search_hotels'].run(city='unknown')==[]
    assert travel['convert_currency'].run(amount=100,from_currency='SGD',to_currency='INR').endswith('SGD = 6500.0 INR')
    for WORKERS,expected in [('flight_agent, hotel_agent, activity_agent',3),('hotel_agent',1),('flight_agent, activity_agent',2),('invalid',3)]:
        TRACE.clear();r=await travel['run_travel_state']('fixture trip')
        assert len(r['chosen_workers'])==expected
        assert sum(k in r for k in ['flight_report','hotel_report','activity_report'])==expected
        assert sum('Fix ONLY' in x for x in TRACE)==1
    CRITIQUE='NO ISSUES FOUND';TRACE.clear()
    r=await travel['run_travel_state']('second trip')
    assert r['final_plan']==r['draft_plan'] and not any('Fix ONLY' in x for x in TRACE)
    ticket=load(ROOT/'LCEL-CrewAI-MAF-LangGraph-Ticket-Solver/Simple_CrewAI_Ticket_Solver.ipynb');ticket['MODEL_NAME']='offline'
    TRACE.clear();r=await ticket['solve_ticket']('  locked account  ')
    assert set(r)=={'ticket','analysis','decision','reply'}
    assert r['ticket']=='locked account' and r['analysis']['category']=='account' and len(TRACE)==5
    TRACE.clear()
    try:await ticket['solve_ticket']('   ')
    except ValueError:pass
    else:raise AssertionError('empty ticket accepted')
    assert not TRACE
    print('PASS: notebook schemas, real CrewAI Flow/Agent/Task/Crew execution, tools, 1/2/3-worker selection, fallback, one revision, no-issues skip, ticket shape/five direct model calls/empty input.')
if __name__=='__main__':
    # Any attempted network connection fails, including accidental provider calls.
    def deny(*args,**kwargs):raise RuntimeError('Network forbidden during developer validation')
    socket.socket.connect=deny
    asyncio.run(main())
