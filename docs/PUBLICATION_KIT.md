# Publication kit

Review the model, reproduce the tests and adapt the wording to work you have personally understood and verified before posting. The text below reports simulation results only.

## Suggested LinkedIn draft

When a DC hoist lowers a load, where does the energy go?

DC LiftLab explores that question through a Python virtual test bench for a separately excited DC machine and an industrial-style hoist duty cycle.

The project compares resistor braking, regenerative braking and loss of source receptivity during descent, using the same load, speed reference and control settings.

For the illustrative 500 kg duty cycle, the simulation returned 4.75 Wh to the source and reduced net source energy from 10.32 Wh to 5.58 Wh, a 45.90% reduction relative to the resistor-braking case. These values apply to this model and duty cycle; they are not measured industrial savings.

The most interesting test occurs at 20 seconds: source export becomes unavailable. The brake chopper absorbs excess energy, with peak DC bus voltage around 331.72 V against a chosen 360 V trip threshold.

The package includes cascaded current/speed control, an energy audit, a separate four-quadrant benchmark, timestep convergence, parameter sensitivity, raw results and an interactive replay. Eight automated checks pass for the supplied baseline.

Built with AI assistance; the assumptions, limitations and reproducible code are documented openly. The next step is comparison with sourced motor parameters and physical measurements.

Attach the repository URL after publishing. Attach demo.mp4 and energy_comparison.png.

#ElectricalEngineering #PowerEngineering #DCMachines #MotorControl #PowerElectronics #Python

## Video

The recommended publication version is `results/demo_narrated_ar.mp4`: 80 seconds, one English synthetic voice, burned-in Arabic captions and two final results/verification slides. The original silent replay remains available. The Arabic LinkedIn post and publishing instructions are supplied separately in the `LinkedIn_Publishing` folder.

`results/demo.mp4` is a 60-second silent replay of the 29-second export-loss simulation. The clock is simulation time. The GIF contains the same sequence. The slower playback allows the viewer to read the values.

## Discussion preparation

- Explain why a DC bus needs an energy sink during regeneration.
- Distinguish electromagnetic conversion power from actual energy returned to the source.
- Explain why field excitation still consumes energy while the armature generates.
- Explain the two control loops, feedforward terms and saturation behavior.
- Distinguish brake-resistor dissipation from mechanical load holding.
- Explain why the hoist cycle visits two quadrants, while the separate benchmark visits four.
- Explain the omitted loss mechanisms and why the percentage result cannot be generalized.

## Repository description

Physics-based DC hoist simulation with regenerative braking, cascaded PI control, DC-bus energy management, reproducible energy audits and fault-scenario replay.
