#!/usr/bin/env python3
"""
Startup script for the Entrepreneurship AI Chatbot Server
=========================================================

This script provides an easy way to start the server with different configurations.

Usage:
    python start_server.py                    # Development mode
    python start_server.py --production       # Production mode
    python start_server.py --port 8001        # Custom port
    python start_server.py --help             # Show help
"""

import argparse
import os
import sys
import uvicorn
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Start the Entrepreneurship AI Chatbot Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_server.py                    # Development mode with auto-reload
  python start_server.py --production       # Production mode with 4 workers
  python start_server.py --port 8001        # Custom port
  python start_server.py --host 127.0.0.1   # Custom host
        """
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode with multiple workers"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of worker processes (production mode only, default: 4)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["critical", "error", "warning", "info", "debug"],
        default="info",
        help="Log level (default: info)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development only)"
    )
    
    args = parser.parse_args()
    
    # Check if server.py exists
    server_path = Path(__file__).parent / "server.py"
    if not server_path.exists():
        print("❌ Error: server.py not found in the current directory")
        print(f"   Expected path: {server_path}")
        sys.exit(1)
    
    # Check if required dependencies are installed
    try:
        import fastapi
        import uvicorn
        import google.generativeai
        print("✅ All required dependencies are installed")
    except ImportError as e:
        print(f"❌ Error: Missing dependency - {e}")
        print("   Please install dependencies with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Prepare uvicorn configuration
    config = {
        "app": "server:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
    }
    
    if args.production:
        print(f"🚀 Starting server in PRODUCTION mode")
        print(f"   Host: {args.host}")
        print(f"   Port: {args.port}")
        print(f"   Workers: {args.workers}")
        print(f"   Log Level: {args.log_level}")
        
        config.update({
            "workers": args.workers,
            "reload": False,
        })
    else:
        print(f"🔧 Starting server in DEVELOPMENT mode")
        print(f"   Host: {args.host}")
        print(f"   Port: {args.port}")
        print(f"   Auto-reload: {args.reload or True}")
        print(f"   Log Level: {args.log_level}")
        
        config.update({
            "reload": args.reload or True,
            "reload_dirs": [str(Path(__file__).parent)],
        })
    
    print(f"📊 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔗 Health Check: http://{args.host}:{args.port}/api/health")
    print("=" * 60)
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()