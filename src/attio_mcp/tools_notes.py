"""Note tools: create and list notes on records."""

from . import client, formatting

TOOLS = [
    {
        "name": "create_note",
        "description": "Add a note to a record (company, person, or deal).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parent_object": {
                    "type": "string",
                    "description": "Object type: companies, people, or deals",
                },
                "parent_record_id": {
                    "type": "string",
                    "description": "The record ID to attach the note to",
                },
                "title": {
                    "type": "string",
                    "description": "Note title",
                },
                "content": {
                    "type": "string",
                    "description": "Note body text (plain text or markdown)",
                },
            },
            "required": ["parent_object", "parent_record_id", "title", "content"],
        },
    },
    {
        "name": "list_notes",
        "description": "List notes on a record.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parent_object": {
                    "type": "string",
                    "description": "Object type: companies, people, or deals",
                },
                "parent_record_id": {
                    "type": "string",
                    "description": "The record ID to list notes for",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max notes to return (default 20)",
                    "default": 20,
                },
            },
            "required": ["parent_object", "parent_record_id"],
        },
    },
    {
        "name": "delete_note",
        "description": "Permanently delete a note. This is irreversible.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "note_id": {
                    "type": "string",
                    "description": "The note ID to delete",
                },
            },
            "required": ["note_id"],
        },
    },
]


def handle(name: str, args: dict) -> str:
    if name == "create_note":
        return _create_note(args)
    elif name == "list_notes":
        return _list_notes(args)
    elif name == "delete_note":
        return _delete_note(args)
    raise ValueError(f"Unknown note tool: {name}")


def _create_note(args: dict) -> str:
    body = {
        "data": {
            "parent_object": args["parent_object"],
            "parent_record_id": args["parent_record_id"],
            "title": args["title"],
            "format": "plaintext",
            "content": args["content"],
        },
    }
    data = client.post("/notes", json=body)
    note = data.get("data", data)
    note_id = note.get("note_id") or note.get("id", "")
    if isinstance(note_id, dict):
        note_id = note_id.get("note_id", str(note_id))

    return f"Created note: {args['title']} (ID: {note_id})"


def _list_notes(args: dict) -> str:
    params = {
        "parent_object": args["parent_object"],
        "parent_record_id": args["parent_record_id"],
        "limit": args.get("limit", 20),
    }
    data = client.get("/notes", params=params)
    notes = data.get("data", [])

    if not notes:
        return "No notes found on this record."

    lines = [f"Notes ({len(notes)}):"]
    for note in notes:
        lines.append(formatting.format_note(note))
        lines.append("")
    return "\n".join(lines)


def _delete_note(args: dict) -> str:
    note_id = args["note_id"]

    client.delete(f"/notes/{note_id}")
    return f"Permanently deleted note {note_id}."
