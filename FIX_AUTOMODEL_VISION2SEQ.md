# Fix AutoModelForVision2Seq Import Issue

## Problem
The Kaggle notebook fails at startup with:
```
ImportError: cannot import name 'AutoModelForVision2Seq' from 'transformers'
```

This happens because the Garment-GPT model uses LLaVA architecture (LlavaForConditionalGeneration), not AutoModelForVision2Seq. The transformers library version on Kaggle doesn't have AutoModelForVision2Seq available.

## Locations to Fix
Two locations in `/Users/mac/ai-body-scan-saas/kaggle-garment-backend/notebook.ipynb`:

1. **Cell 8** (index 8) - The `code = r'''` block that gets written to `api_server.py`
2. **Cell 10** (index 10) - The execution block that runs the server

Both contain the same problematic code pattern:
```python
if hasattr(cfg, 'vision_config'):
    from transformers import AutoModelForVision2Seq
    model_class = AutoModelForVision2Seq
else:
    from transformers import AutoModelForCausalLM
    model_class = AutoModelForCausalLM
```

## Fix
Replace with try/except fallback to LlavaForConditionalGeneration:

```python
if hasattr(cfg, 'vision_config'):
    try:
        from transformers import AutoModelForVision2Seq
        model_class = AutoModelForVision2Seq
    except ImportError:
        from transformers import LlavaForConditionalGeneration
        model_class = LlavaForConditionalGeneration
else:
    from transformers import AutoModelForCausalLM
    model_class = AutoModelForCausalLM
```

## Steps
1. Edit notebook.ipynb - find Cell 8 (the `code = r'''` block) and Cell 10 (execution block)
2. Replace the vision_config block in both locations with the try/except version
3. Save the notebook
4. Upload to Kaggle and restart GPU session

## Verification
After fix, the server should:
- Load the LLaVA-7B model via LlavaForConditionalGeneration
- Print "[vllm-shim] Model loaded on cuda:0 with int8"
- Pass health check with garmentgpt: true