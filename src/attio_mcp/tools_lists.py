"""List/pipeline tools: list, create, query entries, add/update/delete entries."""

from . import client, formatting

TOOLS = [
    {
        "name": "list_lists",
        "description": "Get all lists/pipelines in the workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "create_list",
        "description": "Create a new list/pipeline. Specify the parent object (companies, people, deals) and a name. A slug is auto-generated from the name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the new list",
                },
                "api_slug": {
                    "type": "string",
                    "description": "API slug (snake_case). Auto-generated from name if not provided.",
                },
                "parent_object": {
                    "type": "string",
                    "description": "Parent object slug: companies, people, or deals",
                    "default": "companies",
                },
                "workspace_access": {
                    "type": "string",
                    "description": "Access level: full-access, read-and-write, or read-only",
                    "default": "full-access",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "query_list_entries",
        "description": "View entries in a list/pipeline with optional filtering and sorting. Returns formatted entries with all field values.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {
                    "type": "string",
                    "description": "List ID or slug (e.g. 'sales')",
                },
                "filter": {
                    "type": "object",
                    "description": "Optional Attio filter object. Example: {\"attribute\": \"stage\", \"condition\": \"equals\", \"value\": \"Meeting\"}",
                },
                "sorts": {
                    "type": "array",
                    "description": "Optional sort array. Example: [{\"attribute\": \"created_at\", \"direction\": \"desc\"}]",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max entries to return (default 50)",
                    "default": 50,
                },
            },
            "required": ["list_id"],
        },
    },
    {
        "name": "create_or_update_entry",
        "description": "Add a record to a list or update an existing entry. If the record is already in the list, it updates the entry values.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {
                    "type": "string",
                    "description": "List ID or slug",
                },
                "parent_record_id": {
                    "type": "string",
                    "description": "The record ID to add/update in the list",
                },
                "parent_object": {
                    "type": "string",
                    "description": "Object type slug: companies, people, or deals",
                    "default": "companies",
                },
                "entry_values": {
                    "type": "object",
                    "description": "Values for list-specific fields (stage, next_step, etc.)",
                    "default": {},
                },
            },
            "required": ["list_id", "parent_record_id", "parent_object"],
        },
    },
    {
        "name": "delete_entry",
        "description": "Remove a record from a list/pipeline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {
                    "type": "string",
                    "description": "List ID or slug",
                },
                "entry_id": {
                    "type": "string",
                    "description": "The entry ID to remove",
                },
            },
            "required": ["list_id", "entry_id"],
        },
    },
    {
        "name": "archive_list",
        "description": "Archive a list/pipeline. Hides it from the sidebar but preserves data. Use is_archived=false to unarchive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {
                    "type": "string",
                    "description": "List ID or slug to archive",
                },
                "is_archived": {
                    "type": "boolean",
                    "description": "True to archive, false to unarchive",
                    "default": True,
                },
            },
            "required": ["list_id"],
        },
    },
]


def handle(name: str, args: dict) -> str:
    if name == "list_lists":
        return _list_lists(args)
    elif name == "create_list":
        return _create_list(args)
    elif name == "query_list_entries":
        return _query_entries(args)
    elif name == "create_or_update_entry":
        return _create_or_update_entry(args)
    elif name == "delete_entry":
        return _delete_entry(args)
    elif name == "archive_list":
        return _archive_list(args)
    raise ValueError(f"Unknown list tool: {name}")


def _list_lists(args: dict) -> str:
    data = client.get("/lists")
    lists = data.get("data", [])

    if not lists:
        return "No lists found in workspace."

    lines = ["Lists in workspace:"]
    for lst in lists:
        list_id = lst.get("id", {})
        if isinstance(list_id, dict):
            list_id = list_id.get("list_id", str(list_id))
        name = lst.get("name", "(unnamed)")
        slug = lst.get("api_slug", "")
        parent = lst.get("parent_object", "")
        if isinstance(parent, list) and parent:
            parent = parent[0]
        parts = [f"  {name}"]
        if slug:
            parts.append(f"slug: {slug}")
        parts.append(f"ID: {list_id}")
        if parent:
            parts.append(f"parent: {parent}")
        lines.append(" — ".join(parts))
    return "\n".join(lines)


def _create_list(args: dict) -> str:
    name = args["name"]
    parent = args.get("parent_object", "companies")
    access = args.get("workspace_access", "full-access")

    # Generate slug from name if not provided
    import re
    slug = args.get("api_slug", "")
    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

    body = {
        "data": {
            "name": name,
            "api_slug": slug,
            "parent_object": parent,
            "workspace_access": access,
            "workspace_member_access": [],
        },
    }
    data = client.post("/lists", json=body)
    lst = data.get("data", data)
    list_id = lst.get("id", {})
    if isinstance(list_id, dict):
        list_id = list_id.get("list_id", str(list_id))
    actual_slug = lst.get("api_slug", slug)

    return f"Created list: {name} (ID: {list_id}, slug: {actual_slug})"


def _query_entries(args: dict) -> str:
    list_id = args["list_id"]
    limit = args.get("limit", 50)

    body = {"limit": limit}
    if args.get("filter"):
        body["filter"] = args["filter"]
    if args.get("sorts"):
        body["sorts"] = args["sorts"]

    data = client.post(f"/lists/{list_id}/entries/query", json=body)
    entries = data.get("data", [])

    if not entries:
        return f"No entries in list '{list_id}'."

    # Resolve parent record names in batch
    record_names = _resolve_parent_names(entries)

    lines = [f"List '{list_id}' ({len(entries)} entries):"]
    for i, entry in enumerate(entries, 1):
        lines.append(formatting.format_list_entry(entry, i, record_names))
    return "\n".join(lines)


def _resolve_parent_names(entries: list) -> dict[str, str]:
    """Batch-resolve parent record IDs to names."""
    names = {}
    # Group by parent_object
    by_object: dict[str, list[str]] = {}
    for entry in entries:
        obj = entry.get("parent_object", "")
        rid = entry.get("parent_record_id", "")
        if obj and rid and rid not in names:
            by_object.setdefault(obj, []).append(rid)

    for obj, record_ids in by_object.items():
        for rid in record_ids:
            try:
                data = client.get(f"/objects/{obj}/records/{rid}")
                record = data.get("data", data)
                values = record.get("values", {})
                for name_key in ["name", "full_name"]:
                    if name_key in values:
                        name = formatting.extract_values(values[name_key])
                        if name:
                            names[rid] = name
                            break
            except Exception:
                names[rid] = rid
    return names


def _create_or_update_entry(args: dict) -> str:
    list_id = args["list_id"]
    parent_record_id = args["parent_record_id"]
    parent_object = args.get("parent_object", "companies")
    entry_values = args.get("entry_values", {})

    body = {
        "data": {
            "parent_record_id": parent_record_id,
            "parent_object": parent_object,
            "entry_values": entry_values,
        },
    }
    data = client.put(f"/lists/{list_id}/entries", json=body)
    entry = data.get("data", data)
    entry_id = entry.get("entry_id") or entry.get("id", "")
    if isinstance(entry_id, dict):
        entry_id = entry_id.get("entry_id", str(entry_id))

    return f"Added/updated entry in '{list_id}' (entry ID: {entry_id})"


def _delete_entry(args: dict) -> str:
    list_id = args["list_id"]
    entry_id = args["entry_id"]

    client.delete(f"/lists/{list_id}/entries/{entry_id}")
    return f"Removed entry {entry_id} from list '{list_id}'."


def _archive_list(args: dict) -> str:
    list_id = args["list_id"]
    is_archived = args.get("is_archived", True)

    body = {"data": {"is_archived": is_archived}}
    data = client.patch(f"/lists/{list_id}", json=body)
    lst = data.get("data", data)
    name = lst.get("name", list_id)

    action = "Archived" if is_archived else "Unarchived"
    return f"{action} list: {name}"
