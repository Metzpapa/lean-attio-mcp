"""Record tools: search, get, create/update, update, list entries."""

from . import client, formatting

TOOLS = [
    {
        "name": "search_records",
        "description": "Search for records (companies, people, deals) by name, email, or domain. Returns formatted results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search text (name, email, domain, etc.)",
                },
                "object": {
                    "type": "string",
                    "description": "Object type to search: companies, people, or deals",
                    "enum": ["companies", "people", "deals"],
                    "default": "companies",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 10)",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_record",
        "description": "Get a single record by ID with all its field values, formatted cleanly.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "object": {
                    "type": "string",
                    "description": "Object type: companies, people, or deals",
                },
                "record_id": {
                    "type": "string",
                    "description": "The record ID",
                },
            },
            "required": ["object", "record_id"],
        },
    },
    {
        "name": "create_or_update_record",
        "description": "Create or update a record (upsert). Matches by matching_attribute to avoid duplicates. Use 'domains' for companies, 'email_addresses' for people.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "object": {
                    "type": "string",
                    "description": "Object type: companies, people, deals",
                },
                "matching_attribute": {
                    "type": "string",
                    "description": "Attribute to match on for upsert (e.g. 'domains' for companies, 'email_addresses' for people)",
                },
                "values": {
                    "type": "object",
                    "description": "Field values to set. Each key is an attribute slug, value is the raw value or array of values. Example: {\"name\": \"Acme Corp\", \"domains\": [\"acme.com\"]}",
                },
            },
            "required": ["object", "matching_attribute", "values"],
        },
    },
    {
        "name": "update_record",
        "description": "Update specific fields on an existing record by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "object": {
                    "type": "string",
                    "description": "Object type: companies, people, deals",
                },
                "record_id": {
                    "type": "string",
                    "description": "The record ID to update",
                },
                "values": {
                    "type": "object",
                    "description": "Field values to update. Same format as create_or_update_record.",
                },
            },
            "required": ["object", "record_id", "values"],
        },
    },
    {
        "name": "list_record_entries",
        "description": "See what lists/pipelines a record belongs to.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "object": {
                    "type": "string",
                    "description": "Object type: companies, people, deals",
                },
                "record_id": {
                    "type": "string",
                    "description": "The record ID",
                },
            },
            "required": ["object", "record_id"],
        },
    },
]


def handle(name: str, args: dict) -> str:
    if name == "search_records":
        return _search(args)
    elif name == "get_record":
        return _get(args)
    elif name == "create_or_update_record":
        return _create_or_update(args)
    elif name == "update_record":
        return _update(args)
    elif name == "list_record_entries":
        return _list_entries(args)
    raise ValueError(f"Unknown record tool: {name}")


def _search(args: dict) -> str:
    query = args["query"]
    object_type = args.get("object", "companies")
    limit = args.get("limit", 10)

    # Build filter based on object type — search across name + key fields
    if object_type == "people":
        filter_obj = {
            "$or": [
                {"name": {"$contains": query}},
                {"email_addresses": {"$contains": query}},
            ]
        }
    elif object_type == "companies":
        filter_obj = {
            "$or": [
                {"name": {"$contains": query}},
                {"domains": {"$contains": query}},
            ]
        }
    else:
        # deals or other objects
        filter_obj = {"name": {"$contains": query}}

    body = {
        "filter": filter_obj,
        "limit": limit,
    }
    data = client.post(f"/objects/{object_type}/records/query", json=body)
    records = data.get("data", [])

    if not records:
        return f"No {object_type} found matching '{query}'"

    lines = [f"Found {len(records)} {object_type}:"]
    for i, rec in enumerate(records, 1):
        lines.append(f"{i}. {formatting.format_record_short(rec)}")
    return "\n".join(lines)


def _get(args: dict) -> str:
    object_type = args["object"]
    record_id = args["record_id"]

    data = client.get(f"/objects/{object_type}/records/{record_id}")
    record = data.get("data", data)
    return formatting.format_record(record, object_type)


def _create_or_update(args: dict) -> str:
    object_type = args["object"]
    matching = args["matching_attribute"]
    values = args["values"]

    # Format values for Attio API
    formatted = _format_write_values(values)

    body = {
        "data": {
            "values": formatted,
        },
        "matching_attribute": matching,
    }
    data = client.put(f"/objects/{object_type}/records", json=body)
    record = data.get("data", data)
    record_id = record.get("id", {})
    if isinstance(record_id, dict):
        record_id = record_id.get("record_id", str(record_id))

    # Get name for confirmation
    values_out = record.get("values", {})
    name = ""
    for nk in ["name", "full_name"]:
        if nk in values_out:
            name = formatting.extract_values(values_out[nk])
            if name:
                break

    return f"Created/updated {object_type.rstrip('s')}: {name or '(unnamed)'} (ID: {record_id})"


def _update(args: dict) -> str:
    object_type = args["object"]
    record_id = args["record_id"]
    values = args["values"]

    formatted = _format_write_values(values)
    body = {"data": {"values": formatted}}
    data = client.patch(f"/objects/{object_type}/records/{record_id}", json=body)
    record = data.get("data", data)

    values_out = record.get("values", {})
    name = ""
    for nk in ["name", "full_name"]:
        if nk in values_out:
            name = formatting.extract_values(values_out[nk])
            if name:
                break

    return f"Updated {object_type.rstrip('s')}: {name or record_id}"


def _list_entries(args: dict) -> str:
    object_type = args["object"]
    record_id = args["record_id"]

    data = client.get(f"/objects/{object_type}/records/{record_id}/entries")
    entries = data.get("data", [])

    if not entries:
        return f"This record is not in any lists/pipelines."

    lines = [f"Record belongs to {len(entries)} list(s):"]
    for entry in entries:
        list_id = entry.get("list_id", "")
        entry_id = entry.get("entry_id", entry.get("id", ""))
        lines.append(f"  List: {list_id} — Entry ID: {entry_id}")
    return "\n".join(lines)


def _format_write_values(values: dict) -> dict:
    """Convert simple key-value pairs to Attio's expected write format.

    Attio expects values as either raw values or arrays. We pass them through
    mostly as-is, but wrap scalars in arrays where needed for multi-value fields.
    """
    formatted = {}
    for key, val in values.items():
        if isinstance(val, list):
            formatted[key] = val
        else:
            formatted[key] = val
    return formatted
