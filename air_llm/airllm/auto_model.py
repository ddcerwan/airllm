import importlib
from transformers import AutoConfig
from sys import platform

is_on_mac_os = False

if platform == "darwin":
    is_on_mac_os = True

if is_on_mac_os:
    from airllm import AirLLMLlamaMlx

# Architectures that need a dedicated AirLLM subclass because of a non-standard module layout
# (custom remote-code models). Everything else uses the generic AirLLMBaseModel, which streams any
# standard *ForCausalLM (model.model.layers + lm_head / norm) and lets transformers own the
# forward pass, so newly released architectures work without code changes.
ARCH_OVERRIDES = {
    "ChatGLMModel": "AirLLMChatGLM",
    "ChatGLMForConditionalGeneration": "AirLLMChatGLM",
    "QWenLMHeadModel": "AirLLMQWen",
    "BaichuanForCausalLM": "AirLLMBaichuan",
    "BaiChuanForCausalLM": "AirLLMBaichuan",
    "InternLMForCausalLM": "AirLLMInternLM",
    "KimiK3ForConditionalGeneration": "AirLLMKimiK3",
    "Qwen3_5ForConditionalGeneration": "AirLLMQwen3_5",
    "Qwen4ExpForConditionalGeneration": "AirLLMQwen4Exp",
}


class AutoModel:
    def __init__(self):
        raise EnvironmentError(
            "AutoModel is designed to be instantiated "
            "using the `AutoModel.from_pretrained(pretrained_model_name_or_path)` method."
        )

    @classmethod
    def get_module_class(cls, pretrained_model_name_or_path, *inputs, **kwargs):
        # Reading the config can require executing the checkpoint's bundled remote code. Policy is
        # tri-state, mirroring AirLLMBaseModel: None (default) = auto (try the native parser first,
        # fall back to remote code only if it fails), True = always trust remote code,
        # False = never run remote code (may raise for custom-architecture models).
        trust_remote_code = kwargs.pop('trust_remote_code', None)
        token_kwargs = {'token': kwargs['hf_token']} if 'hf_token' in kwargs else {}

        def _load_config(trc):
            return AutoConfig.from_pretrained(pretrained_model_name_or_path,
                                              trust_remote_code=trc, **token_kwargs)

        if trust_remote_code is True:
            config = _load_config(True)
        elif trust_remote_code is False:
            config = _load_config(False)
        else:
            try:
                config = _load_config(False)
            except Exception:
                config = _load_config(True)

        architectures = getattr(config, "architectures", None) or []
        arch = architectures[0] if architectures else ""

        cls_name = ARCH_OVERRIDES.get(arch)
        if cls_name is None:
            print(f"using generic AirLLM streaming model for architecture: {arch or 'unknown'}")
            cls_name = "AirLLMBaseModel"
        return "airllm", cls_name

    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path, *inputs, **kwargs):

        if is_on_mac_os:
            return AirLLMLlamaMlx(pretrained_model_name_or_path, *inputs, **kwargs)

        # trust_remote_code stays in kwargs so it flows to the model constructor (which applies it to
        # the model's own config + tokenizer). get_module_class reads it too for architecture
        # detection; because Python builds a fresh local kwargs there when we splat **kwargs, its
        # pop() does not remove it from this frame's kwargs. Default None = auto (native first,
        # remote code only as a fallback), consistent with AirLLMBaseModel.
        module, class_name = AutoModel.get_module_class(
            pretrained_model_name_or_path, *inputs, **kwargs)
        module = importlib.import_module(module)
        class_ = getattr(module, class_name)
        return class_(pretrained_model_name_or_path, *inputs, **kwargs)
