"""Use the uncensored Qwen Image 2.1 (qwen-image-2.1-UC-Q8_0.gguf, the model in the saved ComfyUI workflow
qwen_image_2_1_UC_t2i_gguf.json) in place of the regular int8 model. Import this before calling manga.job."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "ghost-comic" / "scripts"))
import comfy  # noqa: E402
import manga  # noqa: E402

GGUF = "qwen-image-2.1-UC-Q8_0.gguf"
_build = comfy.build_graph


def build_uc(*a, **k):
    g = _build(*a, **k)
    g["1"] = {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": GGUF}}
    g.pop("2", None)  # the int8 model's cache node; the saved UC workflow has none
    for node in g.values():
        for key, v in node["inputs"].items():
            if v == ["2", 0]:
                node["inputs"][key] = ["1", 0]
    return g


comfy.build_graph = build_uc
manga.comfy.build_graph = build_uc
