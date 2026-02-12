from __future__ import annotations

import json

from engine.config import load_config
from engine.logging import configure_logging, get_logger

logger = get_logger("Eval")

async def main_eval(cli_args):
    """
    Placeholder for the headless evaluation runner.
    Will be implemented in Phase 3.
    """
    try:
        config_path = cli_args.config if hasattr(cli_args, "config") else None
        config = load_config(config_path) if config_path else load_config()
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error_code": "config_error",
            "message": str(e)
        }))
        return

    # Headless logging to stderr
    configure_logging(config, verbose_count=cli_args.verbose, quiet=cli_args.quiet)

    logger.info(f"Starting evaluation mode with provider: {cli_args.provider}")

    # Simulate work for now
    print(json.dumps({
        "status": "ok",
        "provider": cli_args.provider,
        "audio_file": cli_args.audio,
        "message": "Eval mode placeholder initialized."
    }))
