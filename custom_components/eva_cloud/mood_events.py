"""Read explicit mood activations, not the unrelated current-state matches."""

from datetime import datetime, timezone
from typing import Any


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def mood_activations(home: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the observed Norwegian event feed requested by our API client.

    The feed does not identify an actor or distinguish a wall button, schedule,
    or app activation. Unknown event titles are deliberately not guessed.
    """
    moods = {}
    ambiguous = set()
    for mood in _list(home.get("moods")):
        if isinstance(mood, dict) and isinstance(mood.get("name"), str):
            if mood["name"] in moods:
                ambiguous.add(mood["name"])
            moods[mood["name"]] = mood
    groups = {g["id"]: g for g in _list(home.get("groups"))
              if isinstance(g, dict) and isinstance(g.get("id"), str)}
    result = []
    for event in _list(home.get("recentEvents")):
        if not isinstance(event, dict) or event.get("title") != "Stemning aktivert":
            continue
        name = event.get("bodyText")
        if not isinstance(name, str) or name not in moods or name in ambiguous:
            continue
        try:
            timestamp = datetime.fromisoformat(event["timestamp"])
        except (KeyError, TypeError, ValueError):
            continue
        if timestamp.tzinfo is None:
            continue
        mood = moods[name]
        ids = set(x for x in _list(mood.get("deviceIds")) if isinstance(x, str))
        group_ids = _list(mood.get("groupIds"))
        if any(not isinstance(g, str) or g not in groups for g in group_ids):
            continue  # Never claim complete membership for an unknown group.
        for group_id in group_ids:
            ids.update(x for x in _list(groups[group_id].get("deviceIds")) if isinstance(x, str))
        result.append({"timestamp": timestamp.astimezone(timezone.utc).isoformat(),
                       "mood": name, "device_ids": sorted(ids),
                       "matches_current_state": mood.get("active") is True})
    return sorted(result, key=lambda item: item["timestamp"], reverse=True)[:20]
