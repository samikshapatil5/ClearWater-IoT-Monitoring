# ClearWater UI update

Applied the requested final UI changes:

- Homepage keeps the ClearWater live monitoring design but uses the packaged image assets for the hero, environment section, and hardware gallery.
- Added a glossy, photo-inspired water droplet SVG with a smooth floating animation and realistic highlight/shadow treatment.
- Replaced the old feedback side blocks with a compact Dribbble-style feedback experience: star rating, category pills, short textarea, privacy hint, and a single visual monitoring-loop panel.
- Feedback submission remains connected to the existing `/api/feedback` backend endpoint.
- Existing dashboard, alerts, Agentic AI, history, sensor readings, authentication, backend and ESP32 files are retained.

## Run on Windows

1. Install Node.js LTS.
2. Open the `water-quality-monitoring-frontend` folder in VS Code.
3. Run `run.bat` or:

```bash
npm install
npm --prefix backend install
npm run dev
```

The bundled `node_modules` folder is intentionally excluded from this clean ZIP so npm installs the correct Windows/native packages on your machine.
