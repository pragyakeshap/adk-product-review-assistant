"""Product Requirement Review Assistant using Google Cloud ADK.

Demo flow:
1. Requirement Analyzer
2. Architecture Advisor
3. Risk/Governance Reviewer + Test Case Generator in parallel
4. Final Summary Agent
"""

import os

from google.adk.agents import Agent, ParallelAgent, SequentialAgent

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

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
""",
    output_key="requirement_analysis",
)

architecture_advisor = Agent(
    name="architecture_advisor",
    model=MODEL,
    description="Recommends a cloud architecture based on the analyzed requirements.",
    instruction="""
You are a Google Cloud solution architect.

Use the requirement analysis below:
{requirement_analysis?}

Recommend a practical architecture for the solution. Include:
1. Frontend or client channel
2. Agent / orchestration layer:
Use Google Cloud ADK as the primary orchestration layer.
Explain that the demo uses:
- SequentialAgent for step-by-step workflow
- ParallelAgent for running risk review and test planning together
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
""",
    output_key="architecture_recommendation",
)

risk_governance_reviewer = Agent(
    name="risk_governance_reviewer",
    model=MODEL,
    description="Reviews privacy, security, governance, and operational risks.",
    instruction="""
You are an AI governance and risk reviewer.

Requirement analysis:
{requirement_analysis?}

Architecture recommendation:
{architecture_recommendation?}

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
""",
    output_key="risk_governance_review",
)

test_case_generator = Agent(
    name="test_case_generator",
    model=MODEL,
    description="Creates validation scenarios for the proposed AI workflow.",
    instruction="""
You are a QA lead for AI-enabled applications.

Requirement analysis:
{requirement_analysis?}

Architecture recommendation:
{architecture_recommendation?}

Generate test scenarios for this solution. Include:
1. Happy path tests
2. Edge cases
3. Security/privacy tests
4. Escalation tests
5. Observability/quality tests

Use a compact table format.
""",
    output_key="test_plan",
)

parallel_review_team = ParallelAgent(
    name="parallel_review_team",
    description="Runs risk review and test planning in parallel.",
    sub_agents=[risk_governance_reviewer, test_case_generator],
)

final_summary_agent = Agent(
    name="final_summary_agent",
    model=MODEL,
    description="Creates the final implementation-ready recommendation.",
    instruction="""
You are the final solution reviewer.

Combine the outputs below into a final executive-ready implementation recommendation.

Requirement analysis:
{requirement_analysis?}

Architecture recommendation:
{architecture_recommendation?}

Risk and governance review:
{risk_governance_review?}

Test plan:
{test_plan?}

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

Make it clear, concise, and presentation-friendly.
""",
    output_key="final_recommendation",
)

root_agent = SequentialAgent(
    name="product_requirement_review_assistant",
    description="Multi-agent workflow that reviews a product requirement and produces an implementation-ready recommendation.",
    sub_agents=[
        requirement_analyzer,
        architecture_advisor,
        parallel_review_team,
        final_summary_agent,
    ],
)
