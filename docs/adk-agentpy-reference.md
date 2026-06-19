# ADK Agent.py Reference

This document explains how `product_review_agent/agent.py` is built using Google ADK libraries, and includes a reusable starter template.

## 1. Core ADK Libraries Used

The file is built with these ADK primitives:

- `Agent`: defines an LLM-powered node with a role, instruction, and optional state output.
- `Workflow`: defines a graph of nodes.
- `Edge`: defines directed transitions between nodes in a workflow graph.
- `JoinNode`: merges parallel branches into one continuation point.
- `@node`: creates lightweight function nodes for state preparation.
- `START`: sentinel entry node for each workflow.

## 2. High-Level Architecture in agent.py

The implementation uses a mixed orchestration pattern:

1. Sequential step: requirement analysis
2. Sequential step: architecture recommendation
3. Nested parallel workflow:
- risk/governance review
- test plan generation
4. Sequential step: final summary

Conceptually:

```text
START
  -> requirement_analyzer
      -> prepare_architecture_input
          -> architecture_advisor
              -> parallel_review_team
                  -> prepare_final_input
                      -> final_summary_agent
```

Inside `parallel_review_team`:

```text
START -> prepare_risk_input -> risk_governance_reviewer -> join_reviews
START -> prepare_test_input -> test_case_generator      -> join_reviews
```

## 3. Why FunctionNodes (@node) Are Used

The `prepare_*` functions read previous outputs from workflow state (for example, `ctx.state.get("requirement_analysis")`) and send them as user-message content to downstream agents.

Benefits:

- keeps agent system instructions static
- improves Gemini context caching behavior
- avoids performance warnings about changing system prompts
- makes state handoff explicit and easy to debug

## 4. State Flow Pattern

Each agent writes output to state via `output_key`.

Example state keys in your file:

- `requirement_analysis`
- `architecture_recommendation`
- `risk_governance_review`
- `test_plan`
- `final_recommendation`

Downstream nodes consume these keys using `ctx.state.get(...)`.

## 5. Reusable Minimal Starter Template

Use this template to create new ADK workflow projects quickly.

```python
import os
from google.adk.agents import Agent
from google.adk.workflow import Workflow, Edge, JoinNode, node
from google.adk.workflow._base_node import START

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# 1) First agent
analyzer = Agent(
    name="analyzer",
    model=MODEL,
    description="Analyzes raw user input.",
    instruction="""
You are an analyst.
Summarize user requirement in 3-5 bullets.
""",
    output_key="analysis",
)

# 2) Prep node to pass state to next agent
@node
def prepare_design_input(ctx):
    return f"Analysis:\n{ctx.state.get('analysis', '')}"

# 3) Second agent
designer = Agent(
    name="designer",
    model=MODEL,
    description="Creates architecture suggestion.",
    instruction="""
You are a solution architect.
Use the user message to propose architecture.
""",
    output_key="design",
)

# 4) Parallel branch agents
risk = Agent(
    name="risk",
    model=MODEL,
    description="Reviews risks.",
    instruction="Identify top risks and controls.",
    output_key="risk_review",
)

tests = Agent(
    name="tests",
    model=MODEL,
    description="Creates test plan.",
    instruction="Create a compact test plan table.",
    output_key="test_plan",
)

@node
def prepare_parallel_input(ctx):
    return (
        f"Analysis:\n{ctx.state.get('analysis', '')}\n\n"
        f"Design:\n{ctx.state.get('design', '')}"
    )

join_parallel = JoinNode(name="join_parallel")

parallel_work = Workflow(
    name="parallel_work",
    edges=[
        Edge(from_node=START, to_node=prepare_parallel_input),
        Edge(from_node=prepare_parallel_input, to_node=risk),
        Edge(from_node=prepare_parallel_input, to_node=tests),
        Edge(from_node=risk, to_node=join_parallel),
        Edge(from_node=tests, to_node=join_parallel),
    ],
)

# 5) Final agent
@node
def prepare_final_input(ctx):
    return (
        f"Analysis:\n{ctx.state.get('analysis', '')}\n\n"
        f"Design:\n{ctx.state.get('design', '')}\n\n"
        f"Risk:\n{ctx.state.get('risk_review', '')}\n\n"
        f"Tests:\n{ctx.state.get('test_plan', '')}"
    )

final = Agent(
    name="final",
    model=MODEL,
    description="Produces final recommendation.",
    instruction="Generate a concise final recommendation.",
    output_key="final_output",
)

# 6) Root workflow (entry point)
root_agent = Workflow(
    name="demo_workflow",
    edges=[
        Edge(from_node=START, to_node=analyzer),
        Edge(from_node=analyzer, to_node=prepare_design_input),
        Edge(from_node=prepare_design_input, to_node=designer),
        Edge(from_node=designer, to_node=parallel_work),
        Edge(from_node=parallel_work, to_node=prepare_final_input),
        Edge(from_node=prepare_final_input, to_node=final),
    ],
)
```

## 6. Practical Notes

- Keep instructions stable for better prompt caching.
- Use `output_key` consistently and keep key names simple.
- Prefer function nodes for state composition instead of embedding dynamic placeholders in instructions.
- Keep workflow edges explicit; this makes debugging much easier.
- Keep one clear `root_agent` as the app entry point.

## 7. Mapping to Your Current File

Current file: `product_review_agent/agent.py`

The current implementation follows this exact pattern, with domain-specific prompts for:

- requirements analysis
- cloud architecture recommendation
- risk/governance review
- test generation
- final executive summary
