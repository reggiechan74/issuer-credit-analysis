#!/usr/bin/env python3
"""
Configuration Loader for Extraction Pipeline
Loads and validates extraction_config.yaml
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ExtractionConfig:
    """Configuration manager for extraction pipeline"""

    # Define presets
    PRESETS = {
        "fastest": {
            "phase1_extraction": {"method": "claude_code", "save_markdown": False},
            "phase2_extraction": {"method": "pdf_to_json", "prompt_strategy": "reference"}
        },
        "standard": {
            "phase1_extraction": {"method": "claude_code", "save_markdown": True},
            "phase2_extraction": {"method": "markdown_to_json", "prompt_strategy": "reference"}
        },
        "legacy": {
            "phase1_extraction": {"method": "markitdown", "save_markdown": True},
            "phase2_extraction": {"method": "markdown_to_json", "prompt_strategy": "embedded"}
        },
        "markdown_first": {
            "phase1_extraction": {"method": "markitdown", "save_markdown": True},
            "phase2_extraction": {"method": "markdown_to_json", "prompt_strategy": "reference"}
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader

        Args:
            config_path: Path to config file (default: config/extraction_config.yaml)
        """
        if config_path is None:
            # Default to config/extraction_config.yaml
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            config_path = project_root / "config" / "extraction_config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._apply_preset_if_defined()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def _apply_preset_if_defined(self):
        """Apply preset configuration if specified"""
        preset_name = self.config.get("preset")

        if preset_name:
            if preset_name not in self.PRESETS:
                raise ValueError(f"Unknown preset: {preset_name}. Valid presets: {list(self.PRESETS.keys())}")

            print(f"📦 Applying preset: '{preset_name}'")
            preset = self.PRESETS[preset_name]

            # Merge preset into config
            for section, values in preset.items():
                if section in self.config:
                    self.config[section].update(values)
                else:
                    self.config[section] = values

    def _validate_config(self):
        """Validate configuration values"""
        # Validate Phase 1 method
        phase1_method = self.get_phase1_method()
        if phase1_method not in ["claude_code", "markitdown"]:
            raise ValueError(f"Invalid phase1_extraction.method: {phase1_method}")

        # Validate Phase 2 method
        phase2_method = self.get_phase2_method()
        if phase2_method not in ["markdown_to_json", "pdf_to_json"]:
            raise ValueError(f"Invalid phase2_extraction.method: {phase2_method}")

        # Validate combination: pdf_to_json requires claude_code for Phase 1
        if phase2_method == "pdf_to_json" and phase1_method != "claude_code":
            raise ValueError(
                "phase2_extraction.method='pdf_to_json' requires "
                "phase1_extraction.method='claude_code'"
            )

        # Validate prompt strategy
        prompt_strategy = self.get_prompt_strategy()
        if prompt_strategy not in ["reference", "embedded"]:
            raise ValueError(f"Invalid phase2_extraction.prompt_strategy: {prompt_strategy}")

    # Getter methods
    def get_phase1_method(self) -> str:
        """Get Phase 1 extraction method"""
        return self.config.get("phase1_extraction", {}).get("method", "claude_code")

    def get_phase2_method(self) -> str:
        """Get Phase 2 extraction method"""
        return self.config.get("phase2_extraction", {}).get("method", "markdown_to_json")

    def get_prompt_strategy(self) -> str:
        """Get Phase 2 prompt strategy"""
        return self.config.get("phase2_extraction", {}).get("prompt_strategy", "reference")

    def get_markdown_output_dir(self) -> str:
        """Get markdown output directory"""
        return self.config.get("phase1_extraction", {}).get("markdown_output_dir", "temp/phase1_markdown")

    def get_json_output_dir(self) -> str:
        """Get JSON output directory"""
        return self.config.get("phase2_extraction", {}).get("json_output_dir", "temp")

    def should_save_markdown(self) -> bool:
        """Check if markdown should be saved"""
        return self.config.get("phase1_extraction", {}).get("save_markdown", False)

    def should_validate_schema(self) -> bool:
        """Check if schema validation is enabled"""
        return self.config.get("phase2_extraction", {}).get("validate_schema", True)

    def is_verbose(self) -> bool:
        """Check if verbose logging is enabled"""
        return self.config.get("general", {}).get("verbose", False)

    def should_keep_temp_files(self) -> bool:
        """Check if temporary files should be kept"""
        return self.config.get("general", {}).get("keep_temp_files", True)

    def should_estimate_tokens(self) -> bool:
        """Check if token estimation is enabled"""
        return self.config.get("performance", {}).get("estimate_tokens", True)

    def get_max_pdf_size_mb(self) -> int:
        """Get maximum PDF size for direct reading"""
        return self.config.get("performance", {}).get("max_pdf_size_mb", 10)

    def get_default_currency(self) -> str:
        """Get default currency"""
        return self.config.get("general", {}).get("default_currency", "CAD")

    def print_active_config(self):
        """Print active configuration summary"""
        print("\n" + "="*70)
        print("📋 ACTIVE EXTRACTION CONFIGURATION")
        print("="*70)
        print(f"Phase 1 Method:      {self.get_phase1_method()}")
        print(f"Phase 2 Method:      {self.get_phase2_method()}")
        print(f"Prompt Strategy:     {self.get_prompt_strategy()}")
        print(f"Save Markdown:       {self.should_save_markdown()}")
        print(f"Validate Schema:     {self.should_validate_schema()}")
        print(f"Default Currency:    {self.get_default_currency()}")
        print(f"Verbose Logging:     {self.is_verbose()}")
        print("="*70 + "\n")


def load_config(config_path: Optional[str] = None) -> ExtractionConfig:
    """
    Load extraction configuration

    Args:
        config_path: Optional path to config file

    Returns:
        ExtractionConfig instance
    """
    return ExtractionConfig(config_path)


if __name__ == "__main__":
    # Test configuration loader
    try:
        config = load_config()
        config.print_active_config()
        print("✅ Configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        exit(1)
