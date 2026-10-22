#!/usr/bin/env python3
"""Pre-Antigravity acceptance tests: content and structural checks, not device QC."""
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent

REQUIRED={
 1:["I LOVE YOU","iloveyou.usdz",'rel="ar"'],
 2:["You bring me so much joy babe!","pointermove","SCRATCH HERE"],
 3:["Just a little reminder that loving you is my favorite part of every day. ❤️"],
 4:["Emergency alert: Your husband thinks you're ridiculously beautiful. ❤️","If today feels heavy, remember you never have to carry it all alone. I love you. ❤️"],
 5:["Quality of Husband Hugs","Ability to Find Things Right in Front of Him","Romantic Husband Skills","Listening to Wife's Stories","Overall Husband Cuteness","OUTSTANDING HUSBAND MATERIAL","HUSBAND PLACED ON ROMANTIC PROBATION"],
 6:["No matter how scattered life gets, my heart always belongs with you. ❤️"],
 7:["You're my favorite person.","I'd choose you all over again.","You make ordinary days special.","I love the life we're building.","You're my forever favorite. ❤️"],
 8:["Stolen Kiss","Bear Hug","Giggle Dust","Morning Coffee","Stardust","Pure Love","The Smoochinator 3000","Maximum Cuddle Concentrate","Ridiculous Romance Serum","The Giggle Elixir","Forever & Always Formula","Morning Magic Potion","Anti-Bad-Day Brew","The Justine Effect","You are my favorite discovery. ❤️"],
 9:["A handsome husband is thinking about you. (It's me. Obviously.)","Your future contains an unreasonable number of kisses.","Someone loves you more than coffee. And that's saying something.","A surprise hug is heading your way.","Your lucky number is 2. Because you and me. ❤️"],
 10:["LOVE OVERLOAD","∞%"],
 11:["heart.usdz","You have my whole heart. ❤️"],
 12:["Blake Shelton","I'll Name the Dogs","FR-FoZzp0D8","youtube-nocookie.com"],
 13:["Redeemable for one real hug from your husband. No expiration date. Unlimited renewals. ❤️"],
 14:["If I could go back to the beginning, I'd still choose you. Every single time.","Of all the places life could have taken me, I'm so glad it brought me here with you.","I can't wait to see all the adventures we haven't had yet. ❤️","I'd choose you forever."],
 15:["Greetings, Earthling. After searching the entire universe, we have confirmed that you are the most loved woman in existence. Your husband insisted we tell you. ❤️"],
 16:["The best part? We're still making the sequel."],
 17:["The missing heart was last seen in the immediate vicinity of Justine.","The husband admits he gave it away willingly and has absolutely no intention of getting it back.","Investigators uncovered overwhelming evidence of affection, laughter, and a lifetime of love.","GUILTY OF BEING LOVED","Sentence: A lifetime of kisses, hugs, and being stuck with me. ❤️"],
 18:["Every day with you gives me another reason to love you. ❤️"],
 19:["10 Forehead Kisses","25 Surprise Kisses","Unlimited Goodnight Kisses","One Ridiculously Long Hug + Kiss","No rushing allowed. ❤️"],
 20:["Of all the people in this enormous universe, I'm so glad I found you.","My favorite adventures are the ones we share.","Look at the beautiful little world we've made together.","Wherever life takes us, you're my favorite place to be.","Of all the places in the universe, my favorite will always be wherever you are. I love you, babe. ❤️"],
}

class HTMLCheck(HTMLParser):
 def __init__(self):
  super().__init__();self.main=0;self.buttons=0
 def handle_starttag(self,tag,attrs):
  if tag=="main":self.main+=1
  if tag=="button":self.buttons+=1

class ApprovedContent(unittest.TestCase):
 def test_all_twenty_pages_and_locked_text(self):
  self.assertEqual(len(REQUIRED),20)
  manifest=json.loads((ROOT/"surprises.json").read_text(encoding="utf-8"))["manifest"]
  self.assertEqual(len(manifest),20)
  for n in range(1,21):
   with self.subTest(surprise=n):
    path=ROOT/"surprises"/f"{n:02d}"/"index.html"
    html=path.read_text(encoding="utf-8")
    self.assertEqual(manifest[n-1]["route"],f"surprises/{n:02d}/")
    self.assertEqual(manifest[n-1]["sticker_number"],f"{n:02d}")
    self.assertEqual(manifest[n-1]["implementation_status"],"pending_rebuild")
    self.assertNotRegex(html,re.compile(r"\\b(?:tinkerbell|tink)\\b",re.I))
    parser=HTMLCheck();parser.feed(html)
    self.assertEqual(parser.main,1)
    self.assertGreater(parser.buttons,0)
    for phrase in REQUIRED[n]:
     self.assertIn(phrase,html)
 def test_gate_remains_closed(self):
  manifest=json.loads((ROOT/"surprises.json").read_text(encoding="utf-8"))["manifest"]
  self.assertTrue(all(x["implementation_status"]!="verified" for x in manifest))
  sticker=(ROOT/"scripts"/"generate_stickers.py").read_text(encoding="utf-8")
  self.assertIn('implementation_status',sticker)
  self.assertIn('parsed.scheme != "https"',sticker)

if __name__=="__main__":
 unittest.main()
