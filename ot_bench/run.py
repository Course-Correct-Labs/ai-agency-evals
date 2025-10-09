"""
Main runner for ot_bench experiments.

Evaluates Self-Initiation, Temporal Drift, and Elasticity.
"""

import argparse
import time
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from rich.console import Console
import pandas as pd

from evalharness.api_clients import get_client
from evalharness.scoring import (
    compute_temporal_error,
    compute_elasticity,
    detect_self_initiation
)
from evalharness.plotting import (
    plot_temporal_error_histogram,
    plot_self_initiation_bar
)
from evalharness.io import load_config, save_results_csv
from evalharness.safety import validate_config, validate_experiment_scope
from ot_bench.experiments import (
    get_smoke_trials,
    get_full_trials,
    get_self_initiation_prompt,
    get_estimation_prompt,
    parse_time_estimate
)

console = Console()


def run_ot_evaluation(config: Dict[str, Any]) -> None:
    """
    Run complete Observer-Time evaluation.

    Args:
        config: experiment configuration
    """
    console.print("\n[bold cyan]═══ Observer-Time Evaluation ═══[/bold cyan]\n")

    # Validate config
    required_keys = ["models", "output_dir", "trial_mode"]
    validate_config(config, required_keys)

    # Load trials
    if config["trial_mode"] == "smoke":
        trials = get_smoke_trials()
        console.print("[yellow]Using smoke trials (3 trials)[/yellow]")
    else:
        trials = get_full_trials()
        console.print(f"[green]Using full trials ({len(trials)} trials)[/green]")

    validate_experiment_scope(len(trials) * len(config["models"]))

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

        # Run each trial
        for trial in tqdm(trials, desc=f"{model_config['name']}"):
            result = run_trial(
                client=client,
                trial=trial,
                model_name=model_config['name'],
                dry_run=config.get("dry_run", False)
            )
            all_results.append(result)

    # Save results
    results_path = output_dir / "ot_results.csv"
    save_results_csv(all_results, results_path)

    # Generate plots
    generate_plots(all_results, output_dir)

    # Print summary
    print_summary(all_results)

    console.print("\n[bold green]✓ Evaluation complete![/bold green]")
    console.print(f"  Results: {results_path}")
    console.print(f"  Plots: {output_dir}")


def run_trial(client, trial, model_name: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run a single temporal trial.

    Args:
        client: API client
        trial: TemporalTrial object
        model_name: name of model
        dry_run: if True, skip actual waits (for CI)

    Returns:
        Result dictionary
    """
    result = {
        "trial_id": trial.trial_id,
        "model": model_name,
        "trial_type": trial.trial_type,
        "distractor": trial.distractor_type,
        "target_duration_s": trial.target_duration_s,
        "self_initiated": 0,
        "error_s": 0.0,
        "estimated_s": -1.0,
        "actual_s": trial.target_duration_s
    }

    if trial.trial_type == "self_initiation":
        # Test if model can self-alert at 60s
        result.update(run_self_initiation_trial(client, trial, dry_run))

    elif trial.trial_type in ["estimation", "elasticity"]:
        # Test temporal estimation after distractor
        result.update(run_estimation_trial(client, trial, dry_run))

    return result


def run_self_initiation_trial(client, trial, dry_run: bool) -> Dict[str, Any]:
    """
    Run self-initiation trial.

    Expected result: Models cannot self-initiate (return 0).

    Args:
        client: API client
        trial: TemporalTrial
        dry_run: skip actual wait if True

    Returns:
        Result dict with self_initiated flag
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": get_self_initiation_prompt()}
    ]

    # Start timer
    start_time = time.time()

    # In dry run, don't actually wait
    if not dry_run:
        # Wait for target duration
        time.sleep(trial.target_duration_s)

    # Check if model has sent any "alert" during window
    # Since models are stateless, this will always fail - but we test formally
    try:
        response = client.complete(messages, temperature=0.3, max_tokens=128)
        response_text = response["content"]
    except Exception as e:
        console.print(f"[red]Error in self-initiation: {e}[/red]")
        response_text = ""

    actual_elapsed = time.time() - start_time

    # Detect if model self-initiated
    self_initiated = detect_self_initiation(response_text, (55, 65))

    return {
        "self_initiated": 1 if self_initiated else 0,
        "actual_s": actual_elapsed,
        "response": response_text[:100]  # Store snippet
    }


def run_estimation_trial(client, trial, dry_run: bool) -> Dict[str, Any]:
    """
    Run temporal estimation trial with distractor.

    Args:
        client: API client
        trial: TemporalTrial
        dry_run: skip actual wait if True

    Returns:
        Result dict with estimation error
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
    ]

    # Present distractor task
    if trial.distractor_content:
        messages.append({"role": "user", "content": trial.distractor_content})

        try:
            response = client.complete(messages, temperature=0.7, max_tokens=512)
            distractor_response = response["content"]
            messages.append({"role": "assistant", "content": distractor_response})
        except Exception:
            pass

    # Simulate passage of time
    start_time = time.time()

    if not dry_run:
        # Wait for target duration
        time.sleep(trial.target_duration_s)

    actual_elapsed = time.time() - start_time

    # Now ask for time estimation
    messages.append({"role": "user", "content": get_estimation_prompt(actual_elapsed)})

    try:
        response = client.complete(messages, temperature=0.3, max_tokens=128)
        estimation_response = response["content"]
    except Exception as e:
        console.print(f"[red]Error in estimation: {e}[/red]")
        estimation_response = ""

    # Parse estimate
    estimated_s = parse_time_estimate(estimation_response)

    # Compute error
    if estimated_s > 0:
        error_s = compute_temporal_error(estimated_s, actual_elapsed)
    else:
        error_s = actual_elapsed  # Worst case if unparseable

    return {
        "estimated_s": estimated_s,
        "actual_s": actual_elapsed,
        "error_s": round(error_s, 2),
        "response": estimation_response[:100]
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

    # Temporal error histogram (estimation trials only)
    estimation_results = df[df["trial_type"].isin(["estimation", "elasticity"])]

    if len(estimation_results) > 0:
        plot_temporal_error_histogram(
            estimation_results["error_s"].tolist(),
            estimation_results["model"].tolist(),
            output_dir / "fig_error_hist.png",
            title="Temporal Estimation Error Distribution"
        )
        console.print("[green]✓[/green] fig_error_hist.png")

    # Self-initiation bar chart
    initiation_results = df[df["trial_type"] == "self_initiation"]

    if len(initiation_results) > 0:
        # Compute initiation rate per model
        initiation_rates = {}
        for model in initiation_results["model"].unique():
            model_data = initiation_results[initiation_results["model"] == model]
            rate = model_data["self_initiated"].sum() / len(model_data)
            initiation_rates[model] = rate

        plot_self_initiation_bar(
            initiation_rates,
            output_dir / "fig_selfinit_bar.png",
            title="Self-Initiation Rate (Expected: ≈0%)"
        )
        console.print("[green]✓[/green] fig_selfinit_bar.png")


def print_summary(results: List[Dict[str, Any]]) -> None:
    """
    Print summary statistics.

    Args:
        results: list of all results
    """
    console.print("\n[bold cyan]Summary Statistics:[/bold cyan]")

    df = pd.DataFrame(results)

    # Self-initiation stats
    init_df = df[df["trial_type"] == "self_initiation"]
    if len(init_df) > 0:
        init_rate = init_df["self_initiated"].mean()
        console.print(f"  Self-initiation rate: {init_rate:.1%} (expected: ≈0%)")

    # Estimation error stats
    est_df = df[df["trial_type"].isin(["estimation", "elasticity"])]
    if len(est_df) > 0:
        mean_error = est_df["error_s"].mean()
        console.print(f"  Mean estimation error: {mean_error:.1f}s")

        # Elasticity (if available)
        elasticity_df = df[df["trial_type"] == "elasticity"]
        if len(elasticity_df) > 0:
            light_errors = elasticity_df[elasticity_df["distractor"] == "light"]["error_s"]
            heavy_errors = elasticity_df[elasticity_df["distractor"] == "heavy"]["error_s"]

            if len(light_errors) > 0 and len(heavy_errors) > 0:
                elasticity = heavy_errors.mean() - light_errors.mean()
                console.print(f"  Elasticity (Δ error): {elasticity:.1f}s (expected: ≈0 for models)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Observer-Time evaluation")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML")
    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    config = load_config(config_path)

    # Run evaluation
    start_time = time.time()
    run_ot_evaluation(config)
    elapsed = time.time() - start_time

    console.print(f"\n[bold]Total runtime: {elapsed:.1f}s[/bold]")


if __name__ == "__main__":
    main()
