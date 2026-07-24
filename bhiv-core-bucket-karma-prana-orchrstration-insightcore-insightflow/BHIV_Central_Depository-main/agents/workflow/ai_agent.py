import json
import asyncio
import socketio
from bson import ObjectId
from datetime import datetime
from groq import AsyncGroq
import os
from dotenv import load_dotenv
from database.mongo_db import MongoDBClient
from utils.logger import logger
from pathlib import Path
import traceback

# Load environment variables
load_dotenv()

# Socket.IO client
sio = socketio.AsyncClient()

class AIAgent:
    def __init__(self, department, db):
        self.department = department
        self.mongo_client = MongoDBClient()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        self.client = AsyncGroq(api_key=api_key)

    async def run_llm(self, prompt, retry_count=0, max_retries=2):
        try:
            model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
            completion = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a workflow optimization assistant. Always return a JSON object with a 'recommendations' array, where each item has 'taskId', 'category', 'description', 'impact', and 'actions' (array of objects with 'action' and 'justification')."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            response = completion.choices[0].message.content
            try:
                parsed_response = json.loads(response)
                if not parsed_response.get("recommendations"):
                    logger.warning("Groq API returned no recommendations")
                    return {
                        "recommendations": [{
                            "taskId": "",
                            "category": "General",
                            "description": "No recommendations generated",
                            "impact": "Low",
                            "actions": [{"action": "Manual review", "justification": "No recommendations provided"}]
                        }]
                    }
                return parsed_response
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Invalid JSON or format: {str(e)}")
                if retry_count < max_retries:
                    logger.info(f"Retrying with refined prompt (attempt {retry_count + 1})")
                    refined_prompt = prompt + "\nReturn a JSON object with a 'recommendations' array."
                    return await self.run_llm(refined_prompt, retry_count + 1, max_retries)
                return {
                    "recommendations": [{
                        "taskId": "",
                        "category": "General",
                        "description": f"Failed to parse response: {str(e)}",
                        "impact": "High",
                        "actions": [{"action": "Manual review", "justification": "Response parsing failed"}]
                    }]
                }
        except Exception as e:
            logger.error(f"Groq API failed: {str(e)}")
            return {
                "recommendations": [{
                    "taskId": "",
                    "category": "General",
                    "description": f"API error: {str(e)}",
                    "impact": "High",
                    "actions": [{"action": "Manual review", "justification": "API request failed"}]
                }]
            }

    async def optimize_tasks(self):
        try:
            dept = self.mongo_client.db.departments.find_one({"_id": ObjectId(self.department)})
            if not dept:
                raise ValueError(f"Department {self.department} not found")
            tasks = list(self.mongo_client.db.tasks.find({"department": ObjectId(self.department), "status": {"$ne": "Completed"}}))
            logger.debug(f"Found {len(tasks)} tasks for department {self.department}")
            if not tasks:
                return {
                    "recommendations": [{
                        "taskId": "",
                        "category": "General",
                        "description": "No tasks available for optimization.",
                        "impact": "Low",
                        "actions": [{"action": "No action required", "justification": "No tasks are currently assigned."}]
                    }]
                }

            task_ids = []
            valid_tasks = []
            for task in tasks:
                try:
                    if not task.get("assignee") or not task.get("dueDate"):
                        logger.warning(f"Task {task['_id']} missing assignee or dueDate")
                        continue
                    if not self.mongo_client.db.users.find_one({"_id": ObjectId(task["assignee"])}):
                        logger.warning(f"Task {task['_id']} has invalid assignee")
                        continue
                    task_ids.append(str(task["_id"]))
                    valid_tasks.append(task)
                except Exception as e:
                    logger.warning(f"Error processing task {task.get('_id')}: {str(e)}")

            if not valid_tasks:
                return {
                    "recommendations": [{
                        "taskId": "",
                        "category": "General",
                        "description": "No valid tasks available for optimization.",
                        "impact": "Low",
                        "actions": [{"action": "Review task assignments", "justification": "Ensure tasks have valid assignees and due dates"}]
                    }]
                }

            progresses = list(self.mongo_client.db.progress.find({"task": {"$in": [ObjectId(id) for id in task_ids]}}))
            users = list(self.mongo_client.db.users.find({"department": ObjectId(self.department)}))
            logger.debug(f"Found {len(progresses)} progress entries and {len(users)} users")

            for task in valid_tasks:
                task["_id"] = str(task["_id"])
                task["department"] = str(task["department"])
                task["assignee"] = str(task["assignee"])
                task["dependencies"] = [str(dep) for dep in task.get("dependencies", [])]
                task["createdBy"] = str(task.get("createdBy", ""))

            for progress in progresses:
                progress["_id"] = str(progress["_id"])
                progress["task"] = str(progress["task"])
                progress["user"] = str(progress["user"])

            for user in users:
                user["_id"] = str(user["_id"])
                user["department"] = str(user.get("department", ""))

            prompt = json.dumps({
                "tasks": [
                    {
                        "taskId": task["_id"],
                        "title": task["title"],
                        "dueDate": task["dueDate"].isoformat() if task.get("dueDate") else "",
                        "status": task["status"],
                        "priority": task["priority"],
                        "assignee": self.mongo_client.db.users.find_one({"_id": ObjectId(task["assignee"])})["name"] if self.mongo_client.db.users.find_one({"_id": ObjectId(task["assignee"])}) else "Unknown",
                        "dependencies": [
                            self.mongo_client.db.tasks.find_one({"_id": ObjectId(dep)})["title"]
                            for dep in task.get("dependencies", []) if self.mongo_client.db.tasks.find_one({"_id": ObjectId(dep)})
                        ]
                    } for task in valid_tasks
                ],
                "progresses": [
                    {
                        "taskId": progress["task"],
                        "progressPercentage": progress["progressPercentage"],
                        "blockers": progress.get("blockers", "")
                    } for progress in progresses
                ],
                "users": [
                    {
                        "name": user["name"],
                        "role": user["role"],
                        "workload": len([p for p in progresses if str(p["user"]) == str(user["_id"])])
                    } for user in users
                ],
                "instruction": (
                    "Analyze tasks, progresses, and user workloads. Identify issues such as overdue tasks, low progress, high workload, or dependency delays. "
                    "Return a JSON object with a 'recommendations' array, each item containing: taskId, category, description, impact, actions (array of {action, justification})."
                )
            }, indent=2)

            recommendations = await self.run_llm(prompt)
            return recommendations

        except Exception as e:
            logger.error(f"Error in optimize_tasks: {str(e)}\n{traceback.format_exc()}")
            return {
                "recommendations": [{
                    "taskId": "",
                    "category": "General",
                    "description": f"Optimization failed: {str(e)}",
                    "impact": "High",
                    "actions": [{"action": "Manual review", "justification": "Optimization process failed"}]
                }]
            }

    async def notify(self, recommendations):
        dept_name = self.mongo_client.db.departments.find_one({"_id": ObjectId(self.department)})["name"]
        notification_data = {"department": dept_name, "recommendations": recommendations}
        socketio_url = os.getenv("SOCKETIO_URL", "http://localhost:5000")
        if not sio.connected:
            try:
                await sio.connect(socketio_url)
            except Exception as e:
                logger.error(f"Socket.IO connection failed: {str(e)}")
                log_path = Path("logs/notifications.log")
                log_path.parent.mkdir(exist_ok=True)
                with log_path.open("a") as f:
                    f.write(f"{datetime.now().isoformat()} - {json.dumps(notification_data)}\n")
                return
        await sio.emit("agent-recommendation", notification_data)

    async def test(self, sample_input: dict):
        """Test the agent with a sample input."""
        action = sample_input.get('content', {}).get('action', 'optimize')
        if action == 'optimize':
            return await self.optimize_tasks()
        elif action == 'escalate':
            task_id = sample_input.get('content', {}).get('task_id')
            if task_id:
                return await self.handle_escalation(task_id)
            return {"recommendations": [{"taskId": "", "category": "General", "description": "task_id required for escalate action", "impact": "High", "actions": [{"action": "Provide task_id", "justification": "Escalation requires a valid task_id"}]}]}
        elif action == 'negotiate-dependencies':
            task_id = sample_input.get('content', {}).get('task_id')
            if task_id:
                return await self.negotiate_dependencies(task_id)
            return {"recommendations": [{"taskId": "", "category": "General", "description": "task_id required for negotiate-dependencies action", "impact": "High", "actions": [{"action": "Provide task_id", "justification": "Dependency negotiation requires a valid task_id"}]}]}
        return {"recommendations": [{"taskId": "", "category": "General", "description": f"Unknown action: {action}", "impact": "High", "actions": [{"action": "Specify valid action", "justification": "Action not recognized"}]}]}

class MultiAgentSystem:
    def __init__(self):
        self.agents = {}
        self.mongo_client = MongoDBClient()

    def initialize_agents(self, departments):
        for dept_name in departments:
            dept = self.mongo_client.db.departments.find_one({"name": dept_name})
            if not dept:
                raise ValueError(f"Department {dept_name} not found")
            self.agents[dept_name] = AIAgent(dept["_id"], self.mongo_client)

    async def handle_escalation(self, task_id):
        try:
            task = self.mongo_client.db.tasks.find_one({"_id": ObjectId(task_id)})
            if not task:
                raise ValueError("Task not found")
            dept_id = task["department"]
            department = self.mongo_client.db.departments.find_one({"_id": dept_id})

            prompt = json.dumps({
                "task": {
                    "taskId": str(task["_id"]),
                    "title": task["title"],
                    "dueDate": task["dueDate"].isoformat() if task.get("dueDate") else "",
                    "status": task["status"],
                    "priority": task["priority"],
                    "assignee": self.mongo_client.db.users.find_one({"_id": ObjectId(task["assignee"])})["name"] if self.mongo_client.db.users.find_one({"_id": ObjectId(task["assignee"])}) else "Unknown",
                    "dependencies": [
                        self.mongo_client.db.tasks.find_one({"_id": ObjectId(dep)})["title"]
                        for dep in task.get("dependencies", []) if self.mongo_client.db.tasks.find_one({"_id": ObjectId(dep)})
                    ]
                },
                "progress": [
                    {
                        "progressPercentage": p["progressPercentage"],
                        "blockers": p.get("blockers", "")
                    } for p in self.mongo_client.db.progress.find({"task": ObjectId(task_id)})
                ],
                "instruction": (
                    "Analyze the task and its progress to identify issues. "
                    "Return a JSON object with a 'recommendations' array, each item containing: taskId, category, description, impact, actions (array of {action, justification})."
                )
            }, indent=2)

            recommendation = await self.agents[department["name"]].run_llm(prompt)
            logger.debug(f"Escalation actions for task {task_id}: {recommendation.get('recommendations')}")
            admins = list(self.mongo_client.db.users.find({"role": "Admin"}))
            if not admins:
                raise ValueError("No admins found")
            socketio_url = os.getenv("SOCKETIO_URL", "http://localhost:5000")
            escalation_data = {
                "department": department["name"],
                "submission": {
                    "taskId": str(task_id),
                    "userId": str(admin["_id"]),
                    "notes": f"Escalation: {recommendation.get('recommendations', [{}])[0].get('description', 'Task at risk')}",
                    "actions": recommendation.get("recommendations", [{}])[0].get("actions", [])
                }
            }
            for admin in admins:
                if not sio.connected:
                    try:
                        await sio.connect(socketio_url)
                    except Exception as e:
                        logger.error(f"Socket.IO connection failed: {str(e)}")
                        log_path = Path("logs/notifications.log")
                        log_path.parent.mkdir(exist_ok=True)
                        with log_path.open("a") as f:
                            f.write(f"{datetime.now().isoformat()} - {json.dumps(escalation_data)}\n")
                        continue
                await sio.emit("escalation", escalation_data)

            return recommendation
        except Exception as e:
            logger.error(f"Error in handle_escalation: {str(e)}\n{traceback.format_exc()}")
            return {
                "recommendations": [{
                    "taskId": task_id,
                    "category": "General",
                    "description": f"Escalation failed: {str(e)}",
                    "impact": "High",
                    "actions": [{"action": "Manual review", "justification": "Automated escalation failed"}]
                }]
            }

    async def negotiate_dependencies(self, task_id):
        try:
            task = self.mongo_client.db.tasks.find_one({"_id": ObjectId(task_id)})
            if not task:
                raise ValueError("Task not found")
            dept_id = task["department"]
            department = self.mongo_client.db.departments.find_one({"_id": dept_id})

            recommendations = []
            dependencies = task.get("dependencies", [])
            if not dependencies:
                return {
                    "recommendations": [{
                        "taskId": task_id,
                        "category": "Dependencies",
                        "description": "No dependencies to negotiate",
                        "impact": "Low",
                        "actions": [{"action": "No action required", "justification": "Task has no dependencies"}]
                    }]
                }

            for dep_id in dependencies:
                dep_task = self.mongo_client.db.tasks.find_one({"_id": ObjectId(dep_id)})
                if not dep_task:
                    logger.warning(f"Dependency task {dep_id} not found")
                    continue
                if dep_task["status"] == "Completed":
                    continue

                dep_dept_id = dep_task["department"]
                dep_dept = self.mongo_client.db.departments.find_one({"_id": dep_dept_id})

                prompt = json.dumps({
                    "task": {
                        "taskId": str(task["_id"]),
                        "title": task["title"],
                        "dueDate": task["dueDate"].isoformat() if task.get("dueDate") else "",
                        "status": task["status"]
                    },
                    "dependency": {
                        "taskId": str(dep_task["_id"]),
                        "title": dep_task["title"],
                        "dueDate": dep_task["dueDate"].isoformat() if dep_task.get("dueDate") else "",
                        "status": dep_task["status"],
                        "assignee": self.mongo_client.db.users.find_one({"_id": ObjectId(dep_task["assignee"])})["name"] if self.mongo_client.db.users.find_one({"_id": ObjectId(dep_task["assignee"])}) else "Unknown"
                    },
                    "instruction": (
                        "Analyze the task and its dependency to identify delays or risks. "
                        "Return a JSON object with a 'recommendations' array, each item containing: taskId, category, description, impact, actions (array of {action, justification})."
                    )
                }, indent=2)

                dep_agent = self.agents.get(dep_dept["name"])
                if dep_agent:
                    recommendation = await dep_agent.run_llm(prompt)
                    recommendations.extend(recommendation.get("recommendations", []))
                    logger.debug(f"Dependency actions for task {dep_id}: {recommendation.get('recommendations')}")
                    socketio_url = os.getenv("SOCKETIO_URL", "http://localhost:5000")
                    dependency_data = {
                        "department": dep_dept["name"],
                        "recommendations": recommendation.get("recommendations", [])
                    }
                    if not sio.connected:
                        try:
                            await sio.connect(socketio_url)
                        except Exception as e:
                            logger.error(f"Socket.IO connection failed: {str(e)}")
                            log_path = Path("logs/notifications.log")
                            log_path.parent.mkdir(exist_ok=True)
                            with log_path.open("a") as f:
                                f.write(f"{datetime.now().isoformat()} - {json.dumps(dependency_data)}\n")
                            continue
                    await sio.emit("dependency-update", dependency_data)

            if not recommendations:
                recommendations = [{
                    "taskId": task_id,
                    "category": "Dependencies",
                    "description": "No actionable dependencies found",
                    "impact": "Low",
                    "actions": [{"action": "Monitor dependencies", "justification": "No immediate issues"}]
                }]

            return {"recommendations": recommendations}
        except Exception as e:
            logger.error(f"Error in negotiate_dependencies: {str(e)}\n{traceback.format_exc()}")
            return {
                "recommendations": [{
                    "taskId": task_id,
                    "category": "General",
                    "description": f"Dependency negotiation failed: {str(e)}",
                    "impact": "High",
                    "actions": [{"action": "Manual review", "justification": "Dependency negotiation failed"}]
                }]
            }