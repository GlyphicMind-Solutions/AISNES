# /AISNES/src/controllers/llm_controller.py
# Generic LLM controller for AISNES
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import yaml
from pathlib import Path
from typing import Any, Dict, Optional



# ========================
# LLM CONTROLLER CLASS
# ========================
class LLMController:
    """
    LLMController
    -------------
    Thin wrapper around a local LLM engine.

    Responsibilities:
      - Load model configuration from src/models/manifest.yaml
      - Initialize a text or vision model (via a provided engine)
      - Expose simple generation methods:
          - generate_raw_llama(prompt, ...)
          - generate_multimodal(prompt, image_bytes, ...)
    """

    # -------------
    # Initialize
    # -------------
    def __init__(
        self,
        models_dir: Path,
        engine: Any,
        *,
        use_text_model: bool = True,
        use_vision_model: bool = False,
        text_model_key: Optional[str] = None,
        vision_model_key: Optional[str] = None,
        log=print,
    ):
        """
        models_dir: Path to src/models/
        engine:    An object that provides:
                     - generate_raw_llama(prompt=..., model_name=..., ...)
                     - generate_multimodal(prompt=..., image=..., model_name=..., ...)
        """
        # Model Pathing/Engine/Log
        self.models_dir = Path(models_dir)
        self.engine = engine
        self.log = log

        # manifest loader
        self.manifest = self._load_manifest()

        # load text model from manifest
        self.text_model_key = (
            text_model_key
            or self.manifest.get("default_text_model")
        )
        # load vision model from manifest 
        self.vision_model_key = (
            vision_model_key
            or self.manifest.get("default_vision_model")
        )

        # Resolve model names/paths
        self.text_model_name = None
        self.vision_model_name = None

        if use_text_model and self.text_model_key:
            self.text_model_name = self._resolve_model_name(self.text_model_key)

        if use_vision_model and self.vision_model_key:
            self.vision_model_name = self._resolve_model_name(self.vision_model_key)

        self.log(f"[LLMController] Loaded manifest from: {self.models_dir / 'manifest.yaml'}")
        self.log(f"[LLMController] Text model:   {self.text_model_name or 'None'}")
        self.log(f"[LLMController] Vision model: {self.vision_model_name or 'None'}")

    # ---------------------------------------------------------
    # Manifest loading
    # ---------------------------------------------------------
    def _load_manifest(self) -> Dict[str, Any]:
        """
        Load src/models/manifest.yaml.
        Returns an empty dict if missing or invalid.
        """
        manifest_path = self.models_dir / "manifest.yaml"
        if not manifest_path.exists():
            self.log(f"[LLMController] No manifest.yaml found at {manifest_path}")
            return {}

        try:
            data = yaml.safe_load(manifest_path.read_text())
            if not isinstance(data, dict):
                self.log("[LLMController] manifest.yaml is not a dict; ignoring.")
                return {}
            return data
        except Exception as e:
            self.log(f"[LLMController] Failed to load manifest.yaml: {e}")
            return {}

    # ---------------------------------------------------------
    # Resolve Model Name
    # ---------------------------------------------------------
    def _resolve_model_name(self, key: str) -> Optional[str]:
        """
        Given a logical model key (e.g. 'text_controller'),
        return the model path or name defined in manifest.yaml.
        """
        models = self.manifest.get("models", {})
        cfg = models.get(key)
        if not isinstance(cfg, dict):
            self.log(f"[LLMController] No model config for key: {key}")
            return None

        path = cfg.get("path")
        if not path:
            self.log(f"[LLMController] Model config for '{key}' missing 'path'.")
            return None

        # For local engines, we typically pass the path as model_name.
        return str(self.models_dir / path)

    # ---------------------------------------------------------
    # Text generation
    # ---------------------------------------------------------
    def generate_raw_llama(
        self,
        prompt: str,
        *,
        max_tokens: int = 128,
        temperature: float = 0.0,
        top_p: float = 1.0,
        repeat_penalty: float = 1.0,
        model_name: Optional[str] = None,
    ) -> str:
        """
        Call the underlying engine's text generation method.
        """
        model = model_name or self.text_model_name
        if not model:
            self.log("[LLMController] No text model configured.")
            return ""

        try:
            return self.engine.generate_raw_llama(
                prompt=prompt,
                model_name=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                repeat_penalty=repeat_penalty,
            )
        except Exception as e:
            self.log(f"[LLMController] Text generation error: {e}")
            return ""

    # ---------------------------------------------------------
    # Multimodal generation
    # ---------------------------------------------------------
    def generate_multimodal(
        self,
        prompt: str,
        image_bytes: bytes,
        *,
        max_tokens: int = 128,
        model_name: Optional[str] = None,
    ) -> str:
        """
        Call the underlying engine's multimodal generation method.
        """
        model = model_name or self.vision_model_name
        if not model:
            self.log("[LLMController] No vision model configured.")
            return ""

        try:
            return self.engine.generate_multimodal(
                prompt=prompt,
                image=image_bytes,
                model_name=model,
                max_tokens=max_tokens,
            )
        except Exception as e:
            self.log(f"[LLMController] Multimodal generation error: {e}")
            return ""

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------
    def describe_models(self) -> Dict[str, Any]:
        """
        Return a simple description of available models from manifest.yaml.
        Useful for debugging or UI display.
        """
        models = self.manifest.get("models", {})
        out = {}
        for key, cfg in models.items():
            if not isinstance(cfg, dict):
                continue
            out[key] = {
                "path": cfg.get("path", ""),
                "type": cfg.get("type", "unknown"),
                "description": cfg.get("description", ""),
            }
        return out

