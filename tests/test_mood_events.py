"""Validate actual activation telemetry without importing Home Assistant."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location("mood_events", Path(__file__).resolve().parents[1]
    / "custom_components/eva_cloud/mood_events.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MoodEventsTest(unittest.TestCase):
    def setUp(self):
        self.home = {"moods": [{"name": "Hjemme", "deviceIds": ["thermostat"],
                                "groupIds": ["lights"], "active": True}],
                     "groups": [{"id": "lights", "deviceIds": ["lamp", "thermostat"]}],
                     "recentEvents": [{"title": "Stemning aktivert", "bodyText": "Hjemme",
                                       "timestamp": "2026-10-15T03:00:52.000+0000"}]}

    def test_actual_event_includes_expanded_members_and_utc_timestamp(self):
        self.assertEqual([{"timestamp": "2026-10-15T03:00:52+00:00", "mood": "Hjemme",
                           "device_ids": ["lamp", "thermostat"],
                           "matches_current_state": True}], module.mood_activations(self.home))

    def test_a_state_match_is_not_an_activation(self):
        self.home["recentEvents"] = []
        self.assertEqual([], module.mood_activations(self.home))

    def test_unknown_title_mood_timestamp_or_group_is_not_guessed(self):
        for field, value in (("title", "Temperatur endret"), ("bodyText", "Unknown"),
                             ("timestamp", "not a date"), ("timestamp", None),
                             ("timestamp", "2026-10-15T03:00:52")):
            with self.subTest(field=field, value=value):
                home = deepcopy(self.home)
                home["recentEvents"][0][field] = value
                self.assertEqual([], module.mood_activations(home))
        self.home["groups"] = []
        self.assertEqual([], module.mood_activations(self.home))

    def test_inactive_match_does_not_erase_an_explicit_activation(self):
        self.home["moods"][0]["active"] = False
        self.assertEqual(1, len(module.mood_activations(self.home)))
        self.assertFalse(module.mood_activations(self.home)[0]["matches_current_state"])

    def test_unordered_events_are_sorted_not_treated_as_new_by_list_order(self):
        event = self.home["recentEvents"][0]
        self.home["recentEvents"].append(event | {"timestamp": "2026-10-15T04:00:52Z"})
        self.assertEqual("2026-10-15T04:00:52+00:00", module.mood_activations(self.home)[0]["timestamp"])

    def test_missing_feed_is_safe_and_read_only(self):
        self.assertEqual([], module.mood_activations({}))
        before = deepcopy(self.home)
        module.mood_activations(self.home)
        self.assertEqual(before, self.home)

    def test_null_malformed_fields_and_ambiguous_names_fail_closed(self):
        for field in ("recentEvents", "moods", "groups"):
            home = deepcopy(self.home)
            home[field] = None
            self.assertEqual([], module.mood_activations(home))
        self.home["moods"].append(deepcopy(self.home["moods"][0]))
        self.assertEqual([], module.mood_activations(self.home))


if __name__ == "__main__":
    unittest.main()
