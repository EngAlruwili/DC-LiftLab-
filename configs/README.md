# Parameter provenance

All default values in `baseline.json` are explicit illustrative engineering assumptions, not measurements or a commercial motor datasheet. No hardware has been built or tested.

The model represents a wound-field DC machine with fixed nominal flux. The SI torque/back-EMF constant is 1.2 N m/A (also V s/rad). Armature voltage is bounded by the DC bus and modulation limit. The current command limit is 50 A, not a manufacturer rating. Rotor inertia excludes reflected payload inertia, which is added once in the model. The ideal gearbox ratio is motor speed / drum speed. Gearbox losses and rope elasticity are omitted.

The 500 kg, 5 m nominal lift at 0.5 m/s requires 2452.5 W of steady gravitational power and 36.7875 N m at the motor shaft. Nominal gravitational energy is 24525 J = 6.8125 Wh. Field excitation consumes 80 W continuously, including dwell. These are design assumptions to be replaced by measured or sourced parameters before hardware correlation.

Brake engagement has a 50 ms command dwell and a low-speed capture condition; the holding torque is limited to 100 N m. Capture removes residual kinetic energy and records it as brake dissipation. This is a hybrid holding-brake approximation, not a validated emergency-stop model. Release is idealized. Field-loss protection is outside this version's scope.
