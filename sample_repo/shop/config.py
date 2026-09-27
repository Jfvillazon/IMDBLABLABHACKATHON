"""Demo configuration with an intentionally embedded, fake credential.

The hardcoded credential fallback is a deliberate security finding. No service
uses this value to authenticate or make network requests.
"""

import os

DEMO_API_KEY = "FAKE_DEMO_KEY_NOT_REAL"


def load_config():
    """Read configuration on demand; the embedded fallback needs remediation."""
    return {"api_key": os.environ.get("REPOMEDIC_DEMO_KEY", DEMO_API_KEY)}
