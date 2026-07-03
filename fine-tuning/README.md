# Fine-tuning Plan for GLM-4-9B-Chat

Directory Structure
```
fine-tuning/
├── scripts/
│   ├── generate_qa.py       # reads documents → chunks → GLM-4 generates Q&A → saves JSONL
│   ├── train.py             # QLoRA fine-tuning script
│   └── inference.py         # chat with fine-tuned model
├── data/
│   └── (generated files)
├── documents/               # put your PDF/MD/txt files here
└── requirements.txt
```

| File | Key logic |
|------|-----------|
| generate_qa.py | Load documents → split into 1500-token chunks → prompt GLM-4-9B-Chat to generate 3-5 Q&A per chunk → save train.jsonl in GLM-4 chat format |
| train.py | Load 4-bit model → LoRA (r=8, q_proj+v_proj) → SFTTrainer with packing → save adapter |
| inference.py | Load base model + LoRA adapter → interactive chat |
| requirements.txt | torch, transformers, peft, trl, bitsandbytes, datasets, accelerate, pypdf, langchain-text-splitters |


Your action items before training:
1. Place your .md/.txt/.pdf files in fine-tuning/documents/
2. Run generate_qa.py → creates data/train.jsonl
3. Review & clean the Q&A dataset (critical for quality)
4. Run train.py → produces LoRA adapter weights


## Phases

Phase 1: Data Preparation (do this first ✓)

| Step |     What      |  Time |
|------|---------------|-------|
| 1.1  | Collect & clean documents — remove irrelevant sections, fix formatting, deduplicate | 1-3 days |
| 1.2  | Chunk documents — split into sections/chapters (1k-2k tokens each) | Half day |
| 1.3  | Generate Q&A pairs — this is the critical step. Use GLM-4 itself or GPT-4 to generate high-quality Q&A from each chunk. Format example: {"question": "...", "answer": "..."} | 2-5 days |
| 1.4  | Clean & review Q&A — remove low-quality pairs, check for hallucination | 1-2 days |
| 1.5  | Format dataset — convert to GLM-4 chat template format (multi-turn messages with system/user/assistant roles) | Half day |


Phase 2: Fine-tuning Setup

| Step |     What      |
|------|---------------|
| 2.1  | Choose method — LoRA/QLoRA recommended (you only have ~24GB VRAM with 9B model). QLoRA can run on 16-24GB GPU. |
| 2.2  | Write training script — use transformers + peft + trl.SFTTrainer |
| 2.3  | Split data — train/val/test (80/10/10) |

Phase 3: Training & Evaluation

| Step |     What      |
|------|---------------|
| 3.1  | Run training — LoRA rank=8-16, lr=2e-4, 3-5 epochs |
| 3.2  | Evaluate — hold-out test set, human review of outputs |
| 3.3  | Merge LoRA weights & export |


## Plan

With 8-12GB VRAM and a 9B model, the only viable path is QLoRA (4-bit quantization). The 4-bit model uses ~6-7GB VRAM, leaving room for adapters and optimizer states.

Final Plan: QLoRA Fine-tuning GLM-4-9B-Chat

| #	| File | Purpose |
|---|------|---------|
| 1 | fine-tuning/documents/ | Place your original docs here |
| 2 | fine-tuning/scripts/generate_qa.py | Reads docs → chunks → sends to GLM-4 (or API) to generate Q&A pairs |
| 3 | fine-tuning/data/train.jsonl | Generated dataset in GLM-4 chat format |
| 4 | fine-tuning/scripts/train.py | QLoRA training script using peft + bitsandbytes + trl.SFTTrainer |
| 5 | fine-tuning/scripts/inference.py | Load fine-tuned model and chat interactively |
| 6 | fine-tuning/requirements.txt | Dependencies (torch, transformers, peft, trl, bitsandbytes, datasets, accelerate) |

### Workflow
```
Documents (PDF/MD/txt)
    ↓ generate_qa.py (chunk + LLM + format)
train.jsonl (Q&A pairs in GLM chat format)
    ↓ train.py (QLoRA: 4-bit NF4 + LoRA rank=8)
Adapter weights (~50MB)
    ↓ inference.py
Domain Q&A Bot
```

### Key training config (for 8-12GB VRAM)

| Parameter | Value |
|-----------|-------|
| Quantization | 4-bit NF4 (bitsandbytes) |
| LoRA rank | 8-16 |
| LoRA target | q_proj, v_proj (or all linear) |
| Batch size | 1 (gradient accumulation=4) |
| Learning rate | 2e-4 |
| Precision | bf16 |

LoRA target modules:
- q_proj, v_proj - Standard, good quality-efficiency tradeoff. ~2-4GB adapter memory during training.