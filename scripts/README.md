# Profile artwork

The hero is an original, procedural wireframe surface with a moving section and route markers. It is conceptual artwork, not a scan or live telemetry. The project cards are original SVGs with no remote dependencies.

To regenerate:

```sh
python -m pip install Pillow
python scripts/build_art.py
```

Use `--stills` for a fast layout pass. Windows uses Arial Black, Segoe UI, and Consolas from the system font directory. On Linux, DejaVu is supported as a fallback. `--font-dir PATH` selects another directory with those font filenames. Fonts are not bundled; different fonts can change text metrics, so inspect the results after regenerating on a different machine.

The two GIFs loop every 7.68 seconds and use a shared palette to keep the static type stable. The README selects the portrait layout at 600px and serves static PNGs when the browser requests reduced motion. Its ordinary HTML text preserves all essential information without the artwork. The three project cards wrap onto separate lines on narrow screens.

Before publishing, inspect desktop and mobile layouts, reduced-motion image selection, image loading, and the GIF seam. Keep the generated assets checked in; rendering the profile requires no workflow, API key, or third-party image service.
