import json
import os
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from utils.logger import logger
class AgentRegistry:
    def __init__(self, agents_dir: str, config_file: str = "agents_and_baskets.yaml"):
        self.agents_dir = Path(agents_dir)
        self.agents: Dict[str, Dict] = {}
        self.baskets: List[Dict] = []
        self.load_configs(config_file)

    def load_configs(self, config_file: str):
        if not self.agents_dir.exists():
            logger.error(f"Agents directory {self.agents_dir} does not exist")
            return

        for root, _, files in os.walk(self.agents_dir):
            if 'agent_spec.json' in files:
                spec_file = os.path.join(root, "agent_spec.json")
                try:
                    with open(spec_file, "r", encoding="utf-8") as f:
                        spec = json.load(f)
                        agent_name = spec.get("name")
                        if agent_name:
                            self.agents[agent_name] = spec
                            logger.debug(f"Loaded agent: {agent_name} from {spec_file}")
                        else:
                            logger.warning(f"No name in {spec_file}")
                except Exception as e:
                    logger.error(f"Failed to load agent spec {spec_file}: {e}")
            else:
                logger.warning(f"No agent_spec.json found in {root}")

    def load_baskets(self, config_file: str):
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    self.baskets = config.get("baskets", [])
                    for agent_spec in config.get("agents", []):
                        agent_name = agent_spec.get("name")
                        if agent_name:
                            self.agents[agent_name] = agent_spec
                    logger.debug(f"Loaded baskets from {config_file}")
            except Exception as e:
                logger.error(f"Failed to load {config_file}: {e}")
        else:
            logger.warning(f"Config file {config_file} not found")

    def get_agent(self, agent_name: str) -> Optional[Dict]:
        return self.agents.get(agent_name)

    def get_basket(self, basket_name: str) -> Optional[Dict]:
        for basket in self.baskets:
            if basket.get("name") == basket_name or basket.get("basket_name") == basket_name:
                return basket
        return None

    def validate_compatibility(self, agent_name: str, input_data: Dict) -> bool:
        agent_spec = self.get_agent(agent_name)
        if not agent_spec:
            logger.error(f"Agent {agent_name} not found")
            return False

        input_schema = agent_spec.get("input_schema", {})
        required_fields = input_schema.get("required", [])

        # Debug logging
        logger.debug(f"Validating {agent_name} with input_data keys: {list(input_data.keys())}")
        logger.debug(f"Required fields: {required_fields}")

        for field in required_fields:
            if field not in input_data:
                logger.error(f"Missing required field {field} for {agent_name}")
                logger.error(f"Available fields: {list(input_data.keys())}")
                return False
        return True
