# AGENTS.md — Universal Multi-Agent Contract (Codex, Cline, Goose, Cursor, Claude Code, J.A.R.V.I.S. Omega)

@CLAUDE.md

## Universal Agent Routing & Tool Bindings

1. **Primary Gateway**: `http://localhost:8080/v1` (J.A.R.V.I.S. Omega Unified Router)
2. **Upstream Routers**:
   - `OmniRoute`: `http://localhost:20128/v1` (375 providers, 150+ free, RTK+Caveman stacked compression)
   - `FreeLLMAPI`: `http://localhost:3001/v1` (34 free LLM providers, 635 free endpoints, auto-failover)
   - `Ollama / AirLLM`: `http://localhost:11434/v1` (Local GPU/CPU & layer-wise 70B inference on 4GB VRAM)
3. **Slash Commands**:
   - `/jarvis <mission>` — Full Stark HUD autonomous mission execution
   - `/octo <topic>` — Run 4-Seat Claude Octopus Multi-Model Consensus
   - `/caveman [on|ultra|off]` — Toggle Caveman 89% token compression
   - `/ponytail [lite|full|ultra]` — Toggle Lazy Senior Dev YAGNI mode
   - `/adhd [on|off]` — Toggle Action-First ADHD output shaping
   - `/karpathy` — Audit code/plan against the 10 Karpathy Engineering Rules
   - `/security-review` — Run Claude Security vulnerability & secret scan + STRIDE threat model
   - `/mem <query>` — Search or store in Claude-Mem + Busabase + Notra local vault
   - `/montage <prompt>` — Trigger OpenMontage video/media production pipeline
   - `/godmode <prompt>` — Activate GODMOD3 multi-perspective cognitive red-team research
