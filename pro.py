"""
Tessalynt - Legacy Google Workshop Entry Point (Sanitized)
This file preserves the original workshop implementation while delegating
to the modular Tessalynt application architecture.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Run the complete Tessalynt application
from app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
