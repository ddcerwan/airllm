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
        # Reading the config can require executing the checkpoint's bundled remote code. Default to
        # NOT trusting it: try transformers' native parser first and only fall back to remote code
        # when the native parser can't read the architecture (custom remote-code models). This
        # mirrors what AirLLMBaseModel does internally. Pass trust_remote_code=True to force it on.
        trust_remote_code = kwargs.pop('trust_remote_code', False)
        token_kwargs = {'token': kwargs['hf_token']} if 'hf_token' in kwargs else {}

        def _load_config(trc):
            return AutoConfig.from_pretrained(pretrained_model_name_or_path,
                                              trust_remote_code=trc, **token_kwargs)

        if trust_remote_code:
            config = _load_config(True)
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

        # trust_remote_code is consumed here (config auto-detection) and must not be forwarded to the
        # model class constructor, which decides remote-code usage on its own.
        trust_remote_code = kwargs.pop('trust_remote_code', False)
        module, class_name = AutoModel.get_module_class(
            pretrained_model_name_or_path, *inputs, trust_remote_code=trust_remote_code, **kwargs)
        module = importlib.import_module(module)
        class_ = getattr(module, class_name)
        return class_(pretrained_model_name_or_path, *inputs, **kwargs)
