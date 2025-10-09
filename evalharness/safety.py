"""
Safety utilities and validation checks.

Ensures experiments run within bounds and don't produce harmful outputs.
"""

import re
from typing import List, Dict, Any, Optional
from rich.console import Console

console = Console()


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validate that config contains all required keys.

    Args:
        config: configuration dictionary
        required_keys: list of required key names

    Returns:
        True if valid, raises ValueError otherwise
    """
    missing_keys = [key for key in required_keys if key not in config]

    if missing_keys:
        raise ValueError(f"Missing required config keys: {missing_keys}")

    console.print("[green]✓[/green] Config validation passed")
    return True


def sanitize_prompt(prompt: str, max_length: int = 2000) -> str:
    """
    Sanitize prompt text for safety and length.

    Args:
        prompt: input prompt text
        max_length: maximum allowed length

    Returns:
        Sanitized prompt
    """
    # Remove potential injection patterns
    sanitized = re.sub(r'<\|.*?\|>', '', prompt)  # Remove special tokens
    sanitized = sanitized.strip()

    # Truncate if too long
    if len(sanitized) > max_length:
        console.print(f"[yellow]⚠[/yellow] Truncating prompt from {len(sanitized)} to {max_length} chars")
        sanitized = sanitized[:max_length]

    return sanitized


def check_response_safety(response: str, max_length: int = 5000) -> bool:
    """
    Check if response is within safety bounds.

    Args:
        response: model response text
        max_length: maximum allowed response length

    Returns:
        True if safe, False otherwise
    """
    if len(response) > max_length:
        console.print(f"[yellow]⚠[/yellow] Response exceeds max length: {len(response)} > {max_length}")
        return False

    # Add additional safety checks as needed (e.g., content filters)
    return True


def validate_experiment_scope(num_trials: int, max_trials: int = 1000) -> bool:
    """
    Validate that experiment scope is reasonable.

    Args:
        num_trials: requested number of trials
        max_trials: maximum allowed trials

    Returns:
        True if valid, raises ValueError otherwise
    """
    if num_trials <= 0:
        raise ValueError(f"Number of trials must be positive: {num_trials}")

    if num_trials > max_trials:
        raise ValueError(f"Number of trials exceeds maximum: {num_trials} > {max_trials}")

    console.print(f"[green]✓[/green] Experiment scope validated: {num_trials} trials")
    return True


def check_output_integrity(results: List[Dict[str, Any]], expected_keys: List[str]) -> bool:
    """
    Check that all results contain expected keys.

    Args:
        results: list of result dictionaries
        expected_keys: list of expected key names

    Returns:
        True if all results are valid, False otherwise
    """
    for i, result in enumerate(results):
        missing_keys = [key for key in expected_keys if key not in result]
        if missing_keys:
            console.print(f"[red]✗[/red] Result {i} missing keys: {missing_keys}")
            return False

    console.print(f"[green]✓[/green] All {len(results)} results have valid structure")
    return True


def estimate_cost(num_requests: int, tokens_per_request: int = 500,
                 cost_per_1k_tokens: float = 0.01) -> float:
    """
    Estimate API cost for experiment.

    Args:
        num_requests: number of API requests
        tokens_per_request: estimated tokens per request
        cost_per_1k_tokens: cost per 1000 tokens

    Returns:
        Estimated cost in dollars
    """
    total_tokens = num_requests * tokens_per_request
    cost = (total_tokens / 1000) * cost_per_1k_tokens

    console.print(f"[cyan]💰 Estimated cost: ${cost:.2f} ({total_tokens:,} tokens)[/cyan]")
    return cost


def warn_if_expensive(num_requests: int, cost_threshold: float = 5.0) -> None:
    """
    Warn user if experiment is likely to be expensive.

    Args:
        num_requests: number of API requests
        cost_threshold: warning threshold in dollars
    """
    estimated_cost = estimate_cost(num_requests)

    if estimated_cost > cost_threshold:
        console.print(f"[yellow]⚠ WARNING: Estimated cost ${estimated_cost:.2f} exceeds threshold ${cost_threshold:.2f}[/yellow]")
        console.print("[yellow]  Consider using MOCK_MODE=true for testing[/yellow]")
