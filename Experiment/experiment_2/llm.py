
from haystack.nodes import PromptModel
from llmlayer import LlamaCPPInvocationLayer
import box
import yaml

with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))


def setup_llm():
    return PromptModel(
        model_name_or_path=cfg.MODEL_BIN_PATH,
        invocation_layer_class=LlamaCPPInvocationLayer,
        use_gpu=cfg.USE_GPU,
        max_length=cfg.MODEL_MAX_TOKEN_LIMIT
    )
