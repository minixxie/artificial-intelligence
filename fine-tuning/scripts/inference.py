import os
import sys
import argparse
import types

import torch
from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import PeftModel


def print_device_info():
    print(f"  PyTorch version: {torch.__version__}")
    if torch.cuda.is_available():
        print(f"  Device: GPU ({torch.cuda.get_device_name(0)})")
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print(f"  Device: CPU")
        print("  [WARNING] Running on CPU — responses will be very slow!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", default=None,
                        help="Path to base model (GLM-4-9B-Chat)")
    parser.add_argument("--adapter_path", default=None,
                        help="Path to fine-tuned LoRA adapter")
    parser.add_argument("--merge", action="store_true",
                        help="Merge LoRA weights into base model and save")
    parser.add_argument("--merge_output", default=None,
                        help="Output path for merged model (default: <adapter_path>_merged)")
    parser.add_argument("--quantize", default=None,
                        help="Quantize merged model: 4bit or 8bit")
    args = parser.parse_args()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = args.model_path or os.path.join(base, "glm-4-9b-chat")
    adapter_path = args.adapter_path or os.path.join(base, "output")

    if not os.path.exists(adapter_path) or not os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
        print(f"[ERROR] No LoRA adapter found at: {adapter_path}")
        print("  Run train.py first to fine-tune the model.")
        sys.exit(1)

    print("Device info:")
    print_device_info()
    print()

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    print("Loading base model (4-bit)...")
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

    original_forward = model.transformer.forward

    def patched_transformer_forward(self, input_ids, *args, past_key_values=None, **kwargs):
        if past_key_values is not None:
            try:
                if past_key_values[0][0] is None:
                    past_key_values = None
            except (IndexError, TypeError, KeyError):
                pass
        return original_forward(input_ids, *args, past_key_values=past_key_values, **kwargs)

    model.transformer.forward = types.MethodType(patched_transformer_forward, model.transformer)

    print("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(model, adapter_path)
    print("Fine-tuned model ready!")

    if args.merge:
        merge_output = args.merge_output or adapter_path.rstrip("/") + "_merged"
        print(f"\nMerging LoRA weights into base model (saving to {merge_output})...")
        merged = model.merge_and_unload()

        quantize_config = None
        if args.quantize == "4bit":
            quantize_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
        elif args.quantize == "8bit":
            quantize_config = BitsAndBytesConfig(load_in_8bit=True)

        merged.save_pretrained(merge_output, quantization_config=quantize_config)
        tokenizer.save_pretrained(merge_output)
        print(f"Merged model saved to: {merge_output}")
        return

    print("\n" + "=" * 60)
    print("Interactive Chat (type 'quit' to exit)")
    print("=" * 60)

    system_prompt = "你是一个知识渊博的助手，请根据所学知识回答用户的问题。"
    history = []

    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("quit", "exit", "q"):
            break

        messages = [{"role": "system", "content": system_prompt}]
        for h in history:
            messages.append({"role": "user", "content": h[0]})
            messages.append({"role": "assistant", "content": h[1]})
        messages.append({"role": "user", "content": user_input})

        inputs = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_tensors="pt", return_dict=True
        )
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated = outputs[0][inputs["input_ids"].shape[1]:]
        response = tokenizer.decode(generated, skip_special_tokens=True)

        print(f"\nAssistant: {response}")
        history.append((user_input, response))


if __name__ == "__main__":
    main()
