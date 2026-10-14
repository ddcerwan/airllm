"""Tri-state trust_remote_code policy for AutoModel.get_module_class — no torch/transformers needed.

We stub transformers.AutoConfig with a recorder that mimics the real one: loading with
trust_remote_code=False raises for custom-architecture checkpoints (so only remote code can read
them), and records every trust flag it was called with. This lets us assert the policy branches
without downloading anything.
"""

import sys
import types
import unittest
from pathlib import Path

_AIRLLM_DIR = Path(__file__).resolve().parents[1] / "airllm"

if "airllm" not in sys.modules:
    _pkg = types.ModuleType("airllm")
    _pkg.__path__ = [str(_AIRLLM_DIR)]
    sys.modules["airllm"] = _pkg


class _FakeAutoConfig:
    """Stands in for transformers.AutoConfig.from_pretrained."""

    # Set per-test: architecture names to expose, and whether native (False) parsing is supported.
    architectures = ["SomeModelForCausalLM"]
    native_ok = True
    calls = []  # list of trust_remote_code values this instance was called with

    @classmethod
    def from_pretrained(cls, path, trust_remote_code=False, **kwargs):
        cls.calls.append(trust_remote_code)
        if trust_remote_code is False and not cls.native_ok:
            raise ValueError("native parser cannot read this architecture")
        cfg = types.SimpleNamespace(architectures=list(cls.architectures))
        return cfg


def _load_automodel(fresh_calls):
    """Import auto_model with a stubbed transformers module and a fresh AutoConfig stub."""
    _FakeAutoConfig.calls = fresh_calls
    tf = types.ModuleType("transformers")
    tf.AutoConfig = _FakeAutoConfig
    sys.modules["transformers"] = tf
    # auto_model also imports sys.platform only, no other transformers symbols at module load.
    import importlib
    return importlib.import_module("airllm.auto_model")


class TestTrustRemoteCodePolicy(unittest.TestCase):
    def setUp(self):
        _FakeAutoConfig.architectures = ["SomeModelForCausalLM"]
        _FakeAutoConfig.native_ok = True

    def test_auto_native_first(self):
        """Default (None): native parser tried first; no remote code when it succeeds."""
        calls = []
        am = _load_automodel(calls)
        _, cls_name = am.AutoModel.get_module_class("model-x")
        self.assertEqual(cls_name, "AirLLMBaseModel")
        self.assertEqual(calls, [False], "auto mode must try the native (trust=False) parser first")

    def test_auto_falls_back_to_remote_for_custom_arch(self):
        """Default (None): custom arch fails natively, so it falls back to remote code exactly once."""
        _FakeAutoConfig.native_ok = False
        calls = []
        am = _load_automodel(calls)
        am.AutoModel.get_module_class("model-x")
        self.assertEqual(calls, [False, True], "auto mode falls back to remote only after native fails")

    def test_true_uses_remote_only(self):
        """trust_remote_code=True: remote code used directly, native never attempted."""
        calls = []
        am = _load_automodel(calls)
        am.AutoModel.get_module_class("model-x", trust_remote_code=True)
        self.assertEqual(calls, [True], "True must trust remote code without trying native first")

    def test_false_forbids_remote(self):
        """trust_remote_code=False: native only; must NOT fall back to remote on failure."""
        _FakeAutoConfig.native_ok = False
        calls = []
        am = _load_automodel(calls)
        with self.assertRaises(Exception):
            am.AutoModel.get_module_class("model-x", trust_remote_code=False)
        self.assertEqual(calls, [False], "False must never execute remote code, even on native failure")

    def test_known_arch_routes_to_subclass(self):
        """A recognised architecture still maps to its dedicated subclass."""
        _FakeAutoConfig.architectures = ["QWenLMHeadModel"]
        calls = []
        am = _load_automodel(calls)
        _, cls_name = am.AutoModel.get_module_class("model-x")
        self.assertEqual(cls_name, "AirLLMQWen")


if __name__ == "__main__":
    unittest.main()
