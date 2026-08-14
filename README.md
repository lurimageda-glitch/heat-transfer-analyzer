# Heat Transfer Analyser

A Streamlit web app that calculates steady-state 1-D heat conduction and convection through a composite plane wall (up to three solid layers, with convective boundary layers on both the hot and cold sides). Users interactively set fluid temperatures, convection coefficients, layer thicknesses, and thermal conductivities via the sidebar, and the app instantly computes the total thermal resistance, heat transfer rate, and overall U-value, displaying a per-layer resistance breakdown table and a live-updating temperature profile chart.

**Live app:** [PASTE YOUR STREAMLIT CLOUD URL HERE AFTER DEPLOYING]

## Running locally
```
pip install -r requirements.txt
streamlit run app.py
```
