"""SI-unit averaged drive. Positive shaft rotation raises the payload."""
from dataclasses import dataclass, asdict
import math

@dataclass
class Parameters:
    mass: float = 500.0
    gravity: float = 9.81
    drum_radius: float = 0.15
    gear_ratio: float = 20.0
    rotor_inertia: float = 0.20
    armature_resistance: float = 0.5
    armature_inductance: float = 0.02
    torque_constant: float = 1.2
    viscous_friction: float = 0.015
    brush_drop: float = 2.0
    field_power: float = 80.0
    converter_efficiency: float = 0.97
    interface_efficiency: float = 0.97
    bus_capacitance: float = 0.02
    bus_reference: float = 320.0
    import_limit: float = 6000.0
    export_limit: float = 4000.0
    braking_resistance: float = 20.0
    chopper_threshold: float = 330.0
    chopper_band: float = 5.0
    bus_trip: float = 360.0
    current_limit: float = 50.0
    speed_kp: float = 2.0
    speed_ki: float = 8.0
    current_kp: float = 6.0
    current_ki: float = 150.0
    mechanical_brake_torque: float = 100.0
    brake_delay: float = 0.05
    dt: float = 0.0005
    duration: float = 29.0

def clip(x, lo, hi):
    return min(hi, max(lo, x))

def reference(t):
    """Smooth 5 m lift, dwell, 5 m lower, dwell (nominal integral)."""
    for start, sign in [(1.0, 1.0), (15.0, -1.0)]:
        u = t - start
        if 0 <= u < 2:
            return sign * 0.25 * (1 - math.cos(math.pi*u/2))
        if 2 <= u < 10:
            return sign * 0.5
        if 10 <= u < 12:
            return sign * 0.25 * (1 + math.cos(math.pi*(u-10)/2))
    return 0.0

def simulate(mode='regenerative', p=None, benchmark=False):
    if mode not in ('resistive', 'regenerative', 'export_loss'):
        raise ValueError('Unknown scenario')
    p = p or Parameters()
    if p.dt <= 0 or p.dt > .002 or p.mass < 0:
        raise ValueError('Require 0 < dt <= 0.002 and mass >= 0')
    radius = p.drum_radius / p.gear_ratio
    inertia = p.rotor_inertia + (0 if benchmark else p.mass * radius**2)
    gravity_torque = 0 if benchmark else p.mass*p.gravity*radius
    current = omega = height = zs = zi = 0.0
    voltage = p.bus_reference
    initial_bus_energy = .5*p.bus_capacitance*voltage**2
    imported = exported = losses = resistor = brake_energy = 0.0
    sum_error = peak_current = peak_bus = 0.0
    zero_since = 0.0
    rows, quadrants = [], set()
    step_count = round(p.duration/p.dt)
    stride = max(1, round(.02/p.dt))
    tripped = False
    for n in range(step_count+1):
        t = n*p.dt
        vref = reference(t)
        wref = vref/radius
        if benchmark:
            wref = 60*math.sin(2*math.pi*t/10)
        if abs(wref) > 1e-9:
            zero_since = t
        hold = not benchmark and abs(wref)<1e-9 and abs(omega)<.6 and t-zero_since>=p.brake_delay
        error = wref-omega
        raw_iref = gravity_torque/p.torque_constant + p.speed_kp*error + zs
        iref = clip(raw_iref, -p.current_limit, p.current_limit)
        # Conditional integration implements anti-windup at both saturation stages.
        if abs(raw_iref) <= p.current_limit or error*raw_iref < 0:
            zs += p.speed_ki*error*p.dt
        ierr = iref-current
        raw_va = p.torque_constant*omega + p.armature_resistance*current + p.current_kp*ierr + zi
        va = clip(raw_va, -.95*voltage, .95*voltage)
        if abs(raw_va) <= .95*voltage or ierr*raw_va < 0:
            zi += p.current_ki*ierr*p.dt
        if hold or tripped:
            va = 0.0
            zs = zi = 0.0
        brush_v = p.brush_drop*math.tanh(current/.2)
        armature_power = va*current
        drive_power = armature_power/p.converter_efficiency if armature_power>=0 else armature_power*p.converter_efficiency
        export_available = mode != 'resistive' and not(mode=='export_loss' and t>=20)
        # Finite-power averaged interface, with DC voltage regulation.
        interface_power = clip(drive_power+200*(p.bus_reference-voltage),
                               -p.export_limit if export_available else 0.0, p.import_limit)
        grid_power = interface_power/p.interface_efficiency if interface_power>=0 else interface_power*p.interface_efficiency
        duty = clip((voltage-p.chopper_threshold)/p.chopper_band, 0, 1)
        brake_power = duty*voltage**2/p.braking_resistance
        copper = p.armature_resistance*current**2
        brush = brush_v*current
        friction = p.viscous_friction*omega**2
        loss_power = copper+brush+friction+(drive_power-armature_power)+(grid_power-interface_power)+p.field_power
        acceleration = (p.torque_constant*current-gravity_torque-p.viscous_friction*omega)/inertia
        if hold and abs(gravity_torque-p.torque_constant*current) <= p.mechanical_brake_torque:
            brake_energy += .5*inertia*omega**2
            omega = 0.0
            acceleration = 0.0
        peak_current = max(peak_current, abs(current))
        peak_bus = max(peak_bus, voltage)
        sum_error += (wref-omega)**2
        if abs(omega)>1 and abs(current)>.2:
            quadrants.add((1 if omega>0 else -1, 1 if current>0 else -1))
        stored = .5*inertia*omega**2 + .5*p.armature_inductance*current**2 + .5*p.bus_capacitance*voltage**2-initial_bus_energy + (0 if benchmark else p.mass*p.gravity*height)
        residual = imported-exported-losses-resistor-brake_energy-stored
        if n % stride == 0 or n==step_count:
            state = 'TRIPPED' if tripped else ('HOLDING' if hold else ('BRAKE CHOPPER' if duty>.01 else ('REGENERATING' if grid_power<0 else 'MOTORING')))
            rows.append(dict(time_s=t, height_m=height, speed_rad_s=omega, reference_rad_s=wref,
                             current_A=current, torque_Nm=p.torque_constant*current, bus_V=voltage,
                             grid_W=grid_power, field_W=p.field_power, resistor_W=brake_power,
                             imported_Wh=imported/3600, exported_Wh=exported/3600,
                             losses_Wh=losses/3600, resistor_Wh=resistor/3600,
                             brake_Wh=brake_energy/3600, energy_residual_J=residual, state=state))
        if n==step_count:
            break
        imported += (max(grid_power,0)+p.field_power)*p.dt
        exported += max(-grid_power,0)*p.dt
        losses += loss_power*p.dt
        resistor += brake_power*p.dt
        height += radius*omega*p.dt
        omega += acceleration*p.dt
        current += (va-p.armature_resistance*current-p.torque_constant*(omega-acceleration*p.dt)-brush_v)/p.armature_inductance*p.dt
        # Integrate capacitor energy rather than voltage to preserve its balance.
        bus_e = .5*p.bus_capacitance*voltage**2+(interface_power-drive_power-brake_power)*p.dt
        if bus_e<=0:
            raise ArithmeticError('DC bus collapsed')
        voltage = math.sqrt(2*bus_e/p.bus_capacitance)
        tripped = tripped or voltage>p.bus_trip
    metrics = dict(mode=mode, imported_Wh=imported/3600, exported_Wh=exported/3600,
                   net_imported_Wh=(imported-exported)/3600, resistor_Wh=resistor/3600,
                   other_losses_Wh=losses/3600, brake_Wh=brake_energy/3600,
                   peak_current_A=peak_current, peak_bus_V=peak_bus,
                   speed_rmse_rad_s=math.sqrt(sum_error/(step_count+1)),
                   final_height_m=height, peak_height_m=max(r['height_m'] for r in rows),
                   energy_residual_J=residual, residual_percent_imported=100*abs(residual)/max(imported,1),
                   quadrants_visited=len(quadrants), tripped=tripped)
    return rows, metrics
