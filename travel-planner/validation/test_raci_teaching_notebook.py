import ast, io, contextlib, os
from pathlib import Path
import nbformat
p = Path(__file__).resolve().parents[1] / 'notebooks' / 'travel_planner_langgraph_raci_teaching.ipynb'
n=nbformat.read(p,as_version=4);nbformat.validate(n)
os.environ['OPENAI_API_KEY']='test-not-a-real-key'
ns={};compiled=[]
for i,c in enumerate(n.cells):
 if c.cell_type!='code':continue
 if any(line.lstrip().startswith('%pip') for line in c.source.splitlines()):continue
 ast.parse(c.source)
 if 'read_openai_key()' in c.source or 'draw_mermaid_png' in c.source:continue
 # Defer demos until deterministic model-call replacement is installed.
 if 'result = plan_trip(demo_request)' in c.source or 'plan_text = result[' in c.source or 'RUN_CUSTOM_REQUEST' in c.source:continue
 with contextlib.redirect_stdout(io.StringIO()):exec(compile(c.source,f'cell_{i}','exec'),ns)
assert ns['NODE_ROLES']['flight_agent'] == {'responsible': 'Flight Agent', 'accountable': 'Manager'}
assert all(set(roles) == {'responsible', 'accountable'} for roles in ns['NODE_ROLES'].values())
assert len(ns['build_raci'](['flight_agent']))==5
assert len(ns['build_raci'](['flight_agent','flight_agent']))==5
for selection in [[],['unknown']]:
 try:ns['build_raci'](selection)
 except ValueError:pass
 else:raise AssertionError(selection)
try:ns['hotel_node']({'chosen_workers':['flight_agent']})
except ValueError:pass
else:raise AssertionError('unselected worker accepted')
roles={id(ns['manager_agent']):'manager',id(ns['flight_agent']):'flight_agent',id(ns['hotel_agent']):'hotel_agent',id(ns['activity_agent']):'activity_agent',id(ns['critic_agent']):'critic'}
selected=[];calls=[];critique='NO ISSUES FOUND'
def fake_ask(agent,prompt):
 role=roles[id(agent)];calls.append(role)
 if role=='manager':
  if 'Which specialists' in prompt:return ', '.join(selected)
  if 'list what you understood' in prompt:return 'FROM Mumbai TO Singapore DAYS 4'
  if 'Fix ONLY' in prompt:return 'Revised fixture plan: SQ-421, Hotel Boss'
  return 'Fixture plan: SQ-421, Hotel Boss'
 if role=='critic':return critique
 return role+' fixture report'
ns['ask']=fake_ask
# Run real LangGraph nodes, dynamic routing and parallel fan-in: all seven subsets.
from itertools import combinations
workers=list(ns['WORKER_TASKS'])
for size in range(1,4):
 for group in combinations(workers,size):
  selected[:]=group;calls.clear()
  with contextlib.redirect_stdout(io.StringIO()):result=ns['plan_trip']('Plan a fixture trip')
  steps=[r['step'] for r in result['execution_log']]
  assert len(steps)==len(group)+4,(group,steps)
  assert set(steps)=={'manager','synthesis','critic','revision',*group}
  assert steps.count('synthesis')==1
  assert set(result['chosen_workers'])==set(group)
  assert len(result['raci_entries'])==len(group)+4
  assert result['final_plan']==result['draft_plan']
  assert calls.count('critic')==1
  assert steps.index('synthesis')>max(steps.index(w) for w in group)
# Critical regression: a negated phrase must not bypass revision.
selected[:]=['flight_agent'];critique='Not NO ISSUES FOUND: fix the budget.'
with contextlib.redirect_stdout(io.StringIO()):result=ns['plan_trip']('Flights only')
assert result['final_plan'].startswith('Revised')
try:ns['plan_trip']('   ')
except ValueError:pass
else:raise AssertionError('empty request')
print('PASS: notebook schema and all code syntax; real graph execution for all 7 worker subsets; single synthesis after workers; RACI rows and execution audit; revision and input regressions.')
print('Model calls replaced with deterministic fixtures. No paid API calls; live Colab unverified.')
