#!/usr/bin/env python3
"""Source-level acceptance checks for the first five approved surprises.

These tests do not replace browser, touch, or iPhone AR testing.
"""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent

def page(number):
    return (ROOT / "surprises" / f"{number:02}" / "index.html").read_text(encoding="utf-8")

class BatchOneAcceptance(unittest.TestCase):
    def test_routes_and_manifest(self):
        manifest = json.loads((ROOT / "surprises.json").read_text(encoding="utf-8"))["manifest"]
        expected = [
            "I LOVE YOU in AR", "Love Lottery Scratch-Off",
            "Handwritten Love Letter", "Emergency Love Button",
            "Official Husband Report Card",
        ]
        self.assertEqual([entry["title"] for entry in manifest[:5]], expected)
        self.assertEqual([entry["route"] for entry in manifest[:5]],
                         [f"surprises/{n:02}/" for n in range(1, 6)])

    def test_ar_entrypoint(self):
        self.assertIn('rel="ar"', page(1))
        self.assertIn("iloveyou.usdz", page(1))
        self.assertIn("I LOVE YOU", page(1))

    def test_lottery(self):
        html = page(2)
        self.assertIn("You bring me so much joy babe!", html)
        self.assertIn("touch-action:none", html)
        self.assertIn("position:absolute", html)
        self.assertIn("pointermove", html)
        self.assertIn("Reveal my prize", html)

    def test_letter(self):
        html = page(3)
        self.assertIn("Just a little reminder that loving you is my favorite part of every day. ❤️", html)
        self.assertIn("aria-expanded", html)
        self.assertIn("classList.toggle('opened')", html)

    def test_emergency_messages(self):
        html = page(4)
        match = re.search(r"const messages=(\[.*?\]);let last=", html, re.S)
        self.assertIsNotNone(match)
        messages = json.loads(match.group(1))
        self.assertEqual(len(messages), 12)
        self.assertEqual(len(set(messages)), 12)
        self.assertEqual(messages[0], "Emergency alert: Your husband thinks you're ridiculously beautiful. ❤️")
        self.assertEqual(messages[-1], "If today feels heavy, remember you never have to carry it all alone. I love you. ❤️")
        self.assertIn("if(i>=last)i++", html)

    def test_report_card(self):
        html = page(5)
        for category in [
            "Quality of Husband Hugs",
            "Ability to Find Things Right in Front of Him",
            "Romantic Husband Skills",
            "Listening to Wife's Stories",
            "Overall Husband Cuteness",
        ]:
            self.assertIn(category, html)
        for verdict in [
            "OUTSTANDING HUSBAND MATERIAL",
            "HUSBAND IN GOOD STANDING",
            "HUSBAND REQUIRES ADDITIONAL TRAINING",
            "HUSBAND PLACED ON ROMANTIC PROBATION",
        ]:
            self.assertIn(verdict, html)
        self.assertIn("Regardless of rating, husband remains under a lifetime contract to love you. ❤️", html)
        self.assertIn("avg>=4.5", html)
        self.assertIn("avg>=3.5", html)
        self.assertIn("avg>=2.5", html)

if __name__ == "__main__":
    unittest.main()
