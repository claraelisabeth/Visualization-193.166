"""
Launch the Edge Path Bundling Dashboard

Run this script from the project root to start the interactive dashboard.
"""

if __name__ == "__main__":
    from src.dashboard.app import app
    
    print("🚀 Starting Edge Path Bundling Dashboard...")
    print("📊 Open your browser and go to: http://localhost:8050")
    print("⚡ Dashboard features:")
    print("   • Interactive parameter controls")
    print("   • Multiple dataset support")
    print("   • Real-time bundling visualization")
    print("\n🛑 Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=8050)