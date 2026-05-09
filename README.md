# ai-creative-studio
A Multi-Agent Creative Studio with Google's Agent Stack: ADK, A2A, MCP on Cloud Run &amp; Agent Runtime

A huge thanks to [Saoussen Chaabnia](https://saoussen-chaabnia-ai.com) for the original project! I’m currently building on top of their great work. You can check out the source of inspiration here: [mas-a2a-gcp](https://github.com/Saoussen-CH/mas-a2a-gcp/tree/main). 
Thank you Saoussen, great job!

L'implementazione completa è disponibile come codelab pratico all'indirizzo [codelabs.developers.google.com](https://codelabs.developers.google.com/ai-creative-studio-adk-a2a?hl=it&authuser=3#0)

Repository git originale [mas-a2a-gcp](https://github.com/Saoussen-CH/mas-a2a-gcp/tree/main)

# Build a Multi-Agent Creative Studio with Google's Agent Stack: ADK, A2A, MCP on Cloud Run & Agent Runtime

A hands-on codelab for building a distributed multimodal multi-agent system using **Google ADK**, **A2A protocol**, **MCP**, and **Gemini Enterprise Agent Platform Runtime**. Participants build a complete Instagram campaign generator from scratch, deploying five specialist agents that collaborate through A2A communication.

## What You Build

A distributed multi-agent creative studio where specialized AI agents collaborate to produce complete Instagram campaigns:

| Agent | Role |
|---|---|
| **Brand Strategist** | Market research, competitor analysis, audience insights |
| **Copywriter** | Instagram captions using ADK Skills (platform guidelines + caption formulas) |
| **Designer** | Visual concepts + real image generation via Gemini, stored in GCS |
| **Critic** | Quality review with structured APPROVED / NEEDS_REVISION scores |
| **Project Manager** | Campaign timeline, tasks, and optional Notion integration via MCP |

Coordinated by a **Creative Director** orchestrator that sequences the agents, handles the Critic's revision loop, and compiles the final campaign.

## Key Concepts Covered

- Building ADK agents with tools, callbacks, and system instructions
- **ADK Skills** - packaging reusable knowledge into modular files loaded on demand
- **Multimodal** - bridging a text agent to an image model via a `FunctionTool`
- **A2A protocol** - agents communicating over HTTPS as independent services
- **MCP toolsets** - connecting agents to external services (Notion) without custom glue code
- **`after_tool_callback`** - intercepting tool responses for error handling and schema injection
- Deploying agents to **Cloud Run** and **Gemini Enterprise Agent Platform Runtime**
