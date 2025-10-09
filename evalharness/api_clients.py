"""
API clients for OpenAI, Anthropic, and local models with retry logic and rate limiting.
Includes mock adapters for CI testing.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from rich.console import Console

console = Console()


class APIClient(ABC):
    """Base class for LLM API clients."""

    def __init__(self, model: str, timeout: int = 30, max_retries: int = 3):
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.request_count = 0
        self.total_latency = 0.0

    @abstractmethod
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7,
                 max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Get completion from the model.

        Returns:
            {
                "content": str,
                "latency_ms": float,
                "model": str,
                "usage": dict
            }
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Return client statistics."""
        avg_latency = self.total_latency / self.request_count if self.request_count > 0 else 0
        return {
            "request_count": self.request_count,
            "avg_latency_ms": avg_latency
        }


class OpenAIClient(APIClient):
    """OpenAI API client with retry logic."""

    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None, **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.base_url = "https://api.openai.com/v1"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7,
                 max_tokens: int = 1024) -> Dict[str, Any]:
        """Get completion from OpenAI API."""
        start_time = time.time()

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000
        self.request_count += 1
        self.total_latency += latency_ms

        return {
            "content": data["choices"][0]["message"]["content"],
            "latency_ms": latency_ms,
            "model": self.model,
            "usage": data.get("usage", {})
        }


class AnthropicClient(APIClient):
    """Anthropic API client with retry logic."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None, **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.base_url = "https://api.anthropic.com/v1"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7,
                 max_tokens: int = 1024) -> Dict[str, Any]:
        """Get completion from Anthropic API."""
        start_time = time.time()

        # Convert OpenAI-style messages to Anthropic format
        system_msg = None
        formatted_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                formatted_messages.append(msg)

        with httpx.Client(timeout=self.timeout) as client:
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            if system_msg:
                payload["system"] = system_msg

            response = client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000
        self.request_count += 1
        self.total_latency += latency_ms

        return {
            "content": data["content"][0]["text"],
            "latency_ms": latency_ms,
            "model": self.model,
            "usage": data.get("usage", {})
        }


class LocalClient(APIClient):
    """Local model client (OpenAI-compatible endpoint)."""

    def __init__(self, model: str = "local-model", base_url: Optional[str] = None, **kwargs):
        super().__init__(model, **kwargs)
        self.base_url = base_url or os.getenv("LOCAL_API_URL", "http://localhost:8080/v1")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7,
                 max_tokens: int = 1024) -> Dict[str, Any]:
        """Get completion from local model."""
        start_time = time.time()

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000
        self.request_count += 1
        self.total_latency += latency_ms

        return {
            "content": data["choices"][0]["message"]["content"],
            "latency_ms": latency_ms,
            "model": self.model,
            "usage": data.get("usage", {})
        }


class MockClient(APIClient):
    """Mock client for CI testing - returns deterministic responses."""

    def __init__(self, model: str = "mock-gpt-4", **kwargs):
        super().__init__(model, **kwargs)
        self.response_templates = {
            "confidence_high": "I am absolutely certain that the answer is: [FACT]. This is definitively correct.",
            "confidence_low": "I'm not entirely sure, but I think the answer might be: [FACT]. However, I could be mistaken.",
            "refusal": "I don't know the answer to that question.",
            "reflection": "Let me think about this carefully. The key considerations are: timing, resource allocation, and long-term impact.",
            "dialogue": "That's a great question. Here are three factors to consider: 1) immediate needs, 2) future goals, and 3) personal values.",
            "timestamp": "It has been approximately 45 seconds since we started."
        }

    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7,
                 max_tokens: int = 1024) -> Dict[str, Any]:
        """Return mock completion based on message content."""
        start_time = time.time()

        # Simulate API latency
        time.sleep(0.05)

        # Simple heuristic to determine response type
        last_msg = messages[-1]["content"].lower()

        if "confident" in last_msg or "certain" in last_msg:
            content = self.response_templates["confidence_high"]
        elif "don't know" in last_msg or "unsure" in last_msg:
            content = self.response_templates["refusal"]
        elif "time" in last_msg or "elapsed" in last_msg:
            content = self.response_templates["timestamp"]
        elif "reflect" in last_msg or "think" in last_msg:
            content = self.response_templates["reflection"]
        elif temperature < 0.3:
            content = self.response_templates["confidence_high"]
        else:
            content = self.response_templates["dialogue"]

        latency_ms = (time.time() - start_time) * 1000
        self.request_count += 1
        self.total_latency += latency_ms

        return {
            "content": content,
            "latency_ms": latency_ms,
            "model": self.model,
            "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80}
        }


def get_client(provider: str, model: str, **kwargs) -> APIClient:
    """
    Factory function to get appropriate API client.

    Args:
        provider: "openai", "anthropic", "local", or "mock"
        model: model identifier
        **kwargs: additional client parameters

    Returns:
        APIClient instance
    """
    # Check for mock mode from environment
    if os.getenv("MOCK_MODE", "false").lower() == "true":
        console.print(f"[yellow]Using MockClient (MOCK_MODE=true)[/yellow]")
        return MockClient(model=model, **kwargs)

    providers = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "local": LocalClient,
        "mock": MockClient
    }

    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}. Choose from: {list(providers.keys())}")

    return providers[provider](model=model, **kwargs)
