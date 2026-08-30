"""Validate integration localization without importing Home Assistant."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


COMPONENT = Path(__file__).resolve().parents[1] / "custom_components/eva_cloud"


def _leaf_paths(value: object, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    if isinstance(value, dict):
        paths: set[tuple[str, ...]] = set()
        for key, child in value.items():
            paths |= _leaf_paths(child, (*prefix, key))
        return paths
    return {prefix}


class LocalizationTest(unittest.TestCase):
    def test_english_and_bokmal_have_identical_keys(self) -> None:
        english = json.loads((COMPONENT / "translations/en.json").read_text())
        bokmal = json.loads((COMPONENT / "translations/nb.json").read_text())
        self.assertEqual(_leaf_paths(english), _leaf_paths(bokmal))

    def test_entity_names_are_localized(self) -> None:
        bokmal = json.loads((COMPONENT / "translations/nb.json").read_text())
        self.assertEqual(
            "Aktive stemninger",
            bokmal["entity"]["sensor"]["active_moods"]["name"],
        )


if __name__ == "__main__":
    unittest.main()
