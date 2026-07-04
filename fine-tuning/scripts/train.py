import os
import json
import argparse

import torch
from datasets import Dataset
from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model
from trl import SFTConfig, SFTTrainer


def print_device_info():
    print(f"  PyTorch version: {torch.__version__}")
    if torch.cuda.is_available():
        print(f"  Device: GPU ({torch.cuda.get_device_name(0)})")
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        print(f"  BF16 supported: {torch.cuda.is_bf16_supported()}")
    else:
        print(f"  Device: CPU")
        print("  [WARNING] Running on CPU — training will be extremely slow!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", default=None,
                        help="Path to base model (GLM-4-9B-Chat)")
    parser.add_argument("--data_path", default=None,
                        help="Path to training JSONL file")
    parser.add_argument("--output_dir", default=None,
                        help="Directory to save fine-tuned adapter")
    parser.add_argument("--test", action="store_true",
                        help="Train on only 10 samples to verify setup")
    args = parser.parse_args()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = args.model_path or os.path.join(base, "glm-4-9b-chat")
    data_path = args.data_path or os.path.join(base, "data", "train.jsonl")
    output_dir = args.output_dir or os.path.join(base, "output")

    print("=" * 60)
    print("Device info:")
    print_device_info()
    print()

    print("QLoRA Fine-tuning: GLM-4-9B-Chat")
    print(f"  Base model: {model_path}")
    print(f"  Training data: {data_path}")
    print(f"  Output: {output_dir}")

    if not os.path.exists(data_path):
        print(f"\n[ERROR] Training data not found at: {data_path}")
        print("  Run generate_qa.py first to create the dataset.")
        return

    print("\nStep 1: Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    print(f"  Vocab size: {tokenizer.vocab_size}, Pad token: {tokenizer.pad_token}")

    print("\nStep 2: Loading dataset...")
    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = [json.loads(line) for line in f if line.strip()]

    if args.test:
        raw_data = raw_data[:10]
        print(f"  [TEST MODE] Using only {len(raw_data)} samples")

    dataset = Dataset.from_list(raw_data)
    print(f"  Loaded {len(dataset)} training samples")

    print("\nStep 3: Loading model in 4-bit...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    config.max_length = config.seq_length

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        config=config,
        trust_remote_code=True,
        quantization_config=bnb_config,
        device_map="auto",
        dtype=torch.bfloat16,
    )
    model.config.use_cache = False
    model.lm_head = model.transformer.output_layer
    print("  Model loaded in 4-bit")

    print("\nStep 4: Configuring LoRA...")
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["query_key_value", "dense"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    all_params = sum(p.numel() for p in model.parameters())
    print(f"  Trainable params: {trainable_params:,} ({trainable_params / all_params:.2%} of {all_params:,})")

    print("\nStep 5: Setting up training...")
    training_args = SFTConfig(
        output_dir=output_dir,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        gradient_checkpointing=True,
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        remove_unused_columns=False,
        report_to="none",
        dataloader_num_workers=0,
        optim="adamw_8bit",
        gradient_checkpointing_kwargs={"use_reentrant": False},
        loss_type="nll",
        dataset_text_field="text",
        max_length=512,
        packing=True,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        args=training_args,
        train_dataset=dataset,
    )

    print("\nStep 6: Starting training...")
    print(f"  Batch size: 1, Gradient accumulation: 4 (effective batch: 4)")
    print(f"  Epochs: 3, Max seq length: {training_args.max_length}")
    print("=" * 60)
    trainer.train()

    print("\nStep 7: Saving model...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    with open(os.path.join(output_dir, "training_config.json"), "w") as f:
        json.dump({
            "base_model": model_path,
            "lora_r": 8,
            "lora_alpha": 16,
            "lora_target_modules": ["query_key_value", "dense"],
            "dataset": data_path,
            "num_train_samples": len(dataset),
        }, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Fine-tuned adapter saved to: {output_dir}")
    print(f"  Use inference.py to chat with the fine-tuned model.")


if __name__ == "__main__":
    main()
