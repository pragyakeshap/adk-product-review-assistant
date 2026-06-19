"""Product Requirement Review Assistant using Google Cloud ADK.

Flow:
1. Requirement Analyzer
2. Architecture Advisor
3. Risk/Governance Reviewer + Test Case Generator in parallel
4. Final Summary Agent
"""

import os

from google.adk.agents import Agent
# Workflow replaces the deprecated SequentialAgent and ParallelAgent.
# - Edge: defines directed connections between nodes in the graph
# - JoinNode: merges parallel branches back into a single flow
# - node: decorator to create a lightweight FunctionNode for state prep
from google.adk.workflow import Edge, JoinNode, Workflow, node
# START is a sentinel node representing the entry point of a Workflow graph
from google.adk.workflow._base_node import START

# Model is configurable via environment variable; defaults to gemini-2.5-flash.
# Gemini 2.5 Flash is cost-effective for this multi-step pipeline.
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Requirement Analyzer
# Receives the raw user input and breaks it into a structured analysis.
# This is the first agent in the sequential pipeline.
# Note: No {state?} placeholders in instruction — system prompt stays static
# to avoid Gemini context cache misses and latency warnings.
# ─────────────────────────────────────────────────────────────────────────────
requirement_analyzer = Agent(
    name="requirement_analyzer",
    model=MODEL,
    description="Breaks a product requirement into clear functional and non-functional requirements.",
    instruction="""
You are a senior product and requirements analyst.

Given the user's product requirement, produce a concise structured analysis with:
1. Business goal
2. Primary users
3. Functional requirements
4. Non-functional requirements
5. Assumptions
6. Open questions

Keep the response concise.
Use 5-7 bullets maximum.
Focus on ADK multi-agent orchestration.
Avoid long enterprise implementation tables unless explicitly asked.
Make the output presentation-demo friendly.
Format each section as:
**Section name:**
[content on the next line]
""",
    # output_key saves the agent's response into session state under this key,
    # making it available to downstream agents via ctx.state.get(...)
    output_key="requirement_analysis",
)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Architecture Advisor
# Recommends a Google Cloud + ADK architecture based on the requirements.
#
# Pattern: FunctionNode (prepare_architecture_input) → Agent (architecture_advisor)
# The FunctionNode reads state and injects it as the user message so that
# the Agent's system instruction remains static (cache-friendly).
# ─────────────────────────────────────────────────────────────────────────────
architecture_advisor = Agent(
    name="architecture_advisor",
    model=MODEL,
    description="Recommends a cloud architecture based on the analyzed requirements.",
    instruction="""
You are a Google Cloud solution architect.

Recommend a practical architecture for the solution described in the user message. Include:
1. Frontend or client channel
2. Agent / orchestration layer:
Use Google Cloud ADK Workflow as the primary orchestration layer.
Explain that the demo uses:
- A root Workflow to coordinate the full process
- Edges to define execution order
- A nested Workflow to run risk review and test planning in parallel
- A JoinNode to merge parallel branches before final summary
- Specialized ADK agents for requirements, architecture, risk, testing, and final summary

Cloud Run should be described only as an optional deployment target for the ADK app.
3. Model layer using Gemini / Vertex AI
4. Data sources and retrieval approach
5. Human escalation path
6. Observability and logging
7. Deployment option on Google Cloud

Keep it concise enough to explain in a live demo.
Recommend an ADK-based architecture first.
Mention Vertex AI / Gemini, Cloud Run, Cloud Logging, and optional backend APIs.
Do not make Dialogflow CX the main orchestration layer.
Format each section as:
**Section name:**
[content on the next line]
""",
    output_key="architecture_recommendation",
)

# FunctionNode: reads requirement_analysis from state and passes it as the
# user message to architecture_advisor. Keeps the system prompt static.
@node
def prepare_architecture_input(ctx):
    return ctx.state.get("requirement_analysis", "")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3A: Risk & Governance Reviewer  (runs in parallel with Step 3B)
# Reviews privacy, security, hallucination, escalation, and audit risks.
# ─────────────────────────────────────────────────────────────────────────────
risk_governance_reviewer = Agent(
    name="risk_governance_reviewer",
    model=MODEL,
    description="Reviews privacy, security, governance, and operational risks.",
    instruction="""
You are an AI governance and risk reviewer.

Review the requirement analysis and architecture recommendation provided in the user message.

Identify key risks and recommended controls. Cover:
1. Privacy and sensitive data
2. Security and access control
3. Hallucination or incorrect response risk
4. Human escalation requirements
5. Auditability and monitoring

Return a practical risk-control checklist.
Summarize the outputs from prior agents in 4 sections:
1. Recommended agent workflow
2. Google Cloud services
3. Key risks and controls
4. Validation plan

Keep it under 300 words.
Format each section as:
**Section name:**
[content on the next line]
""",
    output_key="risk_governance_review",
)

# FunctionNode: builds the user message for risk_governance_reviewer by
# combining requirement_analysis and architecture_recommendation from state.
@node
def prepare_risk_input(ctx):
    return (
        f"Requirement analysis:\n{ctx.state.get('requirement_analysis', '')}\n\n"
        f"Architecture recommendation:\n{ctx.state.get('architecture_recommendation', '')}"
    )

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3B: Test Case Generator  (runs in parallel with Step 3A)
# Generates a structured test plan covering happy path, edge cases,
# security, escalation, and observability scenarios.
# ─────────────────────────────────────────────────────────────────────────────
test_case_generator = Agent(
    name="test_case_generator",
    model=MODEL,
    description="Creates validation scenarios for the proposed AI workflow.",
    instruction="""
You are a QA lead for AI-enabled applications.

Review the requirement analysis and architecture recommendation provided in the user message.

Generate test scenarios for this solution. Include:
1. Happy path tests
2. Edge cases
3. Security/privacy tests
4. Escalation tests
5. Observability/quality tests

Use a compact table format with columns: Test Type | Scenario | Expected Result
""",
    output_key="test_plan",
)

# FunctionNode: builds the user message for test_case_generator — same
# inputs as the risk reviewer since both run in parallel from the same state.
@node
def prepare_test_input(ctx):
    return (
        f"Requirement analysis:\n{ctx.state.get('requirement_analysis', '')}\n\n"
        f"Architecture recommendation:\n{ctx.state.get('architecture_recommendation', '')}"
    )

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Parallel Review Team (nested Workflow)
# Runs risk review and test planning simultaneously using fan-out edges.
# JoinNode merges both branches before the pipeline continues to Step 4.
#
# Graph shape:
#   START ──► prepare_risk_input ──► risk_governance_reviewer ──► join
#   START ──► prepare_test_input ──► test_case_generator      ──► join
# ─────────────────────────────────────────────────────────────────────────────
_join_reviews = JoinNode(name="join_reviews")

parallel_review_team = Workflow(
    name="parallel_review_team",
    description="Runs risk review and test planning in parallel.",
    edges=[
        Edge(from_node=START, to_node=prepare_risk_input),
        Edge(from_node=START, to_node=prepare_test_input),
        Edge(from_node=prepare_risk_input, to_node=risk_governance_reviewer),
        Edge(from_node=prepare_test_input, to_node=test_case_generator),
        Edge(from_node=risk_governance_reviewer, to_node=_join_reviews),
        Edge(from_node=test_case_generator, to_node=_join_reviews),
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Final Summary Agent
# Aggregates all prior outputs and produces an executive-ready recommendation.
# ─────────────────────────────────────────────────────────────────────────────
final_summary_agent = Agent(
    name="final_summary_agent",
    model=MODEL,
    description="Creates the final implementation-ready recommendation.",
    instruction="""
You are the final solution reviewer.

Combine the outputs provided in the user message into a final executive-ready implementation recommendation.

Final output format:
1. Recommended solution summary
2. Proposed agent workflow
3. Google Cloud services to use
4. Key risks and controls
5. Validation plan

Do not repeat earlier sections.
Do not include implementation phases.
Keep the final recommendation under 250 words.
Focus on ADK multi-agent orchestration.
Format each section as:
**Section name:**
[content on the next line]

Make it clear, concise, and presentation-friendly.
""",
    output_key="final_recommendation",
)

# FunctionNode: collects all four prior outputs from state and combines them
# into a single user message for the final summary agent.
@node
def prepare_final_input(ctx):
    return (
        f"Requirement analysis:\n{ctx.state.get('requirement_analysis', '')}\n\n"
        f"Architecture recommendation:\n{ctx.state.get('architecture_recommendation', '')}\n\n"
        f"Risk and governance review:\n{ctx.state.get('risk_governance_review', '')}\n\n"
        f"Test plan:\n{ctx.state.get('test_plan', '')}"
    )

# ─────────────────────────────────────────────────────────────────────────────
# ROOT AGENT: Sequential Workflow (entry point for ADK)
# Orchestrates the full pipeline using a graph of directed edges.
#
# Graph shape (sequential with one nested parallel step):
#   START
#     ──► requirement_analyzer
#         ──► prepare_architecture_input
#             ──► architecture_advisor
#                 ──► parallel_review_team  (nested Workflow — runs steps 3A+3B)
#                     ──► prepare_final_input
#                         ──► final_summary_agent
#
# ADK discovers root_agent as the entry point via the variable name convention.
# ─────────────────────────────────────────────────────────────────────────────
root_agent = Workflow(
    name="product_requirement_review_assistant",
    description="Multi-agent workflow that reviews a product requirement and produces an implementation-ready recommendation.",
    edges=[
        Edge(from_node=START, to_node=requirement_analyzer),
        Edge(from_node=requirement_analyzer, to_node=prepare_architecture_input),
        Edge(from_node=prepare_architecture_input, to_node=architecture_advisor),
        Edge(from_node=architecture_advisor, to_node=parallel_review_team),
        Edge(from_node=parallel_review_team, to_node=prepare_final_input),
        Edge(from_node=prepare_final_input, to_node=final_summary_agent),
    ],
)
