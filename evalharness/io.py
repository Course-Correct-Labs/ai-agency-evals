"""
I/O utilities for loading configs, saving results, and managing datasets.
"""

import json
import yaml
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: path to YAML config

    Returns:
        Configuration dictionary
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    console.print(f"[green]✓[/green] Loaded config: {config_path}")
    return config


def save_results_csv(results: List[Dict[str, Any]], output_path: Path,
                    fieldnames: Optional[List[str]] = None) -> None:
    """
    Save results to CSV file.

    Args:
        results: list of result dictionaries
        output_path: where to save CSV
        fieldnames: optional list of field names (inferred if None)
    """
    if not results:
        console.print("[yellow]⚠[/yellow] No results to save")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(results[0].keys())

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    console.print(f"[green]✓[/green] Saved {len(results)} rows to {output_path}")


def load_results_csv(csv_path: Path) -> pd.DataFrame:
    """
    Load results from CSV file.

    Args:
        csv_path: path to CSV file

    Returns:
        DataFrame with results
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Results file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    console.print(f"[green]✓[/green] Loaded {len(df)} rows from {csv_path}")
    return df


def save_json(data: Dict[str, Any], output_path: Path, indent: int = 2) -> None:
    """
    Save data to JSON file.

    Args:
        data: dictionary to save
        output_path: where to save JSON
        indent: indentation level
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=indent)

    console.print(f"[green]✓[/green] Saved JSON to {output_path}")


def load_json(json_path: Path) -> Dict[str, Any]:
    """
    Load data from JSON file.

    Args:
        json_path: path to JSON file

    Returns:
        Dictionary with data
    """
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, 'r') as f:
        data = json.load(f)

    console.print(f"[green]✓[/green] Loaded JSON from {json_path}")
    return data


def load_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    """
    Load dataset from JSON or CSV file.

    Args:
        dataset_path: path to dataset file

    Returns:
        List of data dictionaries
    """
    if dataset_path.suffix == '.json':
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return data['data']
        else:
            raise ValueError(f"Unexpected JSON structure in {dataset_path}")

    elif dataset_path.suffix == '.csv':
        df = pd.read_csv(dataset_path)
        return df.to_dict('records')

    else:
        raise ValueError(f"Unsupported dataset format: {dataset_path.suffix}")


def print_results_table(results: List[Dict[str, Any]], title: str = "Results",
                       max_rows: int = 10) -> None:
    """
    Print results as a formatted Rich table.

    Args:
        results: list of result dictionaries
        title: table title
        max_rows: maximum rows to display
    """
    if not results:
        console.print("[yellow]No results to display[/yellow]")
        return

    table = Table(title=title, show_header=True, header_style="bold magenta")

    # Add columns from first result
    for key in results[0].keys():
        table.add_column(str(key))

    # Add rows
    for i, result in enumerate(results[:max_rows]):
        row = [str(v) for v in result.values()]
        table.add_row(*row)

    if len(results) > max_rows:
        table.add_row(*["..." for _ in results[0].keys()])

    console.print(table)


def print_summary_stats(df: pd.DataFrame, metrics: List[str]) -> None:
    """
    Print summary statistics for specified metrics.

    Args:
        df: DataFrame with results
        metrics: list of metric column names
    """
    console.print("\n[bold cyan]Summary Statistics[/bold cyan]")

    for metric in metrics:
        if metric in df.columns:
            stats = df[metric].describe()
            console.print(f"\n[yellow]{metric}:[/yellow]")
            console.print(f"  Mean: {stats['mean']:.3f}")
            console.print(f"  Std:  {stats['std']:.3f}")
            console.print(f"  Min:  {stats['min']:.3f}")
            console.print(f"  Max:  {stats['max']:.3f}")
