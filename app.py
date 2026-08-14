"""
AI Documentation
----------------
AI tools used: Claude (Anthropic) for app design, code generation, and debugging.

Key prompts given:
1. "Build a Streamlit heat transfer analyser app for a composite plane wall with
   conduction through up to 3 layers plus convection on both sides, showing a
   temperature profile chart and a per-layer resistance table."
2. "Add a sidebar with at least 3 interactive controls (sliders/number inputs/
   selectboxes) and make the chart and table update live with those inputs."
3. "Add error handling so invalid inputs (zero/negative thickness, conductivity,
   or convection coefficient) show a warning message instead of crashing the app."

Most important manual fix/verification: the thermal-resistance network calculation
(R = L/(k*A) for conduction, R = 1/(h*A) for convection) had to be manually checked
against Incropera's "Fundamentals of Heat and Mass Transfer" textbook formulas to
confirm resistances add in series correctly, and the temperature-profile x-axis
positions (cumulative resistance fractions) were manually verified to place each
interface at the correct location so the plotted profile matches the physical wall.
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Heat Transfer Analyser", page_icon="🔥", layout="wide")

# ----------------------------------------------------------------------------
# Title, subtitle, instructions
# ----------------------------------------------------------------------------
st.title("🔥 Heat Transfer Analyser")
st.subheader("Steady-State Conduction & Convection Through a Composite Plane Wall")
st.markdown(
    """
    **Instructions:** Use the sidebar to set the hot-side and cold-side fluid
    temperatures, the convection coefficients on each side, and the properties
    of up to three solid wall layers (thickness and thermal conductivity).
    The app calculates the total thermal resistance, the steady-state heat
    transfer rate, the overall heat transfer coefficient (U), and plots the
    temperature profile through the wall.
    """
)

# ----------------------------------------------------------------------------
# Sidebar — interactive inputs
# ----------------------------------------------------------------------------
st.sidebar.header("Input Parameters")

st.sidebar.markdown("**Fluid Temperatures**")
T_hot = st.sidebar.slider("Hot-side fluid temperature, T∞,h (°C)", -50, 500, 300, step=5)
T_cold = st.sidebar.slider("Cold-side fluid temperature, T∞,c (°C)", -50, 500, 25, step=5)

st.sidebar.markdown("**Convection Coefficients**")
h_hot = st.sidebar.number_input("Hot-side convection coeff., h_h (W/m²·K)", min_value=0.0, value=50.0, step=1.0)
h_cold = st.sidebar.number_input("Cold-side convection coeff., h_c (W/m²·K)", min_value=0.0, value=10.0, step=1.0)

st.sidebar.markdown("**Wall Area**")
area = st.sidebar.number_input("Cross-sectional area, A (m²)", min_value=0.0, value=1.0, step=0.1)

st.sidebar.markdown("**Wall Layers**")
n_layers = st.sidebar.selectbox("Number of solid layers", options=[1, 2, 3], index=1)

layer_data = []
default_k = [1.4, 0.04, 50.0]      # e.g. brick, insulation, steel
default_L = [0.10, 0.05, 0.01]
layer_names = ["Layer 1", "Layer 2", "Layer 3"]

for i in range(n_layers):
    st.sidebar.markdown(f"*{layer_names[i]}*")
    L = st.sidebar.number_input(
        f"{layer_names[i]} thickness, L (m)", min_value=0.0,
        value=default_L[i], step=0.01, key=f"L{i}"
    )
    k = st.sidebar.number_input(
        f"{layer_names[i]} conductivity, k (W/m·K)", min_value=0.0,
        value=default_k[i], step=0.1, key=f"k{i}"
    )
    layer_data.append({"name": layer_names[i], "L": L, "k": k})

# ----------------------------------------------------------------------------
# Error handling — invalid inputs show a warning, not a crash
# ----------------------------------------------------------------------------
errors = []

if h_hot <= 0:
    errors.append("Hot-side convection coefficient must be greater than 0.")
if h_cold <= 0:
    errors.append("Cold-side convection coefficient must be greater than 0.")
if area <= 0:
    errors.append("Cross-sectional area must be greater than 0.")
for ld in layer_data:
    if ld["L"] <= 0:
        errors.append(f"{ld['name']} thickness must be greater than 0.")
    if ld["k"] <= 0:
        errors.append(f"{ld['name']} thermal conductivity must be greater than 0.")
if T_hot == T_cold:
    errors.append("Hot-side and cold-side temperatures are equal — no heat transfer will occur.")

if errors:
    for e in errors:
        st.warning(f"⚠️ {e}")
    st.info("Please correct the inputs in the sidebar to see results.")
    st.stop()

# ----------------------------------------------------------------------------
# Calculations
# ----------------------------------------------------------------------------
R_conv_hot = 1 / (h_hot * area)
R_conv_cold = 1 / (h_cold * area)
R_layers = [ld["L"] / (ld["k"] * area) for ld in layer_data]

R_total = R_conv_hot + sum(R_layers) + R_conv_cold
Q = (T_hot - T_cold) / R_total          # heat transfer rate, W
U = 1 / (R_total * area)                # overall heat transfer coefficient, W/m^2.K

# ----------------------------------------------------------------------------
# Results table (Pandas)
# ----------------------------------------------------------------------------
st.markdown("### Results Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Heat Transfer Rate, Q", f"{Q:,.2f} W")
col2.metric("Overall U-value", f"{U:,.3f} W/m²·K")
col3.metric("Total Thermal Resistance", f"{R_total:.4f} K/W")

rows = [{"Element": "Hot-side convection", "R (K/W)": R_conv_hot, "ΔT (°C)": Q * R_conv_hot}]
for ld, R in zip(layer_data, R_layers):
    rows.append({"Element": f"Conduction – {ld['name']}", "R (K/W)": R, "ΔT (°C)": Q * R})
rows.append({"Element": "Cold-side convection", "R (K/W)": R_conv_cold, "ΔT (°C)": Q * R_conv_cold})

df = pd.DataFrame(rows)
df["R (K/W)"] = df["R (K/W)"].round(5)
df["ΔT (°C)"] = df["ΔT (°C)"].round(2)

st.markdown("### Thermal Resistance Breakdown")
st.dataframe(df, use_container_width=True)

# ----------------------------------------------------------------------------
# Temperature profile plot (Matplotlib) — updates with inputs
# ----------------------------------------------------------------------------
st.markdown("### Temperature Profile Through the Wall")

positions = [0]
temps = [T_hot]
current_T = T_hot
cumulative_R = 0

# hot-side film
cumulative_R += R_conv_hot
current_T -= Q * R_conv_hot
positions.append(cumulative_R)
temps.append(current_T)

# each solid layer
for ld, R in zip(layer_data, R_layers):
    cumulative_R += R
    current_T -= Q * R
    positions.append(cumulative_R)
    temps.append(current_T)

# cold-side film
cumulative_R += R_conv_cold
current_T -= Q * R_conv_cold
positions.append(cumulative_R)
temps.append(current_T)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(positions, temps, marker="o", color="#d62728", linewidth=2)
ax.set_xlabel("Cumulative thermal resistance (K/W)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Temperature Drop Across Wall Elements")
ax.grid(alpha=0.3)

labels = ["Hot fluid"] + [ld["name"] for ld in layer_data] + ["Cold fluid"]
for x, y, lab in zip(positions, temps, labels):
    ax.annotate(lab, (x, y), textcoords="offset points", xytext=(0, 8), fontsize=8, ha="center")

st.pyplot(fig)

st.caption(
    "Model assumes 1-D steady-state heat transfer through a composite plane wall "
    "with convective boundary layers on both sides (resistance-in-series network)."
)
