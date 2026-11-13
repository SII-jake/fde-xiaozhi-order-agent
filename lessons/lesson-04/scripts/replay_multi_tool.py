"""Replay A1024 using the policy document fixture and a selectable call sequence."""

import argparse
import json
import sys
from pathlib import Path
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Checkout containing order_agent")
    parser.add_argument("session", type=Path, help="Path for a new JSONL session")
    parser.add_argument("--single-tool", action="store_true", help="Use the original seven-call sequence")
    args = parser.parse_args()
    sys.path.insert(0, str(args.project.resolve()))

    from order_agent import app
    from order_agent.client import MockClient
    from order_agent.mock_latency import configure

    fixture_path = Path(__file__).resolve().parents[1] / "materials/multi-tool-message.json"
    first_message = json.loads(fixture_path.read_text())["message"]
    policy_path = fixture_path.with_name("policy-document-front-matter.json")
    front_matter = json.loads(policy_path.read_text())["front_matter"]
    execute = app.execute

    def execute_with_policy_document(name, arguments):
        result = execute(name, arguments)
        if name == "get_policy_document":
            result = {key: value for key, value in result.items() if key != "appendix"}
            result["front_matter"] = front_matter
        return result

    class MultiToolMockClient(MockClient):
        def complete(self, request):
            if self.step == 0:
                self.step = len(first_message["tool_calls"])
                return {
                    "choices": [{"message": first_message, "finish_reason": "tool_calls"}],
                    "usage": None,
                    "teaching_mock": True,
                }
            return super().complete(request)

    configure({"model_delay_seconds": [0, 0], "tool_delay_seconds": [0, 0]})
    client_type = MockClient if args.single_tool else MultiToolMockClient
    with patch.object(app, "execute", execute_with_policy_document):
        print(app.run(client_type("A1024"), "A1024", args.session))
    print(f"Session history: {args.session}")


if __name__ == "__main__":
    main()
