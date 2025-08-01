IEEE 14-Bus Voltage Stability & Compensation

Description
This script uses **Pandapower** to analyze voltage stability in the IEEE 14-bus system. It simulates a stressed condition by increasing load at Bus 3, identifies the weakest bus, and applies shunt compensation to restore voltage if it drops below 0.95 p.u.

Features
* Load stress simulation at Bus 3
* Weakest bus detection before/after stress
* Automatic shunt compensation (Q-injection)
* Step-by-step voltage improvement tracking

Requirements
* Python 3.7+
* `pandapower`, `pandas`
  Outputs voltage values and compensation progress in the console.
