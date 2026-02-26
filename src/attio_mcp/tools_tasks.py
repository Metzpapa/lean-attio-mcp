"""Task tools: create, list, and update tasks."""

from . import client, formatting

TOOLS = [
    {
        "name": "create_task",
        "description": "Create a follow-up task with optional deadline and linked records.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Task description",
                },
                "deadline_at": {
                    "type": "string",
                    "description": "Deadline in ISO format (e.g. '2026-03-01T00:00:00.000Z'). Optional.",
                },
                "is_completed": {
                    "type": "boolean",
                    "description": "Whether the task starts completed (default false)",
                    "default": False,
                },
                "linked_records": {
                    "type": "array",
                    "description": "Records to link. Array of {\"target_object\": \"companies\", \"target_record_id\": \"...\"}",
                    "items": {
                        "type": "object",
                        "properties": {
                            "target_object": {"type": "string"},
                            "target_record_id": {"type": "string"},
                        },
                    },
                },
                "assignees": {
                    "type": "array",
                    "description": "Workspace member IDs to assign. Array of {\"referenced_actor_type\": \"workspace-member\", \"referenced_actor_id\": \"...\"}",
                    "items": {"type": "object"},
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "list_tasks",
        "description": "List tasks, optionally filtered by linked record or completion status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "linked_object": {
                    "type": "string",
                    "description": "Filter by linked object type (companies, people, deals). Optional.",
                },
                "linked_record_id": {
                    "type": "string",
                    "description": "Filter by linked record ID. Requires linked_object.",
                },
                "is_completed": {
                    "type": "boolean",
                    "description": "Filter by completion status. Omit to show all.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max tasks to return (default 50)",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "update_task",
        "description": "Update a task: mark complete, change deadline, update content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The task ID to update",
                },
                "content": {
                    "type": "string",
                    "description": "New task description",
                },
                "deadline_at": {
                    "type": "string",
                    "description": "New deadline in ISO format",
                },
                "is_completed": {
                    "type": "boolean",
                    "description": "Set to true to mark complete",
                },
            },
            "required": ["task_id"],
        },
    },
]


def handle(name: str, args: dict) -> str:
    if name == "create_task":
        return _create_task(args)
    elif name == "list_tasks":
        return _list_tasks(args)
    elif name == "update_task":
        return _update_task(args)
    raise ValueError(f"Unknown task tool: {name}")


def _create_task(args: dict) -> str:
    body = {
        "data": {
            "content": args["content"],
            "format": "plaintext",
            "is_completed": args.get("is_completed", False),
            "linked_records": args.get("linked_records", []),
            "assignees": args.get("assignees", []),
        },
    }
    if args.get("deadline_at"):
        # Attio wants date string like "2026-03-01", strip any time/timezone
        dl = args["deadline_at"]
        if "T" in dl:
            dl = dl.split("T")[0]
        body["data"]["deadline_at"] = dl

    data = client.post("/tasks", json=body)
    task = data.get("data", data)
    task_id = task.get("id", {})
    if isinstance(task_id, dict):
        task_id = task_id.get("task_id", str(task_id))

    return f"Created task: {args['content'][:80]} (ID: {task_id})"


def _list_tasks(args: dict) -> str:
    params = {"limit": args.get("limit", 50)}
    if args.get("linked_object") and args.get("linked_record_id"):
        params["linked_object"] = args["linked_object"]
        params["linked_record_id"] = args["linked_record_id"]
    if "is_completed" in args:
        params["is_completed"] = str(args["is_completed"]).lower()

    data = client.get("/tasks", params=params)
    tasks = data.get("data", [])

    if not tasks:
        return "No tasks found."

    lines = [f"Tasks ({len(tasks)}):"]
    for task in tasks:
        lines.append(formatting.format_task(task))
        lines.append("")
    return "\n".join(lines)


def _update_task(args: dict) -> str:
    task_id = args["task_id"]

    body = {"data": {}}
    if "content" in args:
        body["data"]["content"] = args["content"]
        body["data"]["format"] = "plaintext"
    if "deadline_at" in args:
        body["data"]["deadline_at"] = args["deadline_at"]
    if "is_completed" in args:
        body["data"]["is_completed"] = args["is_completed"]

    data = client.patch(f"/tasks/{task_id}", json=body)
    task = data.get("data", data)
    content = task.get("content_plaintext", task.get("content", ""))

    return f"Updated task: {content[:80]}"
