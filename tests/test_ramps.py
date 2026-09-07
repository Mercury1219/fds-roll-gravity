import math
import os
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import generate_roll_ramps as app


def components(code):
    rows = re.findall(r"&RAMP ID='(ramp_[xz])', T=([0-9.]+), F=([-0-9.]+) /", code)
    return {axis: [(float(t), float(v)) for name, t, v in rows if name == axis]
            for axis in ("ramp_x", "ramp_z")}


class RampTests(unittest.TestCase):
    def test_default_full_range(self):
        data = components(app.generate_fds(app.f, app.dt, app.total_time, app.theta0_deg, app.g))
        self.assertEqual(len(data["ramp_x"]), 1501)
        self.assertEqual(data["ramp_x"][0], (0.0, 0.0))
        self.assertEqual(data["ramp_z"][0], (0.0, -9.81))
        self.assertEqual(data["ramp_x"][-1], (300.0, 0.0))
        self.assertEqual(data["ramp_z"][-1], (300.0, -9.81))
        for (ta, _), (tb, _) in zip(data["ramp_x"], data["ramp_x"][1:]):
            self.assertAlmostEqual(tb - ta, 0.2)

    def test_extrema_and_sign(self):
        data = components(app.generate_fds(0.2, 1.25, 5, 10, 9.81))
        gx = [v for _, v in data["ramp_x"]]
        gz = [v for _, v in data["ramp_z"]]
        self.assertAlmostEqual(gx[1], 9.81 * math.sin(math.radians(10)), places=7)
        self.assertAlmostEqual(gx[3], -gx[1], places=7)
        self.assertAlmostEqual(gz[1], -9.81 * math.cos(math.radians(10)), places=7)
        self.assertEqual(gx[0], gx[2])

    def test_periodicity_and_magnitude(self):
        data = components(app.generate_fds(0.2, 0.2, 300, 10, 9.81))
        for axis in data.values():
            for (_, a), (_, b) in zip(axis, axis[25:]):
                self.assertAlmostEqual(a, b, places=7)
        for (_, gx), (_, gz) in zip(data["ramp_x"], data["ramp_z"]):
            self.assertAlmostEqual(math.hypot(gx, gz), 9.81, places=7)

    def test_changed_frequency_step_and_amplitude(self):
        data = components(app.generate_fds(0.5, 0.5, 2, 30, 10))
        self.assertAlmostEqual(data["ramp_x"][1][1], 5.0, places=7)
        self.assertAlmostEqual(data["ramp_z"][1][1], -5 * math.sqrt(3), places=7)
        self.assertAlmostEqual(data["ramp_x"][3][1], -5.0, places=7)

    def test_nondivisible_endpoint(self):
        times = [t for t, _ in components(app.generate_fds(0.3, 0.07, 1, 15, 9.81))["ramp_x"]]
        self.assertEqual(len(times), 16)
        self.assertEqual(times[-2:], [0.98, 1.0])
        self.assertEqual(len(set(times)), len(times))

    def test_step_longer_than_duration(self):
        data = components(app.generate_fds(0.2, 2, 1, 10, 9.81))
        self.assertEqual([t for t, _ in data["ramp_x"]], [0, 1])

    def test_static_gravity(self):
        for frequency, amplitude in ((0, 10), (0.2, 0)):
            data = components(app.generate_fds(frequency, 0.2, 1, amplitude, 9.81))
            self.assertTrue(all(v == 0 for _, v in data["ramp_x"]))
            self.assertTrue(all(v == -9.81 for _, v in data["ramp_z"]))

    def test_invalid_parameters(self):
        default = [0.2, 0.2, 300, 10, 9.81]
        for index in range(5):
            for value in (float("nan"), float("inf"), float("-inf"), -1):
                with self.subTest(index=index, value=value):
                    args = default.copy()
                    args[index] = value
                    with self.assertRaises(ValueError):
                        app.generate_fds(*args)
        for index in (1, 2, 4):
            args = default.copy()
            args[index] = 0
            with self.assertRaises(ValueError):
                app.generate_fds(*args)

    def test_small_step_keeps_unique_timestamps(self):
        data = components(app.generate_fds(0.2, 0.00001, 0.000025, 10, 9.81))
        self.assertEqual([t for t, _ in data["ramp_x"]], [0, 0.00001, 0.00002, 0.000025])

    def test_import_is_silent_and_does_not_need_tkinter(self):
        result = subprocess.run(
            [sys.executable, "-c", "import sys; sys.modules['tkinter'] = None; import generate_roll_ramps"],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    @unittest.skipUnless(os.environ.get("FDS_GUI_TEST") == "1", "requires a desktop; set FDS_GUI_TEST=1")
    def test_complete_window_and_copy(self):
        import tkinter as tk
        code = app.generate_fds(app.f, app.dt, app.total_time, app.theta0_deg, app.g)
        tested = []

        def check_window(root):
            widgets = []

            def visit(widget):
                widgets.append(widget)
                for child in widget.winfo_children():
                    visit(child)

            try:
                visit(root)
                box = next(w for w in widgets if isinstance(w, tk.Text))
                self.assertEqual(box.get("1.0", "end-1c"), code)
                self.assertEqual(box.yview()[0], 0.0)
                copy_button = next(w for w in widgets
                                   if w.winfo_class() == "TButton" and w.cget("text") == "复制全部")
                copy_button.invoke()
                self.assertEqual(root.clipboard_get(), code)
                tested.append(True)
            finally:
                root.destroy()

        with patch.object(tk.Tk, "mainloop", check_window):
            app.show_result(code)
        self.assertEqual(tested, [True])


if __name__ == "__main__":
    unittest.main()
