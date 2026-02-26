"""Schema tools: list attributes, create attributes, list/create select options and statuses."""

from . import client

TOOLS = [
    {
        "name": "list_attributes",
        "description": "List all attributes (fields) on an object or list. Use target='objects' for companies/people/deals, target='lists' for list-specific attributes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Either 'objects' or 'lists'",
                    "enum": ["objects", "lists"],
                },
                "target_id": {
                    "type": "string",
                    "description": "Object slug (companies, people, deals) or list ID/slug",
                },
            },
            "required": ["target", "target_id"],
        },
    },
    {
        "name": "create_attribute",
        "description": "Create a new attribute (field) on an object or list. Types: text, number, checkbox, date, timestamp, currency, select, status, rating, record-reference, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Either 'objects' or 'lists'",
                    "enum": ["objects", "lists"],
                },
                "target_id": {
                    "type": "string",
                    "description": "Object slug or list ID/slug",
                },
                "title": {
                    "type": "string",
                    "description": "Display name for the attribute",
                },
                "api_slug": {
                    "type": "string",
                    "description": "API slug (snake_case). Auto-generated from title if not provided.",
                },
                "type": {
                    "type": "string",
                    "description": "Attribute type: text, number, checkbox, date, timestamp, currency, select, status, rating, record-reference, personal-name, email-address, phone-number, domain, interaction",
                },
                "is_multiselect": {
                    "type": "boolean",
                    "description": "For select/status types, allow multiple selections",
                    "default": False,
                },
                "relationship": {
                    "type": "object",
                    "description": "For record-reference type: {\"target_object\": \"companies\"} etc.",
                },
                "default_currency_code": {
                    "type": "string",
                    "description": "For currency type: ISO currency code (e.g. 'USD')",
                },
            },
            "required": ["target", "target_id", "title", "type"],
        },
    },
    {
        "name": "list_select_options",
        "description": "List options for a select attribute, or statuses for a status attribute.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Either 'objects' or 'lists'",
                    "enum": ["objects", "lists"],
                },
                "target_id": {
                    "type": "string",
                    "description": "Object slug or list ID/slug",
                },
                "attribute": {
                    "type": "string",
                    "description": "Attribute slug",
                },
                "is_status": {
                    "type": "boolean",
                    "description": "Set true if this is a status attribute (uses /statuses endpoint instead of /options)",
                    "default": False,
                },
            },
            "required": ["target", "target_id", "attribute"],
        },
    },
    {
        "name": "create_select_option",
        "description": "Add a new option to a select attribute, or a new status to a status attribute.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Either 'objects' or 'lists'",
                    "enum": ["objects", "lists"],
                },
                "target_id": {
                    "type": "string",
                    "description": "Object slug or list ID/slug",
                },
                "attribute": {
                    "type": "string",
                    "description": "Attribute slug",
                },
                "title": {
                    "type": "string",
                    "description": "Display name for the option/status",
                },
                "is_status": {
                    "type": "boolean",
                    "description": "Set true for status attributes",
                    "default": False,
                },
            },
            "required": ["target", "target_id", "attribute", "title"],
        },
    },
]


def handle(name: str, args: dict) -> str:
    if name == "list_attributes":
        return _list_attributes(args)
    elif name == "create_attribute":
        return _create_attribute(args)
    elif name == "list_select_options":
        return _list_select_options(args)
    elif name == "create_select_option":
        return _create_select_option(args)
    raise ValueError(f"Unknown schema tool: {name}")


def _list_attributes(args: dict) -> str:
    target = args["target"]
    target_id = args["target_id"]

    data = client.get(f"/{target}/{target_id}/attributes")
    attrs = data.get("data", [])

    if not attrs:
        return f"No attributes found on {target}/{target_id}."

    lines = [f"Attributes on {target}/{target_id} ({len(attrs)}):"]
    for attr in attrs:
        slug = attr.get("api_slug", "")
        title = attr.get("title", "")
        attr_type = attr.get("type", "")
        is_system = attr.get("is_system", False)
        writable = attr.get("is_writable", True)

        flags = []
        if is_system:
            flags.append("system")
        if not writable:
            flags.append("read-only")

        flag_str = f" [{', '.join(flags)}]" if flags else ""
        lines.append(f"  {slug} ({attr_type}) — {title}{flag_str}")

    return "\n".join(lines)


def _create_attribute(args: dict) -> str:
    target = args["target"]
    target_id = args["target_id"]

    # Auto-generate slug from title if not provided
    slug = args.get("api_slug") or args["title"].lower().replace(" ", "_").replace("-", "_")

    body = {
        "data": {
            "title": args["title"],
            "api_slug": slug,
            "type": args["type"],
            "description": args.get("description") or None,
            "is_required": args.get("is_required", False),
            "is_unique": args.get("is_unique", False),
            "is_multiselect": args.get("is_multiselect", False),
            "config": args.get("config") or {},
        },
    }
    if args.get("relationship"):
        body["data"]["relationship"] = args["relationship"]
    if args.get("default_currency_code"):
        body["data"]["config"]["currency"] = {"default_currency_code": args["default_currency_code"]}

    data = client.post(f"/{target}/{target_id}/attributes", json=body)
    attr = data.get("data", data)
    slug = attr.get("api_slug", "")
    title = attr.get("title", args["title"])

    return f"Created attribute: {title} (slug: {slug}, type: {args['type']})"


def _list_select_options(args: dict) -> str:
    target = args["target"]
    target_id = args["target_id"]
    attribute = args["attribute"]
    is_status = args.get("is_status", False)

    endpoint = "statuses" if is_status else "options"
    data = client.get(f"/{target}/{target_id}/attributes/{attribute}/{endpoint}")
    items = data.get("data", [])

    kind = "statuses" if is_status else "options"
    if not items:
        return f"No {kind} for {attribute}."

    lines = [f"{kind.capitalize()} for {attribute} ({len(items)}):"]
    for item in items:
        title = item.get("title", "")
        item_id = item.get("id", {})
        if isinstance(item_id, dict):
            item_id = item_id.get("option_id") or item_id.get("status_id") or str(item_id)
        is_archived = item.get("is_archived", False)
        archived = " [archived]" if is_archived else ""
        lines.append(f"  {title}{archived} (ID: {item_id})")

    return "\n".join(lines)


def _create_select_option(args: dict) -> str:
    target = args["target"]
    target_id = args["target_id"]
    attribute = args["attribute"]
    title = args["title"]
    is_status = args.get("is_status", False)

    endpoint = "statuses" if is_status else "options"
    body = {"data": {"title": title}}
    data = client.post(f"/{target}/{target_id}/attributes/{attribute}/{endpoint}", json=body)
    item = data.get("data", data)
    item_id = item.get("id", {})
    if isinstance(item_id, dict):
        item_id = item_id.get("option_id") or item_id.get("status_id") or str(item_id)

    kind = "status" if is_status else "option"
    return f"Created {kind}: {title} (ID: {item_id})"
