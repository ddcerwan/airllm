"""Safe checkpoint loading — guards the pickle RCE fix.

``_safe_torch_load`` must reject a malicious ``.bin`` that uses pickle's reduce hook to run
arbitrary code, while still loading an ordinary tensor-only checkpoint. It needs torch, so the
whole module skips when torch is not installed (mirrors the project's other tests).
"""

import os
import pickle
import sys
import tempfile
import types
import unittest
from pathlib import Path

_AIRLLM_DIR = Path(__file__).resolve().parents[1] / "airllm"

# torch is a hard dependency of airllm.utils, so the import fails without it. Stub the package
# the same way the other dependency-free tests do, but still guard on a real torch below.
try:
    import torch  # noqa: F401
    _HAVE_TORCH = True
except Exception:
    _HAVE_TORCH = False

if "airllm" not in sys.modules:
    _pkg = types.ModuleType("airllm")
    _pkg.__path__ = [str(_AIRLLM_DIR)]
    sys.modules["airllm"] = _pkg


@unittest.skipUnless(_HAVE_TORCH, "torch is required to exercise _safe_torch_load")
class TestSafeTorchLoad(unittest.TestCase):
    def _load(self):
        from airllm.utils import _safe_torch_load
        return _safe_torch_load

    def test_malicious_pickle_is_rejected_not_executed(self):
        """A tampered checkpoint must not execute its embedded payload."""
        marker = Path(tempfile.gettempdir()) / "airllm_rce_marker"

        class _Payload:
            def __reduce__(self):
                # Classic pickle RCE: on load this would run `touch marker`.
                return (os.system, (f"touch {marker}",))

        # Defensive: the marker must not exist before we start.
        if marker.exists():
            marker.unlink()

        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "pytorch_model.bin"
            with open(bad, "wb") as f:
                pickle.dump({"weight": _Payload()}, f)

            _safe_torch_load = self._load()
            # weights_only=True blocks the reduce hook -> an unpickling error, not code execution.
            with self.assertRaises(Exception):
                _safe_torch_load(bad)

        # The critical assertion: the payload never ran.
        self.assertFalse(marker.exists(), "malicious pickle payload was executed!")

    def test_plain_tensor_checkpoint_loads(self):
        import torch

        with tempfile.TemporaryDirectory() as d:
            good = Path(d) / "pytorch_model.bin"
            torch.save({"weight": torch.zeros(2, 3)}, good)

            _safe_torch_load = self._load()
            sd = _safe_torch_load(good)

        self.assertIn("weight", sd)
        self.assertTrue(torch.is_tensor(sd["weight"]))
        self.assertEqual(tuple(sd["weight"].shape), (2, 3))


if __name__ == "__main__":
    unittest.main()
