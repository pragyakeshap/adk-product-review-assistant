# Live Demo Script

## Opening line

"Instead of asking one large prompt to do everything, we will create a small team of specialized agents. Each agent has a clear role, and ADK orchestrates the workflow."

## Demo steps

1. Open the repo.
2. Show `product_review_agent/agent.py`.
3. Point out the four main roles:
   - Requirement Analyzer
   - Architecture Advisor
   - Risk/Governance Reviewer
   - Test Case Generator
   - Final Summary Agent
4. Run:

```bash
adk web
```

5. Select `product_review_agent`.
6. Paste the sample customer-support chatbot requirement.
7. Explain the output as the workflow progresses.

## Key message

"The important part is not just that we used multiple agents. The important part is that each agent has a narrow responsibility, state is passed between steps, and governance/testing are built into the workflow instead of added later."
