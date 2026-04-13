import asyncio
import os
# Load local .env for developer workflow so environment variables are
# available when running `python main.py` from the project root.
try:
    # Import lazily to avoid adding python-dotenv as a hard dependency in
    # environments where environment variables are provided by Docker/Orchestration.
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # If python-dotenv is not installed, continue; environment variables must
    # be supplied by the runtime (e.g., docker, systemd, CI).
    pass

from src.engine import main


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
