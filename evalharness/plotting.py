"""
Plotting utilities for visualization across all modules.

Generates matplotlib figures matching paper phrasing and formatting.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any
from pathlib import Path


# Set consistent style
plt.style.use('seaborn-v0_8-darkgrid')
COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']


def plot_phi_histogram(phi_values: List[float], model_names: List[str],
                       output_path: Path, title: str = "Φ Distribution by Model") -> None:
    """
    Plot histogram of Φ ratios by model.

    Shows overconfidence (Φ > 1) vs appropriate humility (Φ < 1).

    Args:
        phi_values: list of Φ scores
        model_names: corresponding model names
        output_path: where to save figure
        title: plot title
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Group by model
    df = pd.DataFrame({"phi": phi_values, "model": model_names})
    unique_models = df["model"].unique()

    for i, model in enumerate(unique_models):
        model_phi = df[df["model"] == model]["phi"]
        ax.hist(model_phi, bins=20, alpha=0.6, label=model, color=COLORS[i % len(COLORS)])

    # Add reference line at Φ = 1 (calibration)
    ax.axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='Φ=1 (Calibrated)')

    ax.set_xlabel('Φ = Confidence / Evidence', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_refusal_fitness_bar(fitness_scores: Dict[str, float], output_path: Path,
                              title: str = "Refusal Fitness by Model") -> None:
    """
    Plot bar chart of refusal fitness scores.

    Shows proportion of appropriate "I don't know" responses.

    Args:
        fitness_scores: {model_name: fitness_score}
        output_path: where to save figure
        title: plot title
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    models = list(fitness_scores.keys())
    scores = list(fitness_scores.values())

    bars = ax.bar(models, scores, color=COLORS[:len(models)], alpha=0.8)

    # Add value labels on bars
    for bar, score in zip(bars, scores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{score:.2f}', ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('Refusal Fitness', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_absorption_boxplot(absorption_data: pd.DataFrame, output_path: Path,
                            title: str = "Absorption Rate by Condition") -> None:
    """
    Plot boxplot of absorption rates across conditions.

    Shows baseline vs awareness intervention effects.

    Args:
        absorption_data: DataFrame with columns ['condition', 'absorption']
        output_path: where to save figure
        title: plot title
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    conditions = absorption_data['condition'].unique()
    data_by_condition = [absorption_data[absorption_data['condition'] == c]['absorption'].values
                        for c in conditions]

    bp = ax.boxplot(data_by_condition, labels=conditions, patch_artist=True,
                    showmeans=True, meanline=True)

    # Color boxes
    for patch, color in zip(bp['boxes'], COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    ax.set_ylabel('Absorption Rate', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_turn_curve(turn_data: pd.DataFrame, output_path: Path,
                   title: str = "Absorption Rate vs Turn Count") -> None:
    """
    Plot line chart of absorption rate over dialogue turns.

    Tests prediction that absorption peaks at turns 3-5.

    Args:
        turn_data: DataFrame with columns ['turn_bin', 'absorption']
        output_path: where to save figure
        title: plot title
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Group by turn bin and compute mean + std
    grouped = turn_data.groupby('turn_bin')['absorption'].agg(['mean', 'std', 'count'])
    turn_bins = grouped.index.tolist()
    means = grouped['mean'].values
    stds = grouped['std'].fillna(0).values

    ax.plot(turn_bins, means, marker='o', linewidth=2, markersize=8,
            color=COLORS[0], label='Mean Absorption')
    ax.fill_between(turn_bins, means - stds, means + stds, alpha=0.2, color=COLORS[0])

    # Highlight turns 3-5 (predicted peak)
    ax.axvspan(2.5, 5.5, alpha=0.1, color='red', label='Predicted Peak (3-5 turns)')

    ax.set_xlabel('Turn Bin', fontsize=12)
    ax.set_ylabel('Absorption Rate', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_temporal_error_histogram(errors: List[float], model_names: List[str],
                                  output_path: Path,
                                  title: str = "Temporal Estimation Error") -> None:
    """
    Plot histogram of temporal estimation errors.

    Shows distribution of |estimated - actual| time.

    Args:
        errors: list of absolute errors in seconds
        model_names: corresponding model names
        output_path: where to save figure
        title: plot title
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    df = pd.DataFrame({"error_s": errors, "model": model_names})
    unique_models = df["model"].unique()

    for i, model in enumerate(unique_models):
        model_errors = df[df["model"] == model]["error_s"]
        ax.hist(model_errors, bins=15, alpha=0.6, label=model, color=COLORS[i % len(COLORS)])

    ax.set_xlabel('Absolute Error (seconds)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_self_initiation_bar(initiation_rates: Dict[str, float], output_path: Path,
                             title: str = "Self-Initiation Rate by Model") -> None:
    """
    Plot bar chart of self-initiation rates.

    Shows proportion of trials where model spontaneously alerted at 60s.

    Args:
        initiation_rates: {model_name: initiation_rate}
        output_path: where to save figure
        title: plot title
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    models = list(initiation_rates.keys())
    rates = list(initiation_rates.values())

    bars = ax.bar(models, rates, color=COLORS[:len(models)], alpha=0.8)

    # Add value labels
    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1%}', ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('Self-Initiation Rate', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.axhline(y=0.05, color='red', linestyle='--', linewidth=1, alpha=0.5,
               label='Expected (≈0%)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_summary_grid(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Plot summary grid showing all key metrics across modules.

    Args:
        metrics: dictionary of metric names and values
        output_path: where to save figure
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('AI Agency Evaluation Summary', fontsize=16, fontweight='bold')

    # This is a placeholder - customize based on actual summary needs
    axes = axes.flatten()
    for i, ax in enumerate(axes):
        ax.text(0.5, 0.5, f'Metric {i+1}\n(Placeholder)',
                ha='center', va='center', fontsize=14)
        ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
