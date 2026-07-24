import argparse
import json
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from agents.agent_registry import AgentRegistry
from baskets.basket_manager import AgentBasket
from communication.event_bus import EventBus
from utils.logger import logger

async def execute_basket(spec_path: str):
    try:
        with open(spec_path, 'r') as f:
            basket_spec = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load basket spec: {e}")
        return {"error": f"Failed to load basket spec: {str(e)}"}

    registry = AgentRegistry("agents")
    event_bus = EventBus()
    try:
        basket = AgentBasket(basket_spec, registry, event_bus)
        result = await basket.execute({"input": "start"})
        logger.info(f"Basket execution result: {result}")
        return result
    except Exception as e:
        logger.error(f"Basket execution failed: {e}")
        return {"error": f"Basket execution failed: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Agent CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    execute_parser = subparsers.add_parser("execute-basket", help="Execute a basket of agents")
    execute_parser.add_argument("--spec", required=True, help="Path to basket specification JSON")

    args = parser.parse_args()

    if args.command == "execute-basket":
        result = asyncio.run(execute_basket(args.spec))
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()