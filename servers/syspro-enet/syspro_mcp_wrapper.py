#!/usr/bin/env python3
"""
SYSPRO MCP Server Wrapper with Enhanced Error Handling
This wrapper adds detailed logging and error catching
"""

import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Set up file logging immediately
log_file = Path(__file__).parent / "syspro_mcp_startup.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger("syspro-wrapper")

# Log startup
logger.info("=" * 70)
logger.info(f"SYSPRO MCP Server Starting at {datetime.now()}")
logger.info(f"Python: {sys.version}")
logger.info(f"Working Directory: {Path.cwd()}")
logger.info(f"Script Location: {Path(__file__).parent}")
logger.info("=" * 70)

# Global exception handler
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Catch any uncaught exceptions and log them"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow Ctrl+C to work normally
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical("Uncaught exception!", exc_info=(exc_type, exc_value, exc_traceback))
    logger.critical("Server crashed - see log above for details")

sys.excepthook = global_exception_handler

try:
    logger.info("Step 1: Checking dependencies...")
    
    # Check httpx
    try:
        import httpx
        logger.info(f"  [OK] httpx {httpx.__version__}")
    except ImportError as e:
        logger.error(f"  [ERROR] httpx not found: {e}")
        logger.error("  Run: pip install httpx")
        sys.exit(1)
    
    # Check mcp
    try:
        import mcp
        logger.info(f"  [OK] mcp imported successfully")
    except ImportError as e:
        logger.error(f"  [ERROR] mcp not found: {e}")
        logger.error("  Run: pip install mcp")
        sys.exit(1)
    
    logger.info("Step 2: Importing main server module...")

    # Add server directory to path (use the directory where this script is located)
    server_dir = Path(__file__).parent.resolve()
    sys.path.insert(0, str(server_dir))
    logger.info(f"  Added to path: {server_dir}")
    
    import syspro_mcp_server
    logger.info("  [OK] syspro_mcp_server imported")
    
    logger.info("Step 3: Setting up environment...")
    import os
    
    # Set environment variables if not already set
    env_vars = {
        "SYSPRO_BASE_URL": "http://zalpduppdupl:31002/SYSPROWCFService/Rest",
        "SYSPRO_OPERATOR": "ADMIN",
        "SYSPRO_PASSWORD": "admin",
        "SYSPRO_COMPANY_ID": "EDU1",
        "SYSPRO_COMPANY_PASSWORD": ""
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            logger.info(f"  Set {key}")
        else:
            logger.info(f"  {key} already set")
    
    logger.info("Step 4: Starting server...")
    
    # Run the server
    import asyncio
    
    async def run_server():
        try:
            server = syspro_mcp_server.SysproMCPServer()
            logger.info("  Server instance created")
            await server.run()
        except Exception as e:
            logger.error(f"  Error in server.run(): {e}")
            raise
    
    asyncio.run(run_server())
    
except KeyboardInterrupt:
    logger.info("\nServer stopped by user (Ctrl+C)")
    sys.exit(0)
    
except Exception as e:
    logger.critical(f"\nFATAL ERROR: {e}")
    logger.critical("Full traceback:")
    logger.critical(traceback.format_exc())
    
    print("\n" + "=" * 70, file=sys.stderr)
    print("SYSPRO MCP SERVER FAILED TO START", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(f"\nError: {e}", file=sys.stderr)
    print(f"\nCheck the log file for details: {log_file}", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    sys.exit(1)
