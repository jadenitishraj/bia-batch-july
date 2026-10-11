# Google Colab working files

Six standalone ticket notebooks:

- Simple_LangChain_Ticket_Solver_Core_Only.ipynb — LCEL runnable pipeline.

- Simple_LangGraph_Ticket_Solver.ipynb — nodes and shared state.
- Simple_Microsoft_Agent_Framework_Ticket_Solver.ipynb — executors and workflow context.
- Simple_CrewAI_Ticket_Solver.ipynb — Flow with direct LLM calls.
- Simple_CrewAI_Ticket_Solver_Crew.ipynb — one sequential Crew, no Flow.
- Simple_CrewAI_Ticket_Solver_Manager.ipynb — hierarchical Crew with a manager, no Flow.

## Run

1. Upload one notebook to Google Colab.
2. Use a fresh Python 3.12 or 3.13 CPU session for that notebook.
3. In Secrets, add OPENAI_API_KEY and enable Notebook access for this notebook.
4. Run cells from top to bottom. If installation requests a restart, restart and continue with imports/credentials.
5. Use a fresh runtime when switching frameworks, to avoid dependency conflicts.

All use gpt-4o-mini by default. Your API project needs model access and available billing/quota. No Drive mount or project files are required. No credentials are included in these files.

## Verification

Notebook schemas, cell syntax and simulated Colab Secrets success/denied-access paths pass. Real LangGraph/LangChain pipelines, Microsoft Agents/provider/SDK with intercepted HTTP, CrewAI Flow and sequential Crew execute successfully with offline model responses. Empty tickets are rejected and result structures checked. Install versions are pinned; the LangChain dependencies were installed into a fresh Python 3.12 environment.

Not tested inside hosted Google Colab or with your real secret. API authentication, quota and live model output remain dependent on your account. Saved notebook outputs are cleared.

Manager notebook: schema, syntax and real hierarchical Crew execution with an offline fixture pass. Specialist delegation decisions and output quality require a live model run. Normal notebook execution uses OpenAI.
