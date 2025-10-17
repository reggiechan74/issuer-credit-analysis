#!/usr/bin/env python3
"""
Phase 4: Credit Analysis with Slim Agent

This script:
1. Loads calculated metrics from Phase 3
2. Invokes issuer_due_diligence_expert_slim agent
3. Generates qualitative credit assessment
4. Outputs credit analysis markdown

IMPORTANT: This script invokes a Claude Code sub-agent.
It must be run within Claude Code environment (not standalone Python).
"""

import json
import sys
from pathlib import Path


def load_metrics(metrics_path):
    """
    Load calculated metrics from Phase 3

    Args:
        metrics_path: Path to Phase 3 metrics JSON

    Returns:
        dict: Metrics data

    Raises:
        FileNotFoundError: If metrics file doesn't exist
        json.JSONDecodeError: If metrics file is invalid JSON
    """
    metrics_path = Path(metrics_path)

    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Metrics file not found: {metrics_path}\n"
            f"Run Phase 3 first to generate calculated metrics."
        )

    print(f"📊 Loading metrics from: {metrics_path}")

    with open(metrics_path, 'r') as f:
        metrics = json.load(f)

    # Validate required fields
    required_fields = ['issuer_name', 'reporting_date']
    missing = [f for f in required_fields if f not in metrics]

    if missing:
        raise ValueError(
            f"Metrics file missing required fields: {missing}\n"
            f"Ensure Phase 3 completed successfully."
        )

    print(f"✓ Loaded metrics for: {metrics['issuer_name']}")
    print(f"✓ Reporting date: {metrics['reporting_date']}")

    return metrics


def create_agent_prompt(metrics):
    """
    Create detailed prompt for slim agent

    Args:
        metrics: Dictionary of calculated metrics

    Returns:
        str: Agent prompt
    """

    metrics_json = json.dumps(metrics, indent=2)

    prompt = f"""You are tasked with performing qualitative credit analysis for a real estate issuer.

**Issuer:** {metrics['issuer_name']}
**Reporting Date:** {metrics['reporting_date']}
**Report Period:** {metrics.get('report_period', 'Unknown')}

You have been provided with **pre-calculated financial metrics** from Phase 3 of the analysis pipeline.

## Calculated Metrics (JSON)

```json
{metrics_json}
```

## Your Task

Perform comprehensive qualitative credit assessment following the 5-factor rating scorecard methodology.

### Required Output Sections

1. **Executive Summary**
   - Scorecard-indicated rating (Aaa/Aa/A/Baa/Ba/B)
   - One-paragraph credit story
   - Key credit drivers

2. **Credit Strengths** (3-5 bullet points)
   - Quantified using the metrics provided
   - Reference specific numbers

3. **Credit Challenges** (2-4 bullet points)
   - Key risks identified
   - Note mitigants where applicable

4. **Rating Outlook** (Stable/Positive/Negative with justification)

5. **Upgrade Factors** (specific thresholds)

6. **Downgrade Factors** (quantified triggers)

7. **5-Factor Scorecard Analysis**
   - Factor 1: Scale (5%)
   - Factor 2: Business Profile (25%)
   - Factor 3: Access to Capital (20%)
   - Factor 4: Leverage & Coverage (35%)
   - Factor 5: Financial Policy (15%)

   Present in table format with scores and rationale.

8. **Key Observations**
   - REIT-specific metrics (FFO, AFFO, payout ratios)
   - Portfolio quality (occupancy, NOI growth)
   - Unusual ratios or trends

### Important Guidelines

- **Reference actual metrics:** Don't say "high leverage" - say "Debt/Assets of 41.1%"
- **Use benchmarks:** Compare to rating category thresholds
- **Be specific:** Provide concrete numbers and thresholds
- **Evidence quality:** Note when evidence is strong/moderate/limited
- **Professional caveats:** This is analysis, not investment advice

### Output Format

Generate a well-structured markdown document (800-1,500 words) with clear sections and quantified assessments.

**Focus on qualitative credit assessment - the calculations are already done.**

Begin your analysis:
"""

    return prompt


def invoke_agent(metrics, output_path):
    """
    Invoke slim agent for credit analysis

    NOTE: This function provides a prompt that should be used
    with Claude Code's Task tool to invoke the issuer_due_diligence_expert_slim agent.

    Args:
        metrics: Calculated metrics dictionary
        output_path: Path to save analysis output

    Returns:
        str: Path to output file
    """

    print("\n" + "=" * 70)
    print("PHASE 4: CREDIT ANALYSIS (SLIM AGENT)")
    print("=" * 70)

    # Create agent prompt
    agent_prompt = create_agent_prompt(metrics)

    # Display invocation instructions
    print("\n🤖 Invoking issuer_due_diligence_expert_slim agent...")
    print("\n" + "=" * 70)
    print("AGENT INVOCATION DETAILS")
    print("=" * 70)
    print(f"Agent: issuer_due_diligence_expert_slim")
    print(f"Task: Qualitative credit assessment")
    print(f"Input: {len(json.dumps(metrics))} characters of metrics")
    print(f"Output: {output_path}")
    print("=" * 70)

    # IMPORTANT: In actual usage, this script would be called from Claude Code
    # which can invoke sub-agents via the Task tool.
    #
    # For standalone testing, we provide the prompt that would be passed to the agent.

    # Save the prompt to a file for manual agent invocation if needed
    prompt_path = Path(output_path).parent / "phase4_agent_prompt.txt"
    with open(prompt_path, 'w') as f:
        f.write(agent_prompt)

    print(f"\n📝 Agent prompt saved to: {prompt_path}")
    print("\nTo invoke the agent manually:")
    print(f"1. Copy the prompt from: {prompt_path}")
    print(f"2. Use Claude Code Task tool with subagent_type: issuer_due_diligence_expert_slim")
    print(f"3. Save agent output to: {output_path}")

    return str(prompt_path)


def main():
    """Main execution - command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Phase 4: Credit Analysis with Slim Agent',
        epilog='Example: python analyze_credit_with_agent.py metrics.json'
    )
    parser.add_argument(
        'metrics_json',
        help='Path to Phase 3 calculated metrics JSON (REQUIRED)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output path for credit analysis (default: auto-generated from metrics path)'
    )

    args = parser.parse_args()

    # Auto-generate output path if not specified (same folder as metrics)
    if args.output is None:
        metrics_path = Path(args.metrics_json)
        args.output = str(metrics_path.parent / 'phase4_credit_analysis.md')

    print("=" * 70)
    print("PHASE 4: CREDIT ANALYSIS WITH SLIM AGENT")
    print("=" * 70)

    try:
        # Load metrics
        metrics = load_metrics(args.metrics_json)

        # Invoke agent (generates prompt for manual invocation)
        prompt_path = invoke_agent(metrics, args.output)

        print("\n✅ Phase 4 preparation complete")
        print(f"\n📋 Next steps:")
        print(f"   1. Review prompt at: {prompt_path}")
        print(f"   2. Invoke agent via Claude Code Task tool")
        print(f"   3. Save agent output to: {args.output}")
        print(f"   4. Proceed to Phase 5 (report generation)")

        # Exit code 0 (success) even though agent hasn't run yet
        # This is preparation for agent invocation
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Invalid JSON in metrics file: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
