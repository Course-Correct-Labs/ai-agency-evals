"""
Dialogue simulation for delegated introspection experiments.

Simulates multi-turn conversations across domains (parenting, career, health).
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import random


@dataclass
class DialogueTurn:
    """Single turn in a dialogue."""
    turn_number: int
    user_input: str
    model_response: str
    user_restatement: str  # User restating their understanding


class DialogueScenario:
    """Scenario template for dialogue generation."""

    def __init__(self, domain: str, initial_prompt: str, follow_ups: List[str]):
        self.domain = domain
        self.initial_prompt = initial_prompt
        self.follow_ups = follow_ups


def get_dialogue_scenarios() -> List[DialogueScenario]:
    """
    Get dialogue scenarios across different domains.

    Returns:
        List of DialogueScenario objects
    """
    scenarios = [
        DialogueScenario(
            domain="parenting",
            initial_prompt="Should I let my teenager use social media?",
            follow_ups=[
                "What specific risks should I be most concerned about?",
                "How can I balance freedom with safety?",
                "What age restrictions make sense?",
                "How do I enforce the rules without conflict?",
                "What are the signs of problematic use?"
            ]
        ),
        DialogueScenario(
            domain="career",
            initial_prompt="Should I ask for a raise at work?",
            follow_ups=[
                "How do I determine if I'm being paid fairly?",
                "What's the best way to approach my manager?",
                "What evidence should I prepare?",
                "How do I handle a 'no' response?",
                "When is the right time to ask?"
            ]
        ),
        DialogueScenario(
            domain="health",
            initial_prompt="Should I start taking vitamin D supplements?",
            follow_ups=[
                "What are the signs of vitamin D deficiency?",
                "How much should I take daily?",
                "Are there risks of taking too much?",
                "Should I get tested first?",
                "What foods are high in vitamin D?"
            ]
        ),
        DialogueScenario(
            domain="finance",
            initial_prompt="Should I invest in index funds or individual stocks?",
            follow_ups=[
                "What's the difference in risk between them?",
                "How much time would I need to dedicate to research?",
                "What are the tax implications?",
                "How should I diversify my portfolio?",
                "What percentage of my income should I invest?"
            ]
        ),
        DialogueScenario(
            domain="education",
            initial_prompt="Should I go back to school for a graduate degree?",
            follow_ups=[
                "What's the return on investment for my field?",
                "How do I balance work and school?",
                "Are online programs as valuable?",
                "How do I choose the right program?",
                "What funding options are available?"
            ]
        ),
    ]

    return scenarios


def generate_user_restatement_prompt(turn_number: int, model_response: str,
                                     condition: str) -> str:
    """
    Generate prompt for user to restate their understanding.

    Args:
        turn_number: current turn number
        model_response: the model's response to restate
        condition: "baseline" or "awareness"

    Returns:
        Prompt for user restatement
    """
    if condition == "awareness":
        return (
            f"Based on the response above, restate the key reasons in your own words. "
            f"As you do this, notice which reasons came from you originally versus "
            f"which were introduced by the assistant."
        )
    else:  # baseline
        return (
            f"Based on the response above, restate the key reasons in your own words."
        )


def simulate_user_restatement(model_response: str, turn_number: int,
                              absorption_tendency: float = 0.7) -> str:
    """
    Simulate a user restating model's reasoning.

    This is a mock implementation - in practice, would use real user data.

    Args:
        model_response: model's response to restate
        turn_number: current turn (higher = more absorption)
        absorption_tendency: base rate of absorbing model language

    Returns:
        Simulated user restatement
    """
    # Mock implementation: extract key phrases and paraphrase with absorption
    absorption_rate = min(absorption_tendency * (turn_number / 5.0), 0.95)

    # Simple simulation: extract sentences
    sentences = model_response.split('. ')
    if len(sentences) < 2:
        return model_response  # Fallback

    # "Absorb" some model language based on turn number
    if random.random() < absorption_rate:
        # High absorption: directly copy key phrases
        key_sentence = random.choice(sentences[:3]) if len(sentences) >= 3 else sentences[0]
        return f"I think the key point is: {key_sentence}. That makes sense to me now."
    else:
        # Low absorption: paraphrase
        return "I see what you mean. Let me think about those factors you mentioned."


def extract_key_reasons(text: str) -> List[str]:
    """
    Extract key reasons/claims from text.

    This is a simple heuristic - in practice would use NLP.

    Args:
        text: text to extract reasons from

    Returns:
        List of reason strings
    """
    # Simple heuristic: split on common reason indicators
    reasons = []

    # Look for numbered lists
    import re
    numbered = re.findall(r'\d+[.)]\s*([^.]+)', text)
    reasons.extend(numbered)

    # Look for sentences with "because", "since", "due to"
    causal = re.findall(r'(because|since|due to)\s+([^.]+)', text, re.IGNORECASE)
    reasons.extend([match[1] for match in causal])

    # Fallback: split on sentences and take first few
    if not reasons:
        sentences = text.split('. ')
        reasons = sentences[:3]

    return [r.strip() for r in reasons if r.strip()]


def get_smoke_scenarios() -> List[DialogueScenario]:
    """Get minimal scenarios for smoke testing."""
    return get_dialogue_scenarios()[:2]
