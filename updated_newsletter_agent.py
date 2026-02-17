#!/usr/bin/env python3
"""Return of the Jed(AI) Newsletter Agent - Entry Point.

All logic lives in the newsletter/ package. This file is kept as
the entry point for backward compatibility with the GitHub Actions workflow.
"""

import json
import datetime

if __name__ == "__main__":
    try:
        from newsletter.agent import NewsletterAgent

        agent = NewsletterAgent()
        result = agent.run()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.datetime.now().isoformat(),
        }, indent=2))
