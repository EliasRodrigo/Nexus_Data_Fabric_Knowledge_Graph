"""Nexus — inicia o servidor Flask em modo desenvolvimento."""
import os
from app.app import app

if __name__ == "__main__":
    debug = os.environ.get("NEXUS_DEBUG", "0") == "1"
    app.run(debug=debug, host="127.0.0.1", port=5000)
