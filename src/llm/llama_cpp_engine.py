# /AISNES/src/llm/llama_cpp_engine.py
# Llama-cpp backend for AI-SNES
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
from llama_cpp import Llama



# =====================================
# LLAMA-CPP ENGINE CLASS
# =====================================
class LlamaCppEngine:
    # ------------
    # Initialize
    # ------------
    def __init__(self, model_path: str, n_ctx: int = 4096, n_threads: int = 8):
        self.model_path = model_path
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=False,
        )

    # --------------------
    # Generate Raw Llama
    # --------------------
    def generate_raw_llama(
        self,
        prompt: str,
        model_name: str = None,
        max_tokens: int = 128,
        temperature: float = 0.7,
        top_p: float = 1.0,
        repeat_penalty: float = 1.0,
    ):
        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
        )
        return output["choices"][0]["text"]

    # --------------------
    # Generate Multimodal
    # --------------------
    def generate_multimodal(self, *args, **kwargs):
        # Placeholder until you add a vision model
        return "[Vision model not implemented]"

