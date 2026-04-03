# Dynamic tool selection for LLM agents: when it helps and when it doesn't

**For a geoportal agent with ~19 tools, loading all tool definitions upfront is the right call.** At roughly 4,000 tokens (2% of a 200K context window), the overhead is trivial, and dynamic selection introduces retrieval-miss risk that is far more dangerous than a few extra tokens. The evidence is clear: accuracy degradation begins at 30–50 tools for frontier models, and every major benchmark confirms that 19 tools sits comfortably within the reliable operating range. The highest-ROI investment is writing excellent tool descriptions, not building retrieval infrastructure. That said, the dynamic selection techniques now emerging in production are genuinely powerful for larger tool sets and worth understanding for future scaling.

---

## The hard numbers on tool count versus accuracy

Multiple benchmarks from 2024–2026 quantify exactly when models start struggling with tools. The HumanMCP benchmark (2025) tested scaling from 10 to 2,000 tools across frontier models. **Gemini 2.0 Flash dropped from 98.4% accuracy at 10 tools to 88.2% at 100, then to 65% at 2,000.** Claude 3.5 Haiku proved most stable, declining only 9.2 points across the same range. MCPVerse (2025) tested 552 real-world tools spanning 140K tokens of definitions: only Claude 4 Sonnet and Gemini 2.5 Pro could even complete evaluation at that scale, with Claude 4 Sonnet topping out at 57.8% accuracy.

The TaskBench study (NeurIPS 2024) found even steeper drops in multi-tool graph scenarios: **96% accuracy with a single tool collapsed to 25% with eight tools in complex chained workflows**. However, this measures multi-step tool *chaining* accuracy, not single-step tool *selection* — a critical distinction for most agent architectures.

Industry consensus has converged on practical thresholds. OpenAI states that fewer than **~100 tools with ~20 arguments per tool** is "in-distribution" for o3/o4-mini models, though their API hard-caps at 128 tools. Anthropic recommends their Tool Search feature when **10+ tools** are present or definitions exceed **10K tokens**. The Berkeley Function Calling Leaderboard, the de facto evaluation standard, averages only 3 function choices per test case — meaning large-scale tool behavior remains surprisingly under-benchmarked by the primary industry evaluation.

For a 19-tool geoportal agent targeting frontier models, these numbers are reassuring. The system sits well below every documented degradation threshold for single-step tool selection.

---

## Tool retrieval via vector search is real and production-ready

The most widely adopted dynamic selection pattern embeds tool descriptions into a vector store and retrieves semantically similar tools at query time. The architecture is straightforward: tool name, description, and parameter information get converted to embeddings offline, stored in FAISS, pgvector, Pinecone, or similar, and at query time the user's input is embedded and matched via approximate nearest-neighbor search. Only the top-K retrieved tools (typically 3–10) are injected into the LLM's context.

Embedding models commonly used include OpenAI's **text-embedding-3-small** (1,536 dimensions), Sentence-BERT variants like all-MiniLM-L12-v2 (384 dimensions), and BGE M3. Cosine similarity thresholds in production typically sit around **0.4** for broad recall, with top-5 to top-10 retrieval. Latency is sub-100ms across all configurations tested in the Semantic Tool Discovery for MCP paper (2025).

The critical failure mode is **retrieval misses**. A query like "check this area" in a geospatial context could map to buffer analysis, area calculation, or spatial containment — and embedding similarity may not resolve this correctly. The Tool2Vec approach from Red Hat addresses this by embedding *example user queries* that invoke each tool rather than the tool's own description, achieving a **30.5% improvement in recall** over description-based embedding. Apple Research's ProTIP framework takes a different tack, using progressive retrieval conditioned on execution history to handle multi-step dependencies where the right tool at step 2 depends on step 1's results.

The strongest results come from hybrid retrieval combining BM25 lexical matching with dense vector search plus re-ranking. The Tool-to-Agent Retrieval system (2025) embeds both tools and their parent agents in a shared vector space, achieving **19.4% improvement in Recall@5** on LiveMCPBench's 527-tool benchmark over prior state-of-the-art.

---

## Anthropic and OpenAI have converged on deferred tool loading

Both major API providers now offer nearly identical solutions for managing large tool sets, which is the clearest signal of where production practice is heading.

Anthropic's **Tool Search Tool**, released November 2025, lets developers register tools with `defer_loading: true`. The model initially sees only a lightweight search primitive (~500 tokens) instead of the full catalog. When Claude needs a capability, it searches and loads 3–5 relevant tools on demand. The results are striking: **85% reduction in token usage** (from ~77K to ~8.7K for a 50-tool MCP setup) and, counterintuitively, *improved* accuracy — Opus 4 went from **49% to 74%**, and Opus 4.5 from **79.5% to 88.1%** with Tool Search enabled. Fewer irrelevant tools in context means less confusion during selection.

OpenAI introduced parallel features with `tool_search` and `defer_loading` for GPT-5.4+, adding **namespaces** that group related tools under shared descriptions (e.g., "spatial_queries", "geocoding"). Their recommendation: fewer than 10 functions per namespace, prefer namespaces over many individually deferred functions.

Anthropic also introduced **Programmatic Tool Calling**, where Claude writes Python orchestration code in a sandbox rather than making individual tool calls. This achieved **37% token reduction** on complex multi-tool tasks because intermediate results stay in the code environment rather than polluting the conversation context. Cloudflare takes this further with Code Mode, converting MCP tools into TypeScript APIs that the agent programs against — compressing 2,500 API endpoints into 2 effective tools with **99.9% token reduction**.

For production systems at scale, these provider-native features are becoming the standard approach, displacing custom retrieval infrastructure.

---

## The academic foundations: ToolBench, Gorilla, and FunctionGemma

Three research projects established the foundational patterns now appearing in production. **ToolLLM** (Tsinghua/OpenBMB, ICLR 2024) created a benchmark of 16,464 real-world APIs across 49 categories and trained a neural API retriever — a sentence-embedding model matching natural language instructions to API descriptions. A surprising finding: retrieved APIs actually *outperformed* oracle (ground-truth) API sets because the retriever discovered more appropriate similar APIs than human annotators had identified.

**Gorilla** (UC Berkeley, NeurIPS 2024) introduced Retrieval-Aware Training, where the model is trained *with* retriever outputs concatenated to prompts, making it robust to retriever quality. Gorilla outperformed GPT-4 on API call accuracy and hallucinated ~60% less than GPT-3.5. The team's Berkeley Function Calling Leaderboard (now at V4) has become the industry standard for tool-calling evaluation.

**FunctionGemma** (Google, 2025) is a **270M-parameter model** fine-tuned exclusively for function calling — not a dialogue model but a tool-routing preprocessor. After fine-tuning, it achieves **85% accuracy** on mobile action selection (up from 58% base) and runs at ~50 tokens/sec on a phone, needing only 550MB RAM. Google explicitly positions it as a "traffic controller" for compound systems, handling local tool routing while forwarding complex tasks to larger models. Other small models show similar promise: Qwen3 at 1.7B parameters achieved a **0.960 Agent Score** in a 21-model benchmark, and ToolRM-1.5B surpassed models 80x its size on tool-calling reward modeling.

The converging architectural pattern across all this research is: **intent recognition → embedding-based tool retrieval → candidate ranking/filtering → LLM execution with a small tool subset**. This "progressive tool discovery" pipeline appears consistently across ToolLLM, Gorilla, ProTIP, and now production systems.

---

## Two-stage routing and hierarchical organization in practice

Beyond simple vector retrieval, several more sophisticated patterns have emerged for production use.

**Two-stage hybrid cascades** combine fast embedding retrieval with LLM-based re-ranking. Stage 1 retrieves top-K candidates via embedding similarity (sub-100ms). Stage 2 asks the main LLM to evaluate only those candidates. Benchmark data shows hybrid k=3 captures **~98% of LLM-only accuracy at ~40% of the latency**; going from hybrid k=5 to full LLM-only evaluation gains only ~1% accuracy while costing 2.5x more in latency.

**Hierarchical tool organization** groups tools into categories or namespaces where the LLM first picks a category, then sees only tools within it. Salesforce Agentforce implements this with "Topics" — high-level capability categories encapsulating instructions, actions, and guardrails. Their explicit guidance: "Overloading a single agent with too many disparate tools can clutter its context window, leading to slower reasoning or inaccurate results." Their solution is a supervisor agent routing to specialist agents with focused 5-tool sets. LangGraph supports this with hierarchical agent teams: top-level supervisor → mid-level supervisors → worker agents with domain-specific tools.

A practical middle-ground implementation uses **toolkits** — grouped tools with keywords, descriptions, and embeddings. A fast keyword-matching pass handles obvious cases, with embedding similarity as fallback for ambiguous queries. One production system manages 35+ tools this way, loading only the relevant toolkit per request.

For the geoportal use case, a natural hierarchy might group tools as: spatial queries (PostGIS), geocoding/addressing, routing/navigation, feature search/metadata, and administrative operations. But with only 19 tools, this hierarchy adds a routing step without clear benefit — the LLM can see all 19 tools and reason about which to use directly.

---

## Tool description optimization delivers outsized returns

For smaller tool sets, description quality matters more than selection architecture. Atlassian's mcp-compressor benchmark on GitHub's 94-tool MCP server quantifies the compression-accuracy tradeoff across four levels:

- **Full descriptions**: 17,600 tokens (baseline)
- **Low compression** (full descriptions preserved): ~3,900 tokens (78% reduction)
- **Medium** (first sentence only): ~3,300 tokens (81% reduction)
- **High** (tool names + parameter names only): ~2,200 tokens (88% reduction)
- **Maximum** (single `list_tools()` function): ~500 tokens (97% reduction)

Speakeasy's Dynamic Toolsets approach separates search, describe, and execute phases — schemas representing **60–80% of token usage** are loaded only when explicitly requested, achieving up to **160x token reduction** with 100% success rates maintained.

LangChain research found that dynamically selected few-shot examples dramatically improved tool selection accuracy: Claude 3 Sonnet went from **16% zero-shot to 52%** with just 3 semantically similar examples. Paragon's empirical evaluation (50 test cases across 6 integrations with ~20 tools), however, found that enhanced descriptions had **negligible effect on overall tool correctness** — LLM model choice mattered most. The resolution: descriptions matter most when tools have overlapping semantics or when the model is weaker.

For geospatial tools specifically, description optimization should address spatial language ambiguity explicitly. Define what "near" means (buffer distance? k-nearest?), specify coordinate systems expected (WGS84, projected CRS), document geometry type requirements, and include when-to-use and when-not-to-use guidance. Using consistent prefixes like `postgis_` or `spatial_` helps both LLM reasoning and any future dynamic retrieval system.

---

## Concrete recommendation for a 19-tool geoportal agent

The evidence points to a clear strategy. Start by **loading all 19 tools upfront** with well-crafted descriptions. The token overhead (~4,000 tokens) is negligible against modern context windows — **2% of Claude Sonnet's 200K window, 0.4% of the 1M beta**. At $3/M input tokens, that's $0.012 per request, and prompt caching reduces even this by 90% for repeated conversations.

Most successful geospatial LLM agents — LLM-Geo, GIS Copilot, Spatial-RAG — already use all-tools-upfront approaches. Spatial operations have complex interdependencies (knowing about ST_Buffer helps the model understand when to use ST_Intersects), and the LLM benefits from seeing the full toolkit to reason about multi-step spatial workflows.

Invest the engineering effort in three high-ROI optimizations instead of building retrieval infrastructure:

- **Tool descriptions**: Write detailed descriptions covering purpose, parameter constraints, spatial semantics, return formats, and explicit when-to-use/when-not-to-use guidance. Handle ambiguity (what "near" means, what coordinate system to expect) in the descriptions themselves.
- **Few-shot examples**: Include 3–5 examples mapping natural language queries to tool calls, dynamically selected based on query similarity. This alone can triple selection accuracy for weaker models.
- **Prompt caching**: Enable prompt caching so tool definitions are effectively free after the first turn.

**When to reconsider**: If the tool count grows beyond ~30, if you add tools spanning unrelated domains (reducing spatial context coherence), or if you integrate MCP servers bringing the total above 50 tools, then Anthropic's deferred tool loading or a vector-based retrieval layer becomes worthwhile. The architecture to migrate to is well-established: embed tool descriptions in pgvector (which you likely already run alongside PostGIS), retrieve top-5 by cosine similarity at query time, and inject only those into context. But for 19 spatial tools on a frontier model, that infrastructure is premature optimization.