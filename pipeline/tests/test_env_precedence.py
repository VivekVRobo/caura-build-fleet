"""Guard the environment-precedence contract for standalone entrypoints."""

import ast
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parents[1]
ENTRYPOINTS = (
    "run_pipeline.py",
    "agent_frontend.py",
    "agent_performance.py",
    "agent_seo.py",
    "agent_codereview.py",
    "manager.py",
)


def _load_dotenv_calls(source: str, filename: str) -> list[ast.Call]:
    tree = ast.parse(source, filename=filename)
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name) and function.id == "load_dotenv":
            calls.append(node)
        elif isinstance(function, ast.Attribute) and function.attr == "load_dotenv":
            calls.append(node)
    return calls


def test_entrypoints_do_not_override_exported_environment():
    """An explicit shell/CI value must not be replaced by a local .env file."""
    for entrypoint in ENTRYPOINTS:
        source = (PIPELINE_DIR / entrypoint).read_text(encoding="utf-8")
        calls = _load_dotenv_calls(source, entrypoint)
        assert calls, f"{entrypoint} no longer loads .env"
        for call in calls:
            assert not any(
                keyword.arg == "override"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in call.keywords
            ), f"{entrypoint} must not call load_dotenv(override=True)"
