"""Extract clean values from Attio's nested value arrays."""


def extract_value(val: dict) -> str:
    """Pull the display-friendly value from a single Attio value object."""
    # Try keys in priority order
    for key in [
        "display_value",
        "full_name",
        "value",
        "email_address",
        "domain",
        "phone_number",
    ]:
        if key in val and val[key] is not None:
            return str(val[key])

    # Nested option/status
    if "option" in val and val["option"]:
        return val["option"].get("title", str(val["option"]))
    if "status" in val and val["status"]:
        return val["status"].get("title", str(val["status"]))

    # Currency
    if "currency_value" in val and val["currency_value"] is not None:
        currency = val.get("currency_code", "")
        return f"{currency} {val['currency_value']}"

    # Date
    if "date" in val and val["date"] is not None:
        return str(val["date"])

    # Target record reference
    if "target_record_id" in val and val["target_record_id"]:
        return f"[record:{val['target_record_id']}]"

    return ""


def extract_values(values: list) -> str:
    """Extract from a list of value objects, joining multiples with ', '."""
    if not values:
        return ""
    parts = [extract_value(v) for v in values if extract_value(v)]
    return ", ".join(parts)


def format_record(record: dict, object_type: str = "") -> str:
    """Format a single record into clean text."""
    values = record.get("values", {})
    record_id = record.get("id", {})
    if isinstance(record_id, dict):
        record_id = record_id.get("record_id", str(record_id))

    # Get the name
    name = ""
    for name_key in ["name", "full_name", "first_name"]:
        if name_key in values:
            name = extract_values(values[name_key])
            if name:
                break

    # Singularize: companies -> Company, people -> Person, deals -> Deal
    if object_type:
        singular_map = {"companies": "Company", "people": "Person", "deals": "Deal"}
        header = singular_map.get(object_type, object_type.rstrip("s").capitalize())
    else:
        header = "Record"
    lines = [f"{header}: {name or '(unnamed)'} (ID: {record_id})"]

    # Show all non-empty values, skip noise
    skip_attrs = {"name", "full_name", "record_id"}
    for attr, vals in values.items():
        if attr in skip_attrs:
            continue
        display = extract_values(vals)
        if display and not display.startswith("[record:"):
            label = attr.replace("_", " ").replace("-", " ").title()
            lines.append(f"  {label}: {display}")

    return "\n".join(lines)


def format_record_short(record: dict) -> str:
    """One-line summary for search results."""
    values = record.get("values", {})
    record_id = record.get("id", {})
    if isinstance(record_id, dict):
        record_id = record_id.get("record_id", str(record_id))

    name = ""
    for name_key in ["name", "full_name", "first_name"]:
        if name_key in values:
            name = extract_values(values[name_key])
            if name:
                break

    # Try to get a secondary identifier
    secondary = ""
    for sec_key in ["primary_domain", "domains", "email_addresses", "primary_email_address"]:
        if sec_key in values:
            secondary = extract_values(values[sec_key])
            if secondary:
                break

    parts = [name or "(unnamed)"]
    if secondary:
        parts.append(f"({secondary})")
    parts.append(f"— ID: {record_id}")
    return " ".join(parts)


def format_list_entry(entry: dict, index: int, record_names: dict | None = None) -> str:
    """Format a pipeline/list entry."""
    entry_id = entry.get("entry_id") or entry.get("id", {})
    if isinstance(entry_id, dict):
        entry_id = entry_id.get("entry_id", str(entry_id))

    parent_record_id = entry.get("parent_record_id", "")
    values = entry.get("entry_values", entry.get("values", {}))

    # Resolve parent record name from lookup dict
    name = ""
    if record_names and parent_record_id:
        name = record_names.get(parent_record_id, "")

    parts = [f"{index}. {name or parent_record_id}"]

    # Show entry-specific values (stage, etc.), skip noise
    skip_attrs = {"entry_id", "owner", "created_by", "created_at"}
    for attr, vals in values.items():
        if attr in skip_attrs:
            continue
        display = extract_values(vals)
        if display and not display.startswith("[record:"):
            label = attr.replace("_", " ").replace("-", " ").title()
            parts.append(f"{label}: {display}")

    return " — ".join(parts)


def format_note(note: dict) -> str:
    """Format a note."""
    title = note.get("title", "(no title)")
    content = note.get("content_plaintext", note.get("content", ""))
    created = note.get("created_at", "")
    author = ""
    if note.get("author"):
        author = note["author"].get("name", "")

    lines = [f"Note: {title}"]
    if author:
        lines.append(f"  By: {author}")
    if created:
        lines.append(f"  Created: {created[:10]}")
    if content:
        lines.append(f"  {content[:500]}")
    return "\n".join(lines)


def format_task(task: dict) -> str:
    """Format a task."""
    content = task.get("content_plaintext", task.get("content", "(no content)"))
    deadline = task.get("deadline_at", "")
    completed = task.get("is_completed", False)
    task_id = task.get("id", "")
    if isinstance(task_id, dict):
        task_id = task_id.get("task_id", str(task_id))
    assignees = task.get("assignees", [])

    status = "Done" if completed else "Open"
    lines = [f"Task: {content} [{status}] (ID: {task_id})"]
    if deadline:
        lines.append(f"  Deadline: {deadline[:10]}")
    if assignees:
        names = [a.get("name", a.get("email_address", "")) for a in assignees]
        lines.append(f"  Assigned to: {', '.join(n for n in names if n)}")

    # Show linked records
    linked = task.get("linked_records", [])
    if linked:
        links = [lr.get("target_record_id", "") for lr in linked]
        lines.append(f"  Linked records: {', '.join(links)}")

    return "\n".join(lines)
