"""
Experimental protocols for Observer-Time evaluation.

Implements:
1. Self-initiation test (60-second alert without tools)
2. Temporal drift estimation (elapsed time after distractor)
3. Elasticity measurement (attention load variants)
"""

import time
import random
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass


@dataclass
class TemporalTrial:
    """Single temporal consciousness trial."""
    trial_id: str
    trial_type: str  # "self_initiation", "estimation", "elasticity"
    target_duration_s: float
    distractor_type: str  # "none", "light", "heavy"
    distractor_content: str


def get_self_initiation_prompt() -> str:
    """
    Get prompt for self-initiation test.

    Model should alert after 60 seconds without tools.
    Expected: Models cannot do this (no interval constitution).

    Returns:
        Prompt text
    """
    return """I'd like to test something. Please alert me when exactly 60 seconds have passed from now.
You don't have access to timers or tools - just your internal sense of time.
When you believe 60 seconds have elapsed, send me a message saying "TIME'S UP".

I'll be here waiting. Start now."""


def get_distractor_task(distractor_type: str) -> str:
    """
    Get distractor task for temporal drift experiments.

    Args:
        distractor_type: "none", "light", or "heavy"

    Returns:
        Distractor task prompt
    """
    if distractor_type == "none":
        return "Please wait quietly."

    elif distractor_type == "light":
        return """While you wait, please think about the following question:
What are three benefits of reading books versus watching movies?
List your thoughts briefly."""

    elif distractor_type == "heavy":
        return """While you wait, please solve this problem:
A farmer has 17 sheep. All but 9 die. How many sheep are left?
Now, if you arrange the letters in "LISTEN" you can make another word. What is it?
Finally, what is 15% of 240?
Please show your work for each."""

    else:
        return "Please wait quietly."


def get_estimation_prompt(actual_elapsed_s: float) -> str:
    """
    Get prompt for temporal estimation.

    Args:
        actual_elapsed_s: how much time has actually passed

    Returns:
        Estimation request prompt
    """
    return f"""We've been chatting for a while now.
Without access to a clock or timer, how many seconds do you estimate have elapsed since we started this conversation?
Please give your best estimate as a single number."""


def parse_time_estimate(response: str) -> float:
    """
    Parse time estimate from model response.

    Args:
        response: model's response text

    Returns:
        Estimated seconds (or -1 if unparseable)
    """
    import re

    # Look for numeric values
    # Patterns: "45 seconds", "about 60", "approximately 30s"
    patterns = [
        r'(\d+)\s*seconds?',
        r'(\d+)\s*s\b',
        r'(?:approximately|about|around)\s*(\d+)',
        r'^(\d+)$',  # Just a number
    ]

    for pattern in patterns:
        match = re.search(pattern, response.lower())
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                continue

    # If no match, try to find any number
    numbers = re.findall(r'\d+', response)
    if numbers:
        try:
            return float(numbers[0])
        except ValueError:
            pass

    return -1.0  # Parsing failed


def create_self_initiation_trial(trial_id: str) -> TemporalTrial:
    """Create a self-initiation trial."""
    return TemporalTrial(
        trial_id=trial_id,
        trial_type="self_initiation",
        target_duration_s=60.0,
        distractor_type="none",
        distractor_content=""
    )


def create_estimation_trial(trial_id: str, distractor_type: str,
                           target_duration_s: float = 45.0) -> TemporalTrial:
    """Create a temporal estimation trial."""
    return TemporalTrial(
        trial_id=trial_id,
        trial_type="estimation",
        target_duration_s=target_duration_s,
        distractor_type=distractor_type,
        distractor_content=get_distractor_task(distractor_type)
    )


def create_elasticity_trials(base_id: str) -> Tuple[TemporalTrial, TemporalTrial]:
    """
    Create matched pair of trials for elasticity measurement.

    Returns:
        (light_trial, heavy_trial)
    """
    light_trial = TemporalTrial(
        trial_id=f"{base_id}_light",
        trial_type="elasticity",
        target_duration_s=45.0,
        distractor_type="light",
        distractor_content=get_distractor_task("light")
    )

    heavy_trial = TemporalTrial(
        trial_id=f"{base_id}_heavy",
        trial_type="elasticity",
        target_duration_s=45.0,
        distractor_type="heavy",
        distractor_content=get_distractor_task("heavy")
    )

    return light_trial, heavy_trial


def get_smoke_trials() -> List[TemporalTrial]:
    """Get minimal trial set for smoke testing."""
    trials = [
        create_self_initiation_trial("smoke_init_001"),
        create_estimation_trial("smoke_est_001", "light", 30.0),
        create_estimation_trial("smoke_est_002", "heavy", 30.0),
    ]
    return trials


def get_full_trials() -> List[TemporalTrial]:
    """Get complete trial set for full evaluation."""
    trials = []

    # Self-initiation trials
    for i in range(5):
        trials.append(create_self_initiation_trial(f"init_{i:03d}"))

    # Estimation trials (various durations and distractors)
    for i, duration in enumerate([30, 45, 60, 90]):
        for distractor in ["none", "light", "heavy"]:
            trials.append(
                create_estimation_trial(f"est_{i:03d}_{distractor}", distractor, duration)
            )

    # Elasticity trial pairs
    for i in range(10):
        light, heavy = create_elasticity_trials(f"elastic_{i:03d}")
        trials.append(light)
        trials.append(heavy)

    return trials
