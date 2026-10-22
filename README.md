# Little Surprises for Justine (V1)

A lightweight static GitHub Pages website with 20 distinct, mobile-first interactive surprise destinations for Justine, accessed via QR stickers numbered 01–20.

## 🌟 Highlights
- **20 Interactive Destinations**:
  - `01`: 3D "I LOVE YOU" in Augmented Reality (iPhone AR Quick Look USDZ) with 3D WebGL fallback.
  - `02`: Beating 3D Heart in Augmented Reality (iPhone AR Quick Look USDZ) with 3D WebGL fallback.
  - `03`: "Steeped in Love" Tea (Justine) & Coffee (Kristian) interactive brewing experience.
  - `04`: Interactive Love Letter Scratch Card.
  - `05`: "100 Reasons Why I Love You" card generator.
  - `06`: Redeemable Love Coupon Book for Justine.
  - `07`: Retro Mixtape / Cassette Jukebox player.
  - `08`: Daily Love Fortune Cookie with cracking animation.
  - `09`: Hug & Kiss Overflow Meter.
  - `10`: Night Sky Starlight Constellation Heart.
  - `11`: Secret Cipher Decoder Wheel.
  - `12`: Romantic Couple's Trivia Quiz with confetti.
  - `13`: Virtual Flower Bouquet Builder.
  - `14`: Cozy Soundscape Ambient Audio Mixer.
  - `15`: Love Quote Slot Machine.
  - `16`: Pop the Floating Hearts Mini-Game.
  - `17`: Interactive Compliment Jar.
  - `18`: Choose Your Own Date Night adventure.
  - `19`: Memory Flipbook with photo placeholders.
  - `20`: Love Countdown & Ticking Timer with celebration fireworks.

## 📱 Real Camera AR Instructions & iPhone Device Testing
- **Experiences**: Destinations `01` and `02` feature real camera Augmented Reality powered by Apple AR Quick Look USDZ models (`assets/models/iloveyou.usdz` and `assets/models/heart.usdz`).
- **Owner Real-Device Testing Note**: AR Quick Look requires real camera passthrough on an iPhone/iPad running iOS Safari or Chrome. Please test directly on an iPhone after GitHub Pages deployment before printing final stickers. Non-iOS or desktop browsers will seamlessly load the interactive 3D WebGL/Canvas fallback.

## 🖨️ Generating Printable QR Sticker Sheet
1. Once GitHub Pages is activated and you have your final published URL (e.g. `https://<username>.github.io/<repo-name>/`), run:
   ```bash
   python3 scripts/generate_stickers.py "https://<username>.github.io/<repo-name>/"
   ```
2. Open `sticker_sheet.html` in your browser.
3. Print using standard Letter size (8.5" x 11") in portrait mode.
4. The sticker sheet renders a **4 columns x 5 rows grid** with **20 stickers**, numbered `#01` through `#20` with 1.5-inch square QR codes and generous quiet zones.

## 🚀 GitHub Pages Activation Instructions
1. Push this repository to GitHub.
2. Go to **Settings > Pages** in your GitHub repository.
3. Under **Build and deployment**, set **Source** to `Deploy from a branch`.
4. Select the `main` branch and `/ (root)` folder, then click **Save**.
5. GitHub Pages will build and deploy your site within 1–2 minutes.

## 📷 Owner Asset Customization
- **Photos**: Place custom personal photos inside `assets/images/` and update references in `surprises/19/index.html`.
- **Audio**: Place MP3 audio files inside `assets/audio/` and update references in `surprises/07/index.html`.

## 🧪 Automated Site Verification
Run the site test suite to verify file structure, manifest validity, and rule compliance:
```bash
python3 scripts/test_site.py
```
