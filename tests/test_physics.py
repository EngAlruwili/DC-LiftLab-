import unittest
from dataclasses import replace
from dc_liftlab.model import Parameters, simulate

class PhysicsChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = {m:simulate(m) for m in ('resistive','regenerative','export_loss')}

    def test_gravitational_reference(self):
        p=Parameters()
        self.assertAlmostEqual(p.mass*p.gravity*5/3600,6.8125)

    def test_lecture_example_independent(self):
        # Lecture pp. 83-87: 250 V shunt motor, line current 24 A,
        # Rf=125 ohm, Ra=.1 ohm, total brush drop 4 V, no rotation loss.
        ia=24-250/125
        developed=(250-ia*.1-4)*ia
        self.assertAlmostEqual(developed,5363.6)
        self.assertAlmostEqual(developed/(250*24)*100,89.3933333333)

    def test_energy_balance_and_limits(self):
        for _,m in self.results.values():
            self.assertLess(m['residual_percent_imported'],.1)
            self.assertLess(m['peak_current_A'],50)
            self.assertLess(m['peak_bus_V'],360)
            self.assertLess(abs(m['final_height_m']),.01)
            self.assertFalse(m['tripped'])

    def test_fair_trajectory_and_recovery(self):
        a,ma=self.results['resistive']; b,mb=self.results['regenerative']
        self.assertEqual(ma['exported_Wh'],0)
        self.assertGreater(mb['exported_Wh'],0)
        self.assertLess(mb['net_imported_Wh'],ma['net_imported_Wh'])
        self.assertLess(mb['exported_Wh'],500*9.81*ma['peak_height_m']/3600)
        self.assertLess(max(abs(x['height_m']-y['height_m']) for x,y in zip(a,b)),1e-6)

    def test_export_loss_fallback(self):
        rows,m=self.results['export_loss']
        self.assertTrue(any(r['resistor_W']>100 for r in rows if r['time_s']>20))
        self.assertTrue(all(r['grid_W']>=0 for r in rows if r['time_s']>=20))
        self.assertGreater(m['exported_Wh'],0)

    def test_four_quadrant_benchmark(self):
        self.assertEqual(simulate(benchmark=True)[1]['quadrants_visited'],4)

    def test_steady_load_torque(self):
        p=Parameters()
        rows=self.results['regenerative'][0]
        row=min(rows,key=lambda r:abs(r['time_s']-8))
        expected=(p.mass*p.gravity*p.drum_radius/p.gear_ratio+p.viscous_friction*row['speed_rad_s'])/p.torque_constant
        self.assertAlmostEqual(row['current_A'],expected,delta=.02)

    def test_timestep_convergence(self):
        base=self.results['regenerative'][1]
        fine=simulate(p=replace(Parameters(),dt=.00025))[1]
        self.assertLess(abs(base['net_imported_Wh']-fine['net_imported_Wh'])/fine['net_imported_Wh'],.001)
        self.assertLess(abs(fine['energy_residual_J']),abs(base['energy_residual_J']))

if __name__=='__main__':
    unittest.main()
