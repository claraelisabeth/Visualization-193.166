"""
Launch the Edge Path Bundling Dashboard

Run this script from the project root to start the interactive dashboard.
"""

if __name__ == "__main__":
    from src.dashboard.app import app
    app.run(debug=True, host='0.0.0.0', port=8050)