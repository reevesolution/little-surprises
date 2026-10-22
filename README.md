# Little Surprises for Justine

Twenty distinct, numbered, mobile-first surprises, reached by scanning private physical QR stickers. Static GitHub Pages; no sign-in, tracking, backend, or public index of the experiences.

## Status — independent Antigravity QC required

The 20 approved concepts have been implemented on `skippy/approved-surprises-rebuild`. This is a **review candidate, not a deployable or printable release**. The `surprises.json` manifest intentionally leaves every `implementation_status` at `pending_rebuild` until independent evidence and Captain approval. The sticker generator refuses to run against unverified content.

### Known acceptance gaps

- **#01 and #11 AR:** USDZ files inherited from Jules. Their geometry, iPhone Quick Look compatibility, and appearance have not been independently validated on a device. Browser fallbacks are animated 2D visuals, not equivalent 3D scenes.
- **#15 Alien Love Transmission:** animated browser experience exists, but **the approved real iPhone UFO AR model has not been created**. This is a blocker to full acceptance.
- **#12 Tiny Jukebox:** embeds Blake Shelton's official-channel **I'll Name the Dogs** audio, video ID `FR-FoZzp0D8`, on a user tap. Confirm that the embed works on iPhone Safari and that the external link fallback works; YouTube can restrict embeds.
- **#16 Now Showing: Us:** illustrated placeholder scenes only. Personal photos have not yet been provided.
- **#02, #03, #04, #05 and all other pages:** require actual touch/browser visual and behavioral tests. Source-level checks are not a substitute for human device testing.
- **QR printing:** no published production URL and no sticker sheet approved. The existing `sticker_sheet.html` is a legacy sample and must not be printed.

## Run local preflight

```sh
python3 -m unittest discover -s scripts -p 'test_approved_content.py' -v
python3 -m unittest discover -s scripts -p 'test_batch_one.py' -v
python3 scripts/test_site.py
```

The first two tests check source-level content and structure. `test_site.py` **must fail until all 20 experiences are independently verified**, by design. GitHub Actions additionally runs `node --check` on inline JavaScript.

## QR sticker production — only after approval

`scripts/generate_stickers.py` requires a real HTTPS base URL and all 20 entries marked verified. It creates `sticker_sheet.html` (4 columns × 5 rows on US Letter). Before printing, independently confirm every final URL, QR scan, correct numbering, correct sticker stock/layout, and that the QR provider can fetch images. Never print the old sample sheet.

## Antigravity gate

See `ANTIGRAVITY_GATE.md` for the independent review checklist and stop conditions. Do not merge Jules PR #2 or the rebuild PR, deploy, print, or mark all manifest entries verified before independent QC and explicit Captain approval.
