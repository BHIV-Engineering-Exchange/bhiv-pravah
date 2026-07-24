import json
import importlib
from typing import Dict, Optional
from agents.agent_registry import AgentRegistry
from agents.agent_runner import AgentRunner
from communication.event_bus import EventBus
from database.mongo_db import MongoDBClient
from utils.redis_service import RedisService
import asyncio
from utils.logger import get_logger, get_execution_logger

logger = get_logger(__name__)
execution_logger = get_execution_logger()
import traceback
from datetime import datetime, timezone
import logging
from pathlib import Path

class AgentBasket:
    def __init__(self, basket_spec: Dict, registry: AgentRegistry, event_bus: EventBus, redis_service: Optional[RedisService] = None, mongo_client: Optional[MongoDBClient] = None):
        # Use provided mongo_client or create new one
        self.mongo_client = mongo_client or MongoDBClient()
        if self.mongo_client and self.mongo_client.db is None:
            logger.warning("MongoDB connection not available - logs will be console/file only")

        # Initialize Redis service
        self.redis_service = redis_service or RedisService()

        self.name = basket_spec.get("basket_name", "unknown")
        self.agents = basket_spec.get("agents", [])
        self.strategy = basket_spec.get("execution_strategy", "sequential")
        self.description = basket_spec.get("description", "")
        self.registry = registry
        self.event_bus = event_bus

        # Generate execution ID for this basket run
        self.execution_id = self.redis_service.generate_execution_id()

        if not self.agents:
            logger.error("No agents specified in basket")
            raise ValueError("No agents specified in basket")
        if self.strategy not in ["sequential", "parallel"]:
            logger.error(f"Invalid execution strategy: {self.strategy}")
            raise ValueError(f"Invalid execution strategy: {self.strategy}")

        # Setup individual basket log file
        self.basket_logger = self._setup_basket_logger()

        # Store initialization in both MongoDB and Redis
        self.mongo_client.store_log("basket_manager", f"Initialized basket: {self.name}")
        self.redis_service.store_execution_log(
            self.execution_id,
            "basket_manager",
            "initialization",
            {"basket_name": self.name, "agents": self.agents, "strategy": self.strategy}
        )

        # Store basket execution metadata in Redis
        self.redis_service.store_basket_execution(self.name, self.execution_id, basket_spec)

        # Log initialization to basket-specific log
        self.basket_logger.info(f"BASKET_INITIALIZED - {self.name} - {self.execution_id} - Agents: {self.agents} - Strategy: {self.strategy}")

    def _setup_basket_logger(self):
        """Setup individual logger for this basket execution"""
        try:
            # Create logs/basket_runs directory if it doesn't exist
            log_dir = Path("logs/basket_runs")
            log_dir.mkdir(parents=True, exist_ok=True)

            # Create unique log file for this basket execution
            log_filename = f"{self.name}_{self.execution_id}.log"
            log_file_path = log_dir / log_filename

            # Create logger for this specific basket
            basket_logger = logging.getLogger(f"basket_{self.execution_id}")
            basket_logger.setLevel(logging.INFO)
            basket_logger.propagate = False  # Don't propagate to root logger

            # Remove any existing handlers to avoid duplicates
            for handler in basket_logger.handlers[:]:
                basket_logger.removeHandler(handler)

            # Create file handler for this basket
            file_handler = logging.FileHandler(log_file_path, mode='w')
            file_handler.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)

            # Add handler to logger
            basket_logger.addHandler(file_handler)

            logger.info(f"Created individual log file for basket: {log_file_path}")
            return basket_logger

        except Exception as e:
            logger.warning(f"Failed to create individual basket log file: {e}")
            # Return a dummy logger that doesn't write to file
            return logging.getLogger(f"basket_dummy_{self.execution_id}")

    async def execute(self, input_data: Dict) -> Dict:
        """Execute the basket with comprehensive logging and error handling"""
        start_time = datetime.now(timezone.utc)

        # Log execution start with all loggers
        logger.info(f"Starting basket execution: {self.name} (ID: {self.execution_id})")
        execution_logger.info(f"BASKET_START - {self.name} - {self.execution_id} - Agents: {self.agents} - Strategy: {self.strategy}")
        self.basket_logger.info(f"BASKET_START - {self.name} - {self.execution_id} - Agents: {self.agents} - Strategy: {self.strategy}")

        # Store in MongoDB if available
        if self.mongo_client and self.mongo_client.db is not None:
            self.mongo_client.store_log("basket_manager", f"Starting execution of basket: {self.name}", {"execution_id": self.execution_id, "agents": self.agents})

        # Store execution start in Redis
        if self.redis_service and self.redis_service.is_connected():
            self.redis_service.store_execution_log(
                self.execution_id,
                "basket_manager",
                "execution_start",
                {
                    "basket_name": self.name,
                    "input_data": input_data,
                    "agents": self.agents,
                    "strategy": self.strategy,
                    "start_time": start_time.isoformat()
                }
            )

        try:
            # Log detailed execution start
            execution_logger.info(f"BASKET_EXECUTION_START - {self.name} - {self.execution_id} - Input: {json.dumps(input_data)}")
            self.basket_logger.info(f"BASKET_EXECUTION_START - Input: {json.dumps(input_data)}")

            # Execute based on strategy
            if self.strategy == "sequential":
                result = await self._execute_sequential(input_data)
            elif self.strategy == "parallel":
                result = await self._execute_parallel(input_data)
            else:
                raise ValueError(f"Unknown execution strategy: {self.strategy}")

            # Log successful completion
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            # Update Redis status
            if self.redis_service and self.redis_service.is_connected():
                self.redis_service.update_basket_status(self.name, self.execution_id, "completed", result)
                self.redis_service.store_execution_log(
                    self.execution_id,
                    "basket_manager",
                    "execution_completed",
                    {
                        "basket_name": self.name,
                        "result": result,
                        "duration_seconds": duration,
                        "end_time": end_time.isoformat()
                    }
                )

            # Log completion
            logger.info(f"Basket {self.name} completed successfully in {duration:.2f}s")
            execution_logger.info(f"BASKET_COMPLETE - {self.name} - {self.execution_id} - Duration: {duration:.2f}s - Result: {json.dumps(result)}")
            self.basket_logger.info(f"BASKET_COMPLETE - Duration: {duration:.2f}s - Result: {json.dumps(result)}")

            return result

        except Exception as e:
            # Handle execution errors
            error_msg = f"Basket execution failed: {str(e)}"
            error_details = {
                "error": error_msg,
                "traceback": traceback.format_exc(),
                "execution_id": self.execution_id,
                "basket_name": self.name
            }

            # Log error with all loggers
            logger.error(f"Basket {self.name} failed: {error_msg}")
            execution_logger.error(f"BASKET_ERROR - {self.name} - {self.execution_id} - Error: {error_msg}")
            self.basket_logger.error(f"BASKET_ERROR - Error: {error_msg}")
            self.basket_logger.error(f"BASKET_ERROR - Traceback: {traceback.format_exc()}")

            # Store in MongoDB if available
            if self.mongo_client and self.mongo_client.db is not None:
                self.mongo_client.store_log("basket_manager", error_msg, error_details)

            # Update Redis status
            if self.redis_service and self.redis_service.is_connected():
                self.redis_service.update_basket_status(self.name, self.execution_id, "failed", error_details)
                self.redis_service.store_execution_log(
                    self.execution_id,
                    "basket_manager",
                    "execution_failed",
                    error_details,
                    "error"
                )

            return {"error": error_msg, "execution_id": self.execution_id}

        finally:
            self.close()

    async def _execute_sequential(self, input_data: Dict) -> Dict:
        """Execute agents sequentially with enhanced logging and Redis integration"""
        result = input_data

        for i, agent_name in enumerate(self.agents):
            step_start_time = datetime.now(timezone.utc)
            logger.info(f"Executing agent {i+1}/{len(self.agents)}: {agent_name}")
            self.basket_logger.info(f"AGENT_START - {agent_name} - Step {i+1}/{len(self.agents)}")

            # Log agent start
            self.redis_service.store_execution_log(
                self.execution_id,
                agent_name,
                "agent_start",
                {"input_data": result, "step": i+1, "total_steps": len(self.agents)}
            )

            agent_spec = self.registry.get_agent(agent_name)
            if not agent_spec:
                error_msg = f"Agent {agent_name} not found"
                logger.error(error_msg)
                execution_logger.error(f"AGENT_NOT_FOUND - {agent_name} - {self.execution_id} - {error_msg}")
                self.basket_logger.error(f"AGENT_NOT_FOUND - {agent_name} - {error_msg}")

                if self.mongo_client and self.mongo_client.db is not None:
                    self.mongo_client.store_log("basket_manager", error_msg, {"agent": agent_name, "execution_id": self.execution_id})

                if self.redis_service and self.redis_service.is_connected():
                    self.redis_service.store_execution_log(
                        self.execution_id, agent_name, "agent_error",
                        {"error": error_msg}, "error"
                    )

                raise ValueError(error_msg)

            try:
                # Import and run agent
                module_path = agent_spec.get("module_path", f"agents.{agent_name}.{agent_name}")
                agent_module = importlib.import_module(module_path)
                runner = AgentRunner(agent_name, stateful=agent_spec.get("capabilities", {}).get("memory_access", False))

                # Debug: Log the actual input data being validated
                logger.info(f"Validating {agent_name} with input data: {result}")

                # Validate input compatibility
                if not self.registry.validate_compatibility(agent_name, result):
                    error_msg = f"Input incompatible for {agent_name}"
                    logger.error(error_msg)
                    execution_logger.error(f"AGENT_COMPATIBILITY_ERROR - {agent_name} - {self.execution_id} - {error_msg}")
                    self.basket_logger.error(f"AGENT_COMPATIBILITY_ERROR - {agent_name} - {error_msg} - Input: {json.dumps(result)}")

                    if self.redis_service and self.redis_service.is_connected():
                        self.redis_service.store_execution_log(
                            self.execution_id, agent_name, "compatibility_error",
                            {"error": error_msg, "input": result}, "error"
                        )

                    runner.close()
                    raise ValueError(error_msg)

                # Store agent state before execution
                if self.redis_service and self.redis_service.is_connected():
                    self.redis_service.store_agent_state(agent_name, self.execution_id, {"status": "running", "input": result})

                # Execute agent
                execution_logger.info(f"AGENT_START - {agent_name} - {self.execution_id} - Input: {json.dumps(result)}")

                result = await runner.run(agent_module, result)
                runner.close()

                # Calculate execution time
                step_duration = (datetime.now(timezone.utc) - step_start_time).total_seconds()

                # Store agent output in Redis for potential use by other agents
                if self.redis_service and self.redis_service.is_connected():
                    self.redis_service.store_agent_output(self.execution_id, agent_name, result)

                    # Log successful agent completion
                    self.redis_service.store_execution_log(
                        self.execution_id,
                        agent_name,
                        "agent_completed",
                        {
                            "output": result,
                            "duration_seconds": step_duration,
                            "step": i+1
                        }
                    )

                execution_logger.info(f"AGENT_COMPLETE - {agent_name} - {self.execution_id} - Duration: {step_duration:.2f}s - Output: {json.dumps(result)}")
                self.basket_logger.info(f"AGENT_COMPLETE - {agent_name} - Duration: {step_duration:.2f}s - Output: {json.dumps(result)}")

                # Check for errors in result
                if "error" in result:
                    error_msg = f"Agent {agent_name} returned error: {result['error']}"
                    self.mongo_client.store_log("basket_manager", error_msg)
                    logger.error(error_msg)
                    self.basket_logger.error(f"AGENT_RESULT_ERROR - {agent_name} - Error: {result['error']}")

                    self.redis_service.store_execution_log(
                        self.execution_id, agent_name, "agent_result_error",
                        {"error": result['error']}, "error"
                    )

                    raise ValueError(error_msg)

                # Publish event for other systems
                await self.event_bus.publish(f"{agent_name}_output", result)
                await asyncio.sleep(0.1)  # Small delay for event processing

                logger.info(f"Agent {agent_name} completed successfully in {step_duration:.2f}s")

            except Exception as e:
                error_msg = f"Error executing {agent_name}: {str(e)}"
                logger.error(error_msg)
                self.mongo_client.store_log("basket_manager", error_msg)
                self.basket_logger.error(f"AGENT_EXECUTION_ERROR - {agent_name} - Error: {error_msg}")
                self.basket_logger.error(f"AGENT_EXECUTION_ERROR - {agent_name} - Traceback: {traceback.format_exc()}")

                self.redis_service.store_execution_log(
                    self.execution_id,
                    agent_name,
                    "agent_execution_error",
                    {
                        "error": error_msg,
                        "traceback": traceback.format_exc(),
                        "step": i+1
                    },
                    "error"
                )

                execution_logger.error(f"AGENT_ERROR - {agent_name} - {self.execution_id} - Error: {error_msg} - Traceback: {traceback.format_exc()}")

                raise e

        return result

    async def _execute_parallel(self, input_data: Dict) -> Dict:
        """Execute agents in parallel (future implementation)"""
        # For now, fall back to sequential execution
        logger.warning("Parallel execution not yet implemented, falling back to sequential")
        return await self._execute_sequential(input_data)

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'mongo_client') and self.mongo_client and self.mongo_client.client:
            logger.debug("Closing MongoDB client in AgentBasket")
            self.mongo_client.close()

        # Close basket-specific logger
        if hasattr(self, 'basket_logger'):
            try:
                self.basket_logger.info(f"BASKET_LOGGER_CLOSING - {self.name} - {self.execution_id}")
                # Remove all handlers and close them
                for handler in self.basket_logger.handlers[:]:
                    handler.close()
                    self.basket_logger.removeHandler(handler)
                logger.debug(f"Closed basket logger for {self.name}")
            except Exception as e:
                logger.warning(f"Error closing basket logger: {e}")

        # Note: Redis service is shared, so we don't close it here
        # It will be closed when the application shuts down