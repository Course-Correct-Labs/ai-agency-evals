"""
Cost estimation utilities for API usage.

Provides real-time cost tracking and final summaries.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class CostRates:
    """Current API pricing (dollars per 1k tokens)."""
    # OpenAI (as of 2025)
    openai_gpt4o_mini_in: float = 0.00015
    openai_gpt4o_mini_out: float = 0.0006
    openai_gpt4_in: float = 0.03
    openai_gpt4_out: float = 0.06

    # Anthropic (as of 2025)
    anthropic_sonnet_in: float = 0.003
    anthropic_sonnet_out: float = 0.015
    anthropic_opus_in: float = 0.015
    anthropic_opus_out: float = 0.075


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Estimate API cost for a single request.

    Args:
        model: model identifier (e.g., "gpt-4", "claude-3-5-sonnet")
        prompt_tokens: input token count
        completion_tokens: output token count

    Returns:
        Estimated cost in dollars
    """
    rates = CostRates()
    model_lower = model.lower()

    # OpenAI models
    if "gpt-4o-mini" in model_lower or "gpt-4-mini" in model_lower:
        return (prompt_tokens / 1000) * rates.openai_gpt4o_mini_in + \
               (completion_tokens / 1000) * rates.openai_gpt4o_mini_out

    if "gpt-4" in model_lower:
        return (prompt_tokens / 1000) * rates.openai_gpt4_in + \
               (completion_tokens / 1000) * rates.openai_gpt4_out

    # Anthropic models
    if "sonnet" in model_lower or "claude-3-5" in model_lower:
        return (prompt_tokens / 1000) * rates.anthropic_sonnet_in + \
               (completion_tokens / 1000) * rates.anthropic_sonnet_out

    if "opus" in model_lower:
        return (prompt_tokens / 1000) * rates.anthropic_opus_in + \
               (completion_tokens / 1000) * rates.anthropic_opus_out

    # Unknown model - return 0
    return 0.0


def summarize_cost(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute total cost across all results.

    Args:
        results: list of result dicts with 'model', 'usage' keys

    Returns:
        Cost summary dict with total and per-model breakdown
    """
    total_cost = 0.0
    model_costs = {}

    for result in results:
        model = result.get('model', 'unknown')
        usage = result.get('usage', {})

        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)

        if prompt_tokens == 0 and completion_tokens == 0:
            # Try alternative key names
            prompt_tokens = usage.get('input_tokens', 0)
            completion_tokens = usage.get('output_tokens', 0)

        cost = estimate_cost(model, prompt_tokens, completion_tokens)
        total_cost += cost

        if model not in model_costs:
            model_costs[model] = {
                'cost': 0.0,
                'requests': 0,
                'tokens': 0
            }

        model_costs[model]['cost'] += cost
        model_costs[model]['requests'] += 1
        model_costs[model]['tokens'] += prompt_tokens + completion_tokens

    return {
        'total_cost': round(total_cost, 4),
        'total_requests': len(results),
        'by_model': {
            model: {
                'cost': round(data['cost'], 4),
                'requests': data['requests'],
                'tokens': data['tokens']
            }
            for model, data in model_costs.items()
        }
    }


def print_cost_summary(results: List[Dict[str, Any]], console=None) -> None:
    """
    Print formatted cost summary.

    Args:
        results: list of result dicts
        console: optional Rich console (uses print if None)
    """
    summary = summarize_cost(results)

    if console:
        console.print(f"\n[bold cyan]💰 Cost Summary[/bold cyan]")
        console.print(f"  Total cost: ${summary['total_cost']:.4f}")
        console.print(f"  Total requests: {summary['total_requests']}")

        if summary['by_model']:
            console.print(f"\n  [bold]By model:[/bold]")
            for model, data in summary['by_model'].items():
                console.print(f"    {model}: ${data['cost']:.4f} ({data['requests']} req, {data['tokens']:,} tok)")
    else:
        print(f"\n💰 Cost Summary")
        print(f"  Total cost: ${summary['total_cost']:.4f}")
        print(f"  Total requests: {summary['total_requests']}")

        if summary['by_model']:
            print(f"\n  By model:")
            for model, data in summary['by_model'].items():
                print(f"    {model}: ${data['cost']:.4f} ({data['requests']} req, {data['tokens']:,} tok)")
