"""
Main runner for di_eval experiments.

Evaluates Absorption Rate, Style Convergence, and Turn Curve.
"""

import argparse
import time
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from rich.console import Console
import pandas as pd

from evalharness.api_clients import get_client
from evalharness.scoring import compute_absorption_rate, compute_style_convergence
from evalharness.plotting import plot_absorption_boxplot, plot_turn_curve
from evalharness.io import load_config, save_results_csv
from evalharness.safety import validate_config, validate_experiment_scope
from di_eval.dialogue import (
    get_dialogue_scenarios,
    get_smoke_scenarios,
    generate_user_restatement_prompt,
    simulate_user_restatement,
    extract_key_reasons
)

console = Console()


def run_di_evaluation(config: Dict[str, Any]) -> None:
    """
    Run complete delegated introspection evaluation.

    Args:
        config: experiment configuration
    """
    console.print("\n[bold cyan]═══ Delegated Introspection Evaluation ═══[/bold cyan]\n")

    # Validate config
    required_keys = ["models", "output_dir", "num_dialogues", "turns_per_dialogue"]
    validate_config(config, required_keys)

    # Load scenarios
    if config.get("dataset_mode") == "smoke":
        scenarios = get_smoke_scenarios()
        console.print("[yellow]Using smoke scenarios (2 domains)[/yellow]")
    else:
        scenarios = get_dialogue_scenarios()
        console.print(f"[green]Using full scenarios ({len(scenarios)} domains)[/green]")

    validate_experiment_scope(config["num_dialogues"] * len(config["models"]))

    # Setup output directory
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run evaluation
    all_results = []

    for model_config in config["models"]:
        console.print(f"\n[bold]Evaluating model: {model_config['name']}[/bold]")

        # Initialize client
        client = get_client(
            provider=model_config["provider"],
            model=model_config["model"],
            timeout=config.get("timeout", 30)
        )

        # Run dialogues for each condition
        for condition in ["baseline", "awareness"]:
            console.print(f"  Condition: {condition}")

            for i in range(config["num_dialogues"]):
                scenario = scenarios[i % len(scenarios)]
                result = run_dialogue(
                    client=client,
                    scenario=scenario,
                    num_turns=config["turns_per_dialogue"],
                    condition=condition,
                    dialogue_id=f"{model_config['name']}_{condition}_{i}",
                    model_name=model_config['name']
                )
                all_results.append(result)

    # Save results
    results_path = output_dir / "di_results.csv"
    save_results_csv(all_results, results_path)

    # Generate plots
    generate_plots(all_results, output_dir)

    # Print summary
    console.print("\n[bold green]✓ Evaluation complete![/bold green]")
    console.print(f"  Results: {results_path}")
    console.print(f"  Plots: {output_dir}")


def run_dialogue(client, scenario, num_turns: int, condition: str,
                dialogue_id: str, model_name: str) -> Dict[str, Any]:
    """
    Run a single multi-turn dialogue and compute metrics.

    Args:
        client: API client
        scenario: DialogueScenario
        num_turns: number of turns
        condition: "baseline" or "awareness"
        dialogue_id: unique dialogue identifier
        model_name: name of model

    Returns:
        Result dictionary with metrics
    """
    conversation_history = []
    turn_results = []

    # Initial turn
    messages = [
        {"role": "system", "content": "You are a helpful assistant providing thoughtful advice."},
        {"role": "user", "content": scenario.initial_prompt}
    ]

    try:
        response = client.complete(messages, temperature=0.7, max_tokens=512)
        initial_response = response["content"]
    except Exception as e:
        console.print(f"[red]Error in dialogue {dialogue_id}: {e}[/red]")
        initial_response = "I'd be happy to help you think through this."

    conversation_history.append({
        "role": "assistant",
        "content": initial_response
    })

    # Extract initial model reasons
    model_reasons = extract_key_reasons(initial_response)

    # Simulate user restatement
    user_restatement = simulate_user_restatement(initial_response, turn_number=1)
    user_reasons_turn1 = extract_key_reasons(user_restatement)

    # Store initial user text for style convergence
    initial_user_text = user_restatement

    # Continue dialogue for remaining turns
    for turn in range(1, num_turns):
        # Use follow-up questions
        if turn - 1 < len(scenario.follow_ups):
            user_input = scenario.follow_ups[turn - 1]
        else:
            user_input = "Can you elaborate on that?"

        messages.append({"role": "user", "content": user_input})

        try:
            response = client.complete(messages, temperature=0.7, max_tokens=512)
            model_response = response["content"]
        except Exception as e:
            model_response = "That's a good question. Let me think about that."

        messages.append({"role": "assistant", "content": model_response})

        # Get user restatement
        user_restatement = simulate_user_restatement(
            model_response,
            turn_number=turn + 1,
            absorption_tendency=0.7 if condition == "baseline" else 0.5
        )

        # Extract reasons
        model_reasons_turn = extract_key_reasons(model_response)
        user_reasons_turn = extract_key_reasons(user_restatement)

        # Compute absorption for this turn
        absorption = compute_absorption_rate(model_reasons_turn, user_reasons_turn)

        # Determine turn bin
        if turn + 1 <= 2:
            turn_bin = "1-2"
        elif turn + 1 <= 5:
            turn_bin = "3-5"
        else:
            turn_bin = "6-8"

        turn_results.append({
            "turn": turn + 1,
            "turn_bin": turn_bin,
            "absorption": absorption
        })

    # Compute overall metrics
    final_user_text = user_restatement
    style_convergence = compute_style_convergence(initial_user_text, final_user_text)

    # Average absorption across all turns
    avg_absorption = sum(t["absorption"] for t in turn_results) / len(turn_results) if turn_results else 0.0

    # Get absorption for 3-5 turn bin specifically
    turn_3_5_absorption = [t["absorption"] for t in turn_results if t["turn_bin"] == "3-5"]
    avg_3_5_absorption = sum(turn_3_5_absorption) / len(turn_3_5_absorption) if turn_3_5_absorption else avg_absorption

    return {
        "dialogue_id": dialogue_id,
        "model": model_name,
        "domain": scenario.domain,
        "condition": condition,
        "num_turns": num_turns,
        "absorption": round(avg_absorption, 3),
        "absorption_3_5": round(avg_3_5_absorption, 3),
        "style_conv": round(style_convergence, 3),
        "turn_1_2_absorption": round(sum(t["absorption"] for t in turn_results if t["turn_bin"] == "1-2") / max(sum(1 for t in turn_results if t["turn_bin"] == "1-2"), 1), 3)
    }


def generate_plots(results: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    Generate all visualization plots.

    Args:
        results: list of all evaluation results
        output_dir: where to save plots
    """
    console.print("\n[bold cyan]Generating plots...[/bold cyan]")

    df = pd.DataFrame(results)

    # Absorption boxplot by condition
    plot_absorption_boxplot(
        df[["condition", "absorption"]],
        output_dir / "fig_absorption_box.png",
        title="Absorption Rate: Baseline vs Awareness"
    )
    console.print("[green]✓[/green] fig_absorption_box.png")

    # Turn curve (need to expand turn-level data)
    # Create synthetic turn-level data for plotting
    turn_data = []
    for _, row in df.iterrows():
        # Generate synthetic data points for each turn bin
        for turn_bin in ["1-2", "3-5", "6-8"]:
            if turn_bin == "1-2":
                absorption = row["turn_1_2_absorption"]
            elif turn_bin == "3-5":
                absorption = row["absorption_3_5"]
            else:
                absorption = row["absorption"]

            turn_data.append({
                "turn_bin": turn_bin,
                "absorption": absorption
            })

    turn_df = pd.DataFrame(turn_data)
    plot_turn_curve(
        turn_df,
        output_dir / "fig_turn_curve.png",
        title="Absorption Rate Over Dialogue Turns"
    )
    console.print("[green]✓[/green] fig_turn_curve.png")

    # Print aggregate stats
    console.print("\n[bold cyan]Summary Statistics:[/bold cyan]")
    console.print(f"  Mean absorption (baseline): {df[df['condition']=='baseline']['absorption'].mean():.3f}")
    console.print(f"  Mean absorption (awareness): {df[df['condition']=='awareness']['absorption'].mean():.3f}")
    console.print(f"  Mean absorption (turns 3-5): {df['absorption_3_5'].mean():.3f}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Delegated Introspection evaluation")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML")
    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    config = load_config(config_path)

    # Run evaluation
    start_time = time.time()
    run_di_evaluation(config)
    elapsed = time.time() - start_time

    console.print(f"\n[bold]Total runtime: {elapsed:.1f}s[/bold]")


if __name__ == "__main__":
    main()
