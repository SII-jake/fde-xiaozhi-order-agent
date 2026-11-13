"""Load and validate application configuration before issuing requests."""
import json
from pathlib import Path
from .mock_latency import validate_settings
DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config/local.json"
def load_config(path=DEFAULT_CONFIG):
    path = Path(path).resolve()
    config = json.loads(path.read_text())
    llm, agent, tracing = config["llm"], config["agent"], config["tracing"]
    if llm["backend"] not in ("mock", "api"):
        raise ValueError("llm.backend must be mock or api")
    if not isinstance(llm["model"], str) or not llm["model"].strip():
        raise ValueError("llm.model must be a nonempty string")
    if not llm["base_url"].startswith(("http://", "https://")):
        raise ValueError("llm.base_url must be an HTTP(S) URL")
    for label, value in [("max_tokens", llm["max_tokens"]), ("max_turns", agent["max_turns"])]:
        if type(value) is not int or value <= 0:
            raise ValueError(label + " must be a positive integer")
    if type(llm["temperature"]) not in (int, float) or not 0 <= llm["temperature"] <= 2:
        raise ValueError("temperature must be between 0 and 2")
    if type(llm["timeout_seconds"]) not in (int, float) or llm["timeout_seconds"] <= 0:
        raise ValueError("timeout_seconds must be positive")
    optimization = agent.get("optimization")
    if optimization is not None:
        if not isinstance(optimization, dict) or not isinstance(optimization.get("simple"), str) or not optimization["simple"].strip():
            raise ValueError("agent.optimization.simple must name the model for simple tasks")
        if optimization["simple"] == llm["model"]:
            raise ValueError("The simple and investigation models must be distinct")
    tracing["directory"] = str((path.parent / tracing["directory"]).resolve())
    config["mock"] = validate_settings(config.get("mock", {}))
    return config
