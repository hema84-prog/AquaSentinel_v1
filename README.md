# AquaSentinel — Water Network Operations Prototype

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open `http://localhost:8501`.

## Navigation

- Overview — scenario-based telemetry and decision trace
- Live pipe twin — animated pipe, leak/burst modes and browser-generated sound
- Network map — schematic network and suspected segment
- Repair operations — simulated work order and verification workflow
- Detection engine — explainable rule checks and synthetic evaluation
- Leak localization — synthetic multi-node evidence ranking
- Components guide — plain-language component and system walkthrough
- Real-world water loss & research — sourced India case library, evidence register, filters and a comparable Delhi Jal Board water-balance pie chart

## Evidence and scope

The application distinguishes non-revenue water (NRW) from physical pipeline leakage. CAG Delhi Jal Board figures cover FY 2017–18 through FY 2021–22; the report was tabled on 23 March 2026. News reports are explicitly labelled as reported estimates and are not mixed into the Delhi audit chart.

All application telemetry, pipe events, detection outcomes, localization scores, audio and repair state changes are simulated. No physical sensor or municipal network is connected. The rule-based detector and synthetic test metrics are not field-validated performance claims.

## Repair Operations: Interactive Street Map
The Repair Operations page includes an interactive OpenStreetMap basemap with a conceptual underground pipe overlay, turning segments, sensor markers, inlet/outlet flow-meter markers, popups, zoom controls, and scenario-highlighted suspected segment. It requires internet access to load Leaflet and OpenStreetMap tiles. Pipe routes and sensor coordinates are illustrative and are not verified municipal infrastructure data.
