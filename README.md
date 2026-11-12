# Diamonda 0.4.0 — Functional Mods

Windows-first mod manager for YouTube, Facebook, Discord and Spotify Web. Supports CSS packs and opt-in JavaScript behavior mods injected into a Diamonda-managed Chromium profile via CDP.

## New functional mods
- YouTube Creator Toolkit: playback speed, seek controls, Picture-in-Picture, Theater Mode, floating panel.
- Facebook Feed Toolkit: focus-feed toggle, hide detected side rails/stories, back-to-top, keyboard shortcut.
- Discord Power Toolkit: compact message mode and keyboard shortcuts to toggle compact mode/focus composer.
- Spotify Player Toolkit: play/pause, previous/next and keyboard shortcuts.

## Run
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Use
1. Start Diamonda and select a pack.
2. Press Apply. Packs containing JavaScript show a confirmation before execution.
3. Keep Diamonda running for automatic re-application after navigation/reload.
4. Press Unapply to run registered cleanup callbacks and remove injected CSS/UI.

## Notes
- CDP controls only the dedicated browser profile launched by Diamonda, not the user's regular browser profile.
- Sign into supported websites once in that dedicated profile.
- JavaScript packs can interact with the current page. Only run packs from sources you trust.
- Website DOM changes can break app-specific selectors; test each target website after updates.
- Native desktop apps are not supported by this web injector.
- CDP is bound to 127.0.0.1; do not expose the debugging port to a network.


## Diamonda 0.4.1 — Ad cleanup packs

Added two opt-in packs:
- **YouTube Ad Cleaner**: hides identifiable ad placements and clicks the visible Skip Ad button when available. It does not block network requests or bypass non-skippable ads.
- **Spotify Sponsored Cleaner**: hides identifiable sponsored UI placements. It does not block audio ads delivered in Spotify's playback stream.

Apply these packs only in the Diamonda-managed Chromium profile. Website selectors can change at any time; this is best-effort page-level filtering, not a guarantee of removing every ad. JavaScript packs require explicit confirmation and can be removed with Unapply.
