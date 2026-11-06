# DC LiftLab engineering report

Author: Abdullah Alruwaili. AI-assisted simulation project, prepared for author review and reproduction.

## Objective and scope

Quantify source energy and braking-resistor dissipation for a separately excited DC hoist under identical motion commands. Demonstrate loss of source receptivity during lowering. This version is a physics-based virtual test bench using illustrative parameters, not an experimentally validated digital twin or certified hoist controller.

## Equations and signs

Positive speed raises the payload. Positive current produces raising torque. Source power is positive into the system. With fixed flux, the back-EMF constant equals the torque constant in consistent SI units.

\[L_a\dot i_a=v_a-R_ai_a-k\omega-V_b\tanh(i_a/0.2)\]
\[J_{eq}\dot\omega=ki_a-mgr/G-B\omega-T_{brake},\qquad \dot h=r\omega/G\]
\[J_{eq}=J_{rotor}+m(r/G)^2\]
\[\frac{d}{dt}(C V_{dc}^2/2)=P_{interface}-P_{drive}-P_{resistor}\]

The brush-voltage smoothing prevents numerical chatter near zero current. The gearbox is ideal; its efficiency is not silently combined with motor efficiency. Core losses are omitted because no measured loss map is available. Viscous friction is the only continuous rotational loss. Field power is a separately supplied constant 80 W and is included in both imported energy and losses.

## Controller and bus

An outer speed PI includes gravitational torque feedforward. An inner current PI includes back EMF and resistive-drop feedforward. Both use conditional-integration anti-windup. The current command is limited to 50 A; terminal voltage is limited to 95% of bus voltage. Gains are illustrative tuned values, not a formal robustness proof.

The averaged bidirectional interface uses drive-power feedforward and proportional bus-voltage regulation, with finite 6 kW import and 4 kW export limits at the DC side. Its assumed efficiency is 97%, as is the motor converter's efficiency. These are power-level models; no AC current waveform or power-quality claim is made. When export is blocked, the interface cannot take negative DC power. A chopper activates above 330 V, reaches full duty at 335 V and drives a 20 ohm resistor. Its modeled peak capacity is sufficient for the included cases. No resistor thermal-capacity qualification is claimed.

The holding brake captures the shaft only near zero speed after a 50 ms zero-command dwell. Capture dissipates residual kinetic energy; static holding torque is limited. Brake release is idealized. A bus overvoltage latch disables armature voltage above 360 V, but this is not a complete emergency braking sequence. The validated demonstration concerns loss of energy receptivity with an available brake chopper. Field-loss and emergency-stop certification are outside this release.

## Numerical method

Fixed-step explicit integration at 0.5 ms; capacitor energy is integrated directly. Trace sampling is 20 ms. Energy metrics are accumulated at every integration step. Half-step convergence uses 0.25 ms. The simulator is computational replay, not a guaranteed real-time system.

## Experiments

1. Resistive baseline: zero export capability throughout.
2. Regenerative: export available throughout.
3. Export loss: export disabled at exactly 20 s while descending.
4. Independent inertia-only sinusoidal reversal: demonstrate all four speed/torque sign combinations. The hoist itself normally visits two.
5. One-at-a-time sensitivity: payload, rotor inertia and armature resistance varied by +/-20%.

The nominal speed profile integrates to 5 m up and 5 m down. Tiny final height offsets due to tracking are reported, not concealed. Comparisons use identical controllers, limits, loads and references. Initial and final capacitor/inductor/kinetic/potential-energy changes are retained in the audit.

## Energy accounting

\[E_{import}-E_{export}=E_{loss}+E_{resistor}+E_{brake}+\Delta E_{stored}+E_{residual}\]

Stored energy includes gravity, rotor/payload kinetic energy, armature inductance and DC capacitor energy. Total field supply consumption is counted during dwell as well as movement. Reported percentage improvement is reduction of net source energy over the specific full cycle, not a universal motor-efficiency improvement. Synthetic parameter uncertainty limits industrial extrapolation.

## Acceptance checks

The baseline must export zero energy; the regenerative case must return positive energy; export must stop after the injected failure. All demonstrated cases must stay below the chosen bus and current limits. Endpoint energy residual must be below 0.1% of imported energy. Half-step net-energy change must be below 0.1%, and the residual must decrease. These are project verification criteria, not industry safety standards.

See `results/RESULTS.md`, `summary.json` and `tests/test_physics.py` for computed evidence. The independent lecture calculation checks a known steady-state reference; it does not experimentally validate the transient model.

## Connection to the supplied course material

Dr. Ahmad Al-Subhi, *Electrical Machines, Lecture 5: DC Machines*, user-supplied 137-page lecture. Pages 32 and 36-37 establish EMF, torque and conversion power; page 57 gives separate excitation; pages 71-73 cover losses; pages 123 and 132-136 cover characteristics, starting and control. The model adds converter dynamics, feedback control, gravity and bus-energy management beyond the lecture. The original PDF is not redistributed.

## Sources

- MathWorks, DC Motor Control: https://www.mathworks.com/help/simscape-electrical/ug/dc-motor-control.html
- MathWorks, Four-quadrant operation: https://www.mathworks.com/help/simscape-electrical/ug/visualize-four-quadrant-operation-of-electric-drive-system.html
- ABB, cranes and hoists: https://www.abb.com/global/en/areas/motion/applications/cranes-hoists
- ABB, DCS880-A DC drives: https://www.abb.com/global/en/areas/motion/drives/dc-drives/dcs880-a

These references motivate architecture and application. They are not the source of the illustrative parameter set, and the project does not model a particular ABB product.
