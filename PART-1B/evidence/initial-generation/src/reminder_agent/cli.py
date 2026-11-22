import argparse
import sys
from collections.abc import Sequence

from reminder_agent.config import ConfigurationError, load_settings
from reminder_agent.engine import PipelineError, ReminderAgent
from reminder_agent.gemini_client import GeminiAdapter, ProviderError
from reminder_agent.output import serialize_response


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reminder-agent")
    parser.add_argument("--text", required=True, help="Natural-language reminder request.")
    parser.add_argument("--reference-time", help="Offset-aware resolution reference time.")
    parser.add_argument("--timezone", help="IANA time-zone name.")
    parser.add_argument(
        "--reminder-task",
        action="append",
        default=[],
        help="Candidate reminder task; may be supplied more than once.",
    )
    args = parser.parse_args(argv)
    request = {
        "text": args.text,
        "context": {
            "reference_time": args.reference_time,
            "timezone": args.timezone,
            "reminder_tasks": args.reminder_task,
        },
    }

    try:
        settings = load_settings()
        result = ReminderAgent(GeminiAdapter(settings)).process(request)
    except (ConfigurationError, PipelineError, ProviderError) as error:
        _write_error(error.code)
        return 2

    print(serialize_response(result.response))
    return 0


def _write_error(code: str) -> None:
    safe_code = code if code.isascii() and code.replace("_", "").isalnum() else "OPERATIONAL_ERROR"
    sys.stderr.write(f"ERROR: {safe_code}\n")


if __name__ == "__main__":
    raise SystemExit(main())
