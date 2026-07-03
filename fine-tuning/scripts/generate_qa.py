import os
import re
import json
import glob
import time
import argparse
import types
from tqdm import tqdm

import torch
from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)

def print_device_info():
    print(f"  PyTorch version: {torch.__version__}")
    if torch.cuda.is_available():
        print(f"  Device: GPU ({torch.cuda.get_device_name(0)})")
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        print(f"  BF16 supported: {torch.cuda.is_bf16_supported()}")
    else:
        print(f"  Device: CPU")
        print("  [WARNING] Running on CPU — generation will be very slow!")


QA_GENERATION_PROMPT = """你是一个文档分析专家。请基于以下文档内容，生成3个高质量的中文问答对。

要求：
1. 问题必须能直接从文档中找到答案
2. 答案要准确、完整，严格基于原文，不要编造
3. 问题和答案都用中文
4. 每个问答对应覆盖文档中不同的知识点

文档内容：
{chunk}

请严格按以下格式输出（不要添加额外内容）：

问：xxx
答：xxx

问：xxx
答：xxx

问：xxx
答：xxx"""


def load_documents(doc_dir: str) -> list[str]:
    texts = []
    for filepath in sorted(glob.glob(os.path.join(doc_dir, "**/*"), recursive=True)):
        if not os.path.isfile(filepath):
            continue
        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext in (".txt", ".md"):
                with open(filepath, "r", encoding="utf-8") as f:
                    texts.append(f.read())
            elif ext == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(filepath)
                text = "\n".join(page.extract_text() for page in reader.pages)
                if text.strip():
                    texts.append(text)
        except Exception as e:
            print(f"  [skip] {os.path.basename(filepath)}: {e}")
    return texts


def chunk_text(text: str, chunk_size_chars: int = 3000, overlap_chars: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size_chars, len(text))
        chunks.append(text[start:end])
        start += chunk_size_chars - overlap_chars
    return chunks


def parse_qa(text: str) -> list[dict]:
    pairs = []
    lines = text.strip().split("\n")
    current_q = None
    for line in lines:
        line = line.strip()
        if line.startswith("问：") or line.startswith("问:"):
            current_q = line[2:].strip()
        elif line.startswith("答：") or line.startswith("答:"):
            answer = line[2:].strip()
            if current_q and answer:
                pairs.append({"question": current_q, "answer": answer})
                current_q = None
    return pairs


def format_chat(question: str, answer: str, tokenizer) -> str:
    messages = [
        {"role": "system", "content": "你是一个知识渊博的助手，请根据所学知识回答用户的问题。"},
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", default=None,
                        help="Path to GLM-4-9B-Chat model directory")
    parser.add_argument("--doc_dir", default=None,
                        help="Path to documents directory")
    parser.add_argument("--output", default=None,
                        help="Output JSONL file path")
    parser.add_argument("--test", action="store_true",
                        help="Process only first 2 chunks to test")
    args = parser.parse_args()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = args.model_path or os.path.join(base, "glm-4-9b-chat")
    doc_dir = args.doc_dir or os.path.join(base, "documents")
    output_path = args.output or os.path.join(base, "data", "train.jsonl")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("=" * 60)
    print("Device info:")
    print_device_info()
    print()

    print("Step 1: Loading documents...")
    print(f"  Document directory: {doc_dir}")
    all_docs = load_documents(doc_dir)
    if not all_docs:
        print("  [ERROR] No documents found. Place .txt/.md/.pdf files in the documents/ folder.")
        return
    print(f"  Loaded {len(all_docs)} document(s), total {sum(len(d) for d in all_docs)} chars")

    print("\nStep 2: Chunking documents...")
    all_chunks = []
    for doc in all_docs:
        all_chunks.extend(chunk_text(doc))
    print(f"  Created {len(all_chunks)} chunks")

    if args.test:
        all_chunks = all_chunks[:2]
        print(f"  [TEST MODE] Using only 2 chunks")
        output_path = output_path.replace(".jsonl", "_test.jsonl")

    print("\nStep 3: Loading GLM-4-9B-Chat (4-bit)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    config.max_length = config.seq_length

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
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

    model.eval()
    print("  Model loaded successfully")

    print(f"\nStep 4: Generating Q&A pairs for each chunk...")
    print(f"  Output: {output_path}")
    all_records = []
    total_tokens_in = 0
    total_tokens_out = 0
    start_time = time.time()
    for i, chunk in enumerate(tqdm(all_chunks, desc="Generating")):
        if not chunk.strip():
            continue

        prompt = QA_GENERATION_PROMPT.format(chunk=chunk)
        messages = [{"role": "user", "content": prompt}]
        inputs = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_tensors="pt", return_dict=True
        )
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        chunk_start = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        chunk_time = time.time() - chunk_start

        generated = outputs[0][inputs["input_ids"].shape[1]:]
        response = tokenizer.decode(generated, skip_special_tokens=True)
        num_in = inputs["input_ids"].shape[1]
        num_out = generated.shape[0]
        total_tokens_in += num_in
        total_tokens_out += num_out

        tqdm.write(
            f"  Chunk {i + 1}/{len(all_chunks)}: "
            f"{num_in} in → {num_out} out tokens, "
            f"{chunk_time:.1f}s ({num_out / chunk_time:.1f} tok/s)"
        )

        pairs = parse_qa(response)
        for pair in pairs:
            text = format_chat(pair["question"], pair["answer"], tokenizer)
            all_records.append({
                "text": text,
                "question": pair["question"],
                "answer": pair["answer"],
            })
    total_time = time.time() - start_time
    print(f"\n  Total tokens: {total_tokens_in} in, {total_tokens_out} out")
    print(f"  Total time: {total_time:.1f}s ({total_tokens_out / total_time:.1f} tok/s)")
    print(f"  Generated {len(all_records)} Q&A pairs")

    print(f"\n  Generated {len(all_records)} Q&A pairs")

    with open(output_path, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nDone! Dataset saved to: {output_path}")

    if len(all_records) == 0:
        print("  [WARNING] No Q&A pairs were generated. Possible issues:")
        print("    - The model output format doesn't match the expected pattern")
        print("    - Documents may be too short or low quality")
        print("  Try running with --test to debug generation output.")


if __name__ == "__main__":
    main()
