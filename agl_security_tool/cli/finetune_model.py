#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║  AGL Model Fine-Tuner — تدريب النموذج المتخصص                        ║
║  QLoRA fine-tuning on smart contract security data                   ║
╚══════════════════════════════════════════════════════════════════════╝

Fine-tunes a small LLM (qwen2.5:3b/7b) into a specialized smart contract
security analyzer using QLoRA (4-bit quantization + LoRA adapters).

Supports two modes:
  1. Unsloth (recommended) — 2x faster, lower VRAM
  2. Transformers + PEFT — standard HuggingFace approach

Hardware requirements:
  - QLoRA 3B: ~3.5 GB VRAM (fits RTX 2050 4GB)
  - QLoRA 7B: ~6 GB VRAM (needs RTX 3060+)

Usage:
    # Quick start with Unsloth (recommended)
    python -m agl_security_tool.cli.finetune_model \\
        --data artifacts/training_data.jsonl \\
        --base-model Qwen/Qwen2.5-3B-Instruct \\
        --output artifacts/agl-solidity-expert \\
        --epochs 3

    # Export to Ollama after training
    python -m agl_security_tool.cli.finetune_model --export-ollama \\
        --model-dir artifacts/agl-solidity-expert

    # Using standard transformers (fallback)
    python -m agl_security_tool.cli.finetune_model \\
        --data artifacts/training_data.jsonl \\
        --backend transformers \\
        --base-model Qwen/Qwen2.5-3B-Instruct
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import textwrap
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PKG_ROOT = os.path.dirname(_SCRIPT_DIR)

logger = logging.getLogger("agl.finetune")

# ═══════════════════════════════════════════════════════════════
# TRAINING DATA FORMATTER
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "You are AGL-SEC, an elite smart contract security auditor specialized in "
    "Solidity/EVM vulnerability detection, DeFi protocol analysis, symbolic reasoning, "
    "and exploit path construction. You understand the AGL Security Tool pipeline: "
    "Z3 symbolic engine, CFG analysis, state extraction, temporal analysis, action space, "
    "attack simulation, search engine, exploit reasoning, and Heikal Math scoring. "
    "Always respond with precise, structured JSON analysis."
)


def format_chat_template(sample: dict) -> dict:
    """Convert training pair to chat template format for Qwen2.5."""
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": sample["instruction"] + "\n\n" + sample.get("input", "")},
            {"role": "assistant", "content": sample["output"]},
        ]
    }


def load_training_data(data_path: str) -> list[dict]:
    """Load JSONL training data and format for fine-tuning."""
    samples = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sample = json.loads(line)
            formatted = format_chat_template(sample)
            samples.append(formatted)
    logger.info("Loaded %d training samples from %s", len(samples), data_path)
    return samples


# ═══════════════════════════════════════════════════════════════
# UNSLOTH TRAINING (RECOMMENDED — 2x faster, less VRAM)
# ═══════════════════════════════════════════════════════════════

def train_with_unsloth(
    data_path: str,
    base_model: str = "Qwen/Qwen2.5-3B-Instruct",
    output_dir: str = "artifacts/agl-solidity-expert",
    epochs: int = 3,
    batch_size: int = 2,
    grad_accum: int = 4,
    lr: float = 2e-4,
    lora_r: int = 16,
    lora_alpha: int = 32,
    max_seq_length: int = 4096,
) -> str:
    """Fine-tune using Unsloth (fastest method)."""
    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
    except ImportError:
        logger.error(
            "Unsloth not installed. Install with:\n"
            "  pip install unsloth\n"
            "  pip install trl transformers datasets"
        )
        raise

    logger.info("Loading base model: %s (4-bit quantized)", base_model)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )

    # Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=0.05,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    # Load and format data
    samples = load_training_data(data_path)

    # Format for Qwen2.5 chat template
    def formatting_func(examples):
        texts = []
        for msgs in examples["messages"]:
            text = tokenizer.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=False,
            )
            texts.append(text)
        return {"text": texts}

    from datasets import Dataset
    dataset = Dataset.from_list(samples)
    dataset = dataset.map(formatting_func, batched=True)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        num_train_epochs=epochs,
        learning_rate=lr,
        fp16=True,
        logging_steps=10,
        save_strategy="epoch",
        warmup_ratio=0.05,
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
    )

    logger.info("Starting training: %d samples, %d epochs", len(samples), epochs)
    trainer.train()

    # Save
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    logger.info("Model saved to %s", output_dir)

    return output_dir


# ═══════════════════════════════════════════════════════════════
# TRANSFORMERS + PEFT TRAINING (FALLBACK)
# ═══════════════════════════════════════════════════════════════

def train_with_transformers(
    data_path: str,
    base_model: str = "Qwen/Qwen2.5-3B-Instruct",
    output_dir: str = "artifacts/agl-solidity-expert",
    epochs: int = 3,
    batch_size: int = 1,
    grad_accum: int = 8,
    lr: float = 2e-4,
    lora_r: int = 16,
    lora_alpha: int = 32,
    max_seq_length: int = 2048,
    max_samples: int = 0,
) -> str:
    """Fine-tune using transformers + PEFT (LoRA).
    
    Supports two modes:
      - QLoRA 4-bit (if bitsandbytes is available) — lowest VRAM
      - Float16 + CPU offloading (fallback) — works on any GPU
    """
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
    )
    from peft import LoraConfig, get_peft_model
    from trl import SFTTrainer, SFTConfig
    from datasets import Dataset

    # ── Detect bitsandbytes for QLoRA ─────────
    use_qlora = False
    try:
        from transformers import BitsAndBytesConfig
        from peft import prepare_model_for_kbit_training
        import bitsandbytes  # noqa: F401
        use_qlora = True
        logger.info("bitsandbytes found → using QLoRA 4-bit")
    except ImportError:
        logger.info("bitsandbytes not available → using float16 + LoRA + CPU offloading")

    # ── Auto-detect GPU memory and adjust settings ─────
    if torch.cuda.is_available():
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info("GPU: %s | VRAM: %.1f GB", torch.cuda.get_device_name(0), vram_gb)
        if vram_gb < 5 and not use_qlora:
            logger.info("Low VRAM detected — using batch_size=1, max_seq=512, CPU offload")
            batch_size = 1
            max_seq_length = min(max_seq_length, 512)
    else:
        logger.info("No GPU detected — training on CPU (will be slow)")

    # ── Load tokenizer ─────────
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ── Load model ─────────
    if use_qlora:
        logger.info("Loading base model: %s (QLoRA 4-bit)", base_model)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model)
    else:
        logger.info("Loading base model: %s (float16 on CPU → GPU train)", base_model)
        # Load on CPU first (model is bigger than VRAM)
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()

    # ── LoRA config ─────────
    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=0.05,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ── Load data ─────────
    samples = load_training_data(data_path)
    if max_samples > 0 and len(samples) > max_samples:
        logger.info("Limiting dataset: %d → %d samples (--max-samples)", len(samples), max_samples)
        samples = samples[:max_samples]

    def formatting_func(examples):
        texts = []
        for msgs in examples["messages"]:
            text = tokenizer.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=False,
            )
            texts.append(text)
        return {"text": texts}

    dataset = Dataset.from_list(samples)
    dataset = dataset.map(formatting_func, batched=True)

    # ── Training args ─────────
    # Determine fp16/bf16 based on where model actually is
    model_on_gpu = use_qlora  # QLoRA puts model on GPU
    train_on_cpu = not use_qlora  # CPU training when model doesn't fit in VRAM
    training_args = SFTConfig(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        num_train_epochs=epochs,
        learning_rate=lr,
        fp16=model_on_gpu,  # Only use fp16 if model is on GPU
        bf16=False,
        use_cpu=train_on_cpu,  # Force CPU training (model 6GB > VRAM 4GB)
        logging_steps=25,
        save_strategy="epoch",
        warmup_ratio=0.05,
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
        gradient_checkpointing=not use_qlora,
        dataloader_pin_memory=False,
        max_grad_norm=1.0,
        max_length=max_seq_length,
        dataset_text_field="text",
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=training_args,
    )

    logger.info("Starting training: %d samples, %d epochs, batch=%d, grad_accum=%d",
                len(samples), epochs, batch_size, grad_accum)
    logger.info("Effective batch size: %d", batch_size * grad_accum)
    trainer.train()

    # Save LoRA adapters + tokenizer
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    logger.info("Model saved to %s", output_dir)

    return output_dir


# ═══════════════════════════════════════════════════════════════
# GGUF EXPORT + OLLAMA IMPORT
# ═══════════════════════════════════════════════════════════════

def merge_lora_and_save(model_dir: str, base_model: str = None) -> str:
    """Merge LoRA adapters back into base model and save full model."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel, PeftConfig

    merged_dir = os.path.join(model_dir, "merged")
    os.makedirs(merged_dir, exist_ok=True)

    # Detect base model from adapter config
    if base_model is None:
        peft_config = PeftConfig.from_pretrained(model_dir)
        base_model = peft_config.base_model_name_or_path
        logger.info("Detected base model: %s", base_model)

    logger.info("Loading base model for merge...")
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        device_map="cpu",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_dir)

    logger.info("Loading LoRA adapters...")
    model = PeftModel.from_pretrained(base, model_dir)

    logger.info("Merging LoRA into base model...")
    model = model.merge_and_unload()

    model.save_pretrained(merged_dir)
    tokenizer.save_pretrained(merged_dir)
    logger.info("Merged model saved to %s", merged_dir)
    return merged_dir


def export_to_gguf(model_dir: str, quantization: str = "q4_k_m") -> str:
    """Convert fine-tuned model to GGUF format for Ollama."""
    gguf_path = os.path.join(model_dir, f"agl-solidity-expert-{quantization}.gguf")

    # If model_dir has LoRA adapters (not full model), merge first
    adapter_config = os.path.join(model_dir, "adapter_config.json")
    if os.path.exists(adapter_config):
        logger.info("LoRA adapters detected — merging into base model first...")
        model_dir = merge_lora_and_save(model_dir)
        gguf_path = os.path.join(model_dir, f"agl-solidity-expert-{quantization}.gguf")

    # Method 1: Unsloth native export
    try:
        from unsloth import FastLanguageModel
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_dir,
            max_seq_length=4096,
            load_in_4bit=True,
        )
        model.save_pretrained_gguf(
            model_dir,
            tokenizer,
            quantization_method=quantization,
        )
        logger.info("GGUF exported via Unsloth: %s", gguf_path)
        return gguf_path
    except (ImportError, Exception) as e:
        logger.info("Unsloth export failed (%s), trying llama.cpp...", e)

    # Method 2: llama.cpp convert
    convert_script = os.path.join(
        os.path.expanduser("~"), "llama.cpp", "convert_hf_to_gguf.py"
    )
    if os.path.exists(convert_script):
        subprocess.run(
            [sys.executable, convert_script, model_dir, "--outfile", gguf_path,
             "--outtype", quantization],
            check=True,
        )
        logger.info("GGUF exported via llama.cpp: %s", gguf_path)
        return gguf_path

    # Method 3: Try transformers built-in GGUF export
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        logger.info("Attempting HF → safetensors (Ollama can import directly)...")
        safetensors_path = os.path.join(model_dir, "model.safetensors")
        if os.path.exists(safetensors_path):
            logger.info("Safetensors model ready at: %s", model_dir)
            return model_dir  # Ollama can create from safetensors dir
    except Exception:
        pass

    logger.error(
        "Cannot export to GGUF. Options:\n"
        "  1. pip install unsloth\n"
        "  2. git clone https://github.com/ggerganov/llama.cpp\n"
        "  3. Use ollama create with safetensors directly"
    )
    raise RuntimeError("No GGUF export method available")


def import_to_ollama(gguf_path: str, model_name: str = "agl-solidity-expert") -> bool:
    """Create Ollama model from GGUF file."""
    modelfile_path = os.path.join(os.path.dirname(gguf_path), "Modelfile")

    modelfile_content = textwrap.dedent(f"""\
        FROM {gguf_path}

        PARAMETER temperature 0.3
        PARAMETER top_p 0.9
        PARAMETER repeat_penalty 1.1
        PARAMETER num_ctx 4096

        SYSTEM \"\"\"You are AGL-SEC, an elite smart contract security auditor specialized in \
Solidity/EVM vulnerability detection, DeFi protocol analysis, symbolic reasoning, \
and exploit path construction. You understand the AGL Security Tool pipeline: \
Z3 symbolic engine, CFG analysis, state extraction, temporal analysis, action space, \
attack simulation, search engine, exploit reasoning, and Heikal Math scoring. \
Always respond with precise, structured JSON analysis.\"\"\"
    """)

    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)

    logger.info("Creating Ollama model: %s", model_name)
    result = subprocess.run(
        ["ollama", "create", model_name, "-f", modelfile_path],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        logger.info("Ollama model created: %s", model_name)
        return True
    else:
        logger.error("Ollama import failed: %s", result.stderr)
        return False


# ═══════════════════════════════════════════════════════════════
# DEPENDENCY INSTALLER
# ═══════════════════════════════════════════════════════════════

def install_dependencies(backend: str = "unsloth") -> bool:
    """Install required packages for fine-tuning."""
    packages = {
        "unsloth": [
            "unsloth",
            "trl",
            "transformers",
            "datasets",
            "accelerate",
        ],
        "transformers": [
            "torch",
            "transformers",
            "peft",
            "trl",
            "datasets",
            "bitsandbytes",
            "accelerate",
        ],
    }

    pkgs = packages.get(backend, packages["transformers"])
    logger.info("Installing packages: %s", ", ".join(pkgs))

    for pkg in pkgs:
        try:
            __import__(pkg.replace("-", "_"))
            logger.info("  ✓ %s already installed", pkg)
        except ImportError:
            logger.info("  ↓ Installing %s...", pkg)
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                capture_output=True,
            )

    return True


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="AGL Model Fine-Tuner — تدريب النموذج المتخصص",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # ── Train command ─────────────────────────
    train_parser = subparsers.add_parser("train", help="Fine-tune the model")
    train_parser.add_argument(
        "--data",
        default=os.path.join(_PKG_ROOT, "artifacts", "training_master.jsonl"),
        help="Training data JSONL path",
    )
    train_parser.add_argument(
        "--base-model",
        default="Qwen/Qwen2.5-3B-Instruct",
        help="HuggingFace base model name",
    )
    train_parser.add_argument(
        "--output",
        default=os.path.join(_PKG_ROOT, "artifacts", "agl-solidity-expert"),
        help="Output directory for fine-tuned model",
    )
    train_parser.add_argument(
        "--backend",
        choices=["unsloth", "transformers"],
        default="transformers",
        help="Training backend (transformers is default)",
    )
    train_parser.add_argument("--epochs", type=int, default=3)
    train_parser.add_argument("--batch-size", type=int, default=1)
    train_parser.add_argument("--grad-accum", type=int, default=8)
    train_parser.add_argument("--lr", type=float, default=2e-4)
    train_parser.add_argument("--lora-r", type=int, default=16)
    train_parser.add_argument("--lora-alpha", type=int, default=32)
    train_parser.add_argument("--max-seq-length", type=int, default=2048)
    train_parser.add_argument("--max-samples", type=int, default=0, help="Limit training samples (0=all)")

    # ── Export command ────────────────────────
    export_parser = subparsers.add_parser("export", help="Export to GGUF + Ollama")
    export_parser.add_argument(
        "--model-dir",
        default=os.path.join(_PKG_ROOT, "artifacts", "agl-solidity-expert"),
        help="Fine-tuned model directory",
    )
    export_parser.add_argument(
        "--quantization",
        default="q4_k_m",
        choices=["q4_0", "q4_k_m", "q5_k_m", "q8_0", "f16"],
        help="GGUF quantization type",
    )
    export_parser.add_argument(
        "--ollama-name",
        default="agl-solidity-expert",
        help="Name for the Ollama model",
    )

    # ── Install command ───────────────────────
    install_parser = subparsers.add_parser("install", help="Install dependencies")
    install_parser.add_argument(
        "--backend",
        choices=["unsloth", "transformers"],
        default="unsloth",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    if args.command == "train":
        train_fn = (
            train_with_unsloth if args.backend == "unsloth"
            else train_with_transformers
        )
        output = train_fn(
            data_path=args.data,
            base_model=args.base_model,
            output_dir=args.output,
            epochs=args.epochs,
            batch_size=args.batch_size,
            grad_accum=args.grad_accum,
            lr=args.lr,
            lora_r=args.lora_r,
            lora_alpha=args.lora_alpha,
            max_seq_length=args.max_seq_length,
            max_samples=args.max_samples,
        )
        print(f"\n✓ Model fine-tuned successfully → {output}")
        print(f"  Next: python -m agl_security_tool.cli.finetune_model export --model-dir {output}")

    elif args.command == "export":
        gguf_path = export_to_gguf(args.model_dir, args.quantization)
        success = import_to_ollama(gguf_path, args.ollama_name)
        if success:
            print(f"\n✓ Model available in Ollama as: {args.ollama_name}")
            print(f"  Test: ollama run {args.ollama_name}")
            print(f"  Use in AGL: set AGL_LLM_MODEL={args.ollama_name}")

    elif args.command == "install":
        install_dependencies(args.backend)
        print("\n✓ Dependencies installed")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
