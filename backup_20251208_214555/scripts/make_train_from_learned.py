#!/usr/bin/env python3
"""Convert artifacts/learned_facts.jsonl -> infra/adaptive/train_input.jsonl

Default filter: score >= 0.75
"""
import json
import os
import subprocess
import time
from pathlib import Path

try:
    from Self_Improvement.meta_logger import MetaLogger
except Exception:
    MetaLogger = None

ROOT = Path(os.getcwd())
LEARNED = ROOT / 'artifacts' / 'learned_facts.jsonl'
OUT_DIR = Path(os.getcwd()).parents[0] / '1762911536282' / 'infra' / 'adaptive'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'train_input.jsonl'

MIN_SCORE = float(os.getenv('AGL_TRAIN_MIN_SCORE', '0.75'))


def read_learned(path):
    if not path.exists():
        return []
    rows = []
    with path.open('r', encoding='utf-8') as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            rows.append(obj)
    return rows


def make_example(row):
    q = row.get('question') or row.get('title') or ''
    a = row.get('answer') or ''
    ts = row.get('ts')
    # include contextual metadata where present so training can condition on relations/media
    prompt = f"السؤال: {q}\n\n###\n\n"
    completion = f" {a}\n"
    meta = {"ts": ts, "score": row.get('score'), "source": row.get('source')}
    if 'context_relations' in row:
        meta['context_relations'] = row.get('context_relations')
    if 'hypothesis_variants' in row:
        meta['hypothesis_variants'] = row.get('hypothesis_variants')
    if 'media_ctx' in row:
        meta['media_ctx'] = row.get('media_ctx')
    return {"prompt": prompt, "completion": completion, "meta": meta}


def _write_train_input(kept_rows):
    with OUT.open('w', encoding='utf-8') as fh:
        for r in kept_rows:
            ex = make_example(r)
            fh.write(json.dumps(ex, ensure_ascii=False) + "\n")


def _attempt_lora_train(out_dir: Path, train_file: Path, model_name: str = "gpt2", kg_version: int = None) -> dict:
    """Try a minimal LoRA-style training if required libraries exist.

    If libraries are missing or training fails, create a placeholder adapter
    directory with metadata and return info dict.
    """
    info = {"out_dir": str(out_dir), "trained": False, "dry_run": True, "note": "no-train-attempted"}
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        import transformers
        from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
        try:
            from peft import LoraConfig, get_peft_model, prepare_model_for_int8_training
        except Exception:
            # PEFT not available; fallback to metadata-only write
            raise ImportError("peft not available")

        # Load small model and tokenizer (may be large; user env decides)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)

        # Minimal LoRA config
        lora_config = LoraConfig(
            r=8,
            lora_alpha=32,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.1,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_config)

        # Build tiny dataset from train_file
        examples = []
        with train_file.open('r', encoding='utf-8') as fh:
            for ln in fh:
                try:
                    j = json.loads(ln)
                except Exception:
                    continue
                prompt = j.get('prompt', '')
                completion = j.get('completion', '')
                text = (prompt + completion).strip()
                if text:
                    examples.append(text)
        if not examples:
            info['note'] = 'no-examples'
            return info

        # Tokenize dataset
        tok = tokenizer(examples, truncation=True, padding=True, return_tensors='pt')

        # Create a minimal trainer (no real training tuning)
        train_args = TrainingArguments(
            output_dir=str(out_dir),
            num_train_epochs=1,
            per_device_train_batch_size=1,
            logging_steps=10,
            save_strategy='no',
        )

        import torch

        class SimpleDataset(torch.utils.data.Dataset):
            def __init__(self, enc):
                self.enc = enc
            def __len__(self):
                return len(self.enc['input_ids'])
            def __getitem__(self, idx):
                return {k: v[idx] for k,v in self.enc.items()}

        ds = SimpleDataset(tok)
        trainer = Trainer(model=model, args=train_args, train_dataset=ds)
        trainer.train()
        # Save peft adapter
        model.save_pretrained(str(out_dir))
        info.update({"trained": True, "dry_run": False, "note": "trained_ok"})
        return info
    except Exception as e:
        # Write metadata file so callers can see a placeholder adapter
        meta = {"ts": time.time(), "error": repr(e)}
        if kg_version is not None:
            meta['kg_version'] = int(kg_version)
        with (out_dir / 'adapter_info.json').open('w', encoding='utf-8') as fh:
            json.dump(meta, fh, ensure_ascii=False)
        info['note'] = f"train-failed: {e!r}"
        if kg_version is not None:
            info['kg_version'] = int(kg_version)
        return info


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--min-score', type=float, default=MIN_SCORE)
    p.add_argument('--train', action='store_true', help='Attempt LoRA training on the produced train set')
    p.add_argument('--adapter-out', type=str, default=None, help='Directory to write adapter (overrides default)')
    p.add_argument('--model', type=str, default=os.getenv('AGL_BASE_MODEL', 'gpt2'))
    p.add_argument('--kg-version', type=int, default=None, help='Optional knowledge-graph version to record in adapter metadata')
    args = p.parse_args()

    rows = read_learned(LEARNED)
    kept = [r for r in rows if (r.get('score') is not None and float(r.get('score', 0.0)) >= float(args.min_score))]
    _write_train_input(kept)
    print(f"Wrote {len(kept)} examples to {OUT}")

    if args.train:
        # Determine adapter output path
        ts = int(time.time())
        default_adapter_dir = Path(os.getcwd()) / 'artifacts' / 'adapters' / str(ts)
        adapter_out = Path(args.adapter_out) if args.adapter_out else default_adapter_dir
        adapter_out = Path(adapter_out)
        adapter_out.mkdir(parents=True, exist_ok=True)

        print(f"Starting training attempt; adapter_out={adapter_out}")
        info = _attempt_lora_train(adapter_out, OUT, model_name=args.model, kg_version=args.kg_version)
        print(f"Training info: {info}")

        # Log via MetaLogger if available
        try:
            if MetaLogger is not None:
                class _S: pass
                s = _S()
                s.question = 'lora_training'
                s.engine_calls = []
                meta = MetaLogger.start_session(s)
                meta.update({"training_info": info, "adapter_out": str(adapter_out), "kg_version": args.kg_version})
                MetaLogger.finish_session(meta, s)
        except Exception:
            pass


if __name__ == '__main__':
    main()
