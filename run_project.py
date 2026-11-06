"""Run all experiments and generate the reproducibility package."""
import argparse, csv, json
from dataclasses import asdict, replace
from pathlib import Path
from dc_liftlab.model import Parameters, simulate

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config', type=Path)
    parser.add_argument('--no-media', action='store_true')
    args=parser.parse_args()
    p=Parameters(**json.loads(args.config.read_text())) if args.config else Parameters()
    out=ROOT/'results'; out.mkdir(exist_ok=True)
    (ROOT/'configs').mkdir(exist_ok=True)
    (out/'parameters_used.json').write_text(json.dumps(asdict(p),indent=2))
    all_rows={}; metrics=[]
    for mode in ('resistive','regenerative','export_loss'):
        rows,m=simulate(mode,p)
        all_rows[mode]=rows; metrics.append(m)
        with (out/f'{mode}.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    qrows,qmetrics=simulate(p=p,benchmark=True)
    with (out/'four_quadrant.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(qrows[0]));w.writeheader();w.writerows(qrows)
    sensitivity=[]
    for name in ('mass','rotor_inertia','armature_resistance'):
        for factor in (.8,1.2):
            _,m=simulate(p=replace(p,**{name:getattr(p,name)*factor}))
            sensitivity.append(dict(parameter=name,factor=factor,**m))
    fine=simulate(p=replace(p,dt=p.dt/2))[1]
    summary=dict(scenarios=metrics,four_quadrant=qmetrics,sensitivity=sensitivity,
                 convergence=dict(base_dt_s=p.dt,fine_dt_s=p.dt/2,fine_metrics=fine))
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    template=(ROOT/'dc_liftlab/viewer.html').read_text(encoding='utf-8')
    (out/'dashboard.html').write_text(template.replace('__DATA__',json.dumps(dict(traces=all_rows,metrics=metrics,parameters=asdict(p)))),encoding='utf-8')
    if not args.no_media:
        from dc_liftlab.media import generate
        generate(all_rows,metrics,qrows,out,p)
    baseline,regen=metrics[:2]
    reduction=100*(baseline['net_imported_Wh']-regen['net_imported_Wh'])/baseline['net_imported_Wh']
    lines=['# Generated simulation results','',
           'Illustrative parameters; numerical simulation, not experimental measurements.','',
           '| Scenario | Imported Wh | Exported Wh | Net Wh | Resistor Wh | Peak bus V |',
           '|---|---:|---:|---:|---:|---:|']
    for m in metrics:
        lines.append(f"| {m['mode']} | {m['imported_Wh']:.4f} | {m['exported_Wh']:.4f} | {m['net_imported_Wh']:.4f} | {m['resistor_Wh']:.4f} | {m['peak_bus_V']:.2f} |")
    lines += ['',f'Simulated net import reduction versus resistor braking: **{reduction:.2f}%** for this duty cycle and parameter set only.',
              f"Maximum sampled endpoint energy residual: {max(abs(m['energy_residual_J']) for m in metrics):.3f} J.",
              f"Four-quadrant inertial benchmark: {qmetrics['quadrants_visited']} quadrants visited.",
              '', 'See summary.json for convergence and sensitivity results. Field input and converter/interface losses are included.']
    (out/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print('\n'.join(lines))

if __name__=='__main__': main()
