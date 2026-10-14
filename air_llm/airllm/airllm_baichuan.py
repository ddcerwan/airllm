
from transformers import GenerationConfig

from .tokenization_baichuan import BaichuanTokenizer

from .airllm_base import AirLLMBaseModel



class AirLLMBaichuan(AirLLMBaseModel):


    def __init__(self, *args, **kwargs):


        super(AirLLMBaichuan, self).__init__(*args, **kwargs)

    def get_use_better_transformer(self):
        return False
    def get_tokenizer(self, hf_token=None):
        # Baichuan's custom tokenizer genuinely requires remote code, so in auto mode the config
        # load in __init__ already resolved self.trust_remote_code=True. Reuse it so an explicit
        # trust_remote_code=False from the caller is still honored (it will then fail to load,
        # which is the caller's choice) instead of silently overriding it.
        # https://github.com/baichuan-inc/Baichuan2-7B-Base/discussions/2
        return BaichuanTokenizer.from_pretrained(
            self.model_local_path, use_fast=False, trust_remote_code=self.trust_remote_code is not False)

    def get_generation_config(self):
        return GenerationConfig()


