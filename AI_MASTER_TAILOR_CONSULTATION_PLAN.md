# KORRA: AI Master Tailor Consultation Roadmap
**Objective**: Transform the existing VLM (Vision-Language Model) and VQ-VAE (Geometric DNA) checkpoints into a conversational "Ask AI" interface that provides expert sewing guidance, assembly logic, and fabric intelligence based on specific 3D meshes and images.

---

## Technical Concept: "The Geometric Bridge"
1. **Input**: User Message + Garment Image + 3D Mesh (.obj).
2. **Encoding**: The **VQ-VAE** (`best_model.pth`) compresses the 3D mesh into "Geometric Tokens."
3. **Reasoning**: The **VLM** (`checkpoint-12844`) ingests the image and the geometric tokens.
4. **Output**: Conversational tailoring advice (e.g., "Join edge A1 to B2 with a 1cm seam allowance").

---

## 🚀 Implementation Plan (50 Phases)

### Track A: Backend Architecture & VLM Activation (Phases 1–15)
**Activating the dormant conversational capabilities of the VLM.**

| Phase | Deliverable | Description |
|-------|------------|-------------|
| 1 | VLM SafeTensor Loader | Update `api_server.py` to utilize `AutoModelForVision2Seq` for multi-file Safetensor loading. |
| 2 | Chat Template Injection | Parse `chat_template.json` to handle multi-modal inputs (Image + Text + Mesh). |
| 3 | GPU Memory Sharding | Implement `device_map="auto"` to split the 14GB+ VLM across available T4 VRAM. |
| 4 | Processor Initialization | Configure `AutoProcessor` using `processor_config.json` for image-text tokenization. |
| 5 | VQ-VAE Encoder Bridge | Load `vqvae/best_model.pth` as a feature extractor for 3D meshes. |
| 6 | Mesh-to-Token Logic | Script the conversion of `.obj` vertex/edge data into latent embeddings. |
| 7 | Latent Concatenation | Create the logic to "prepend" mesh tokens to the VLM's text embedding layer. |
| 8 | Inference Optimization | Apply `torch.compile` to the VLM forward pass for faster chat responses. |
| 9 | FastAPI `/v2/interrogate` | Create the primary POST endpoint for consultation requests. |
| 10 | Streaming Response Logic | Implement Server-Sent Events (SSE) for "typing" effect in chat. |
| 11 | Context Window Handler | Manage history of 2048 tokens to keep the "tailor" aware of previous steps. |
| 12 | Image Pre-processing Shim | Resize and normalize input images to match the VLM's vision tower specs. |
| 13 | VQ-VAE RT Mode | Integrate `rt_vqvae.pth` for low-latency mesh interrogation. |
| 14 | System Prompt Design | "You are KORRA, a master tailor with 40 years of Savile Row and Pan-African experience..." |
| 15 | Backend Integration Test | Verify HTTP 200 for a sample prompt: "How do I sew this collar?" |

### Track B: Geometric Context & Precision (Phases 16–30)
**Ensuring the AI "sees" the specific folds and seams of the garment.**

| Phase | Deliverable | Description |
|-------|------------|-------------|
| 16 | Pattern Piece Mapping | Inject 2D pattern coordinate metadata into the VLM prompt. |
| 17 | Drape Analysis Layer | Extract "Wrinkle Heatmaps" from the mesh to identify high-tension areas. |
| 18 | Seam Identification Logic | Auto-label edges in the latent space (e.g., shoulder, side-seam). |
| 19 | Assembly Sequence Engine | Define the chronological order of sewing based on garment type. |
| 20 | Fabric Intelligence Bridge | Connect `MaterialRail` coefficients (K/B/M) to the AI's tension advice. |
| 21 | Notch Correlation | Direct the AI to reference specific notches (`drawNotch`) in the 2D pattern. |
| 22 | Grainline Awareness | AI warns the user if pattern placement conflicts with fabric grain. |
| 23 | Ease Buffer Interrogation | User asks: "Is this fit too tight?" -> AI checks mesh-skin distance. |
| 24 | Texture Mapping Context | VLM analyzes the "Image" to determine if the fabric is silk, denim, or knit. |
| 25 | Collision Analysis Report | AI identifies areas where the cloth clips the skin and suggests pattern adjustments. |
| 26 | Multi-Garment Context | AI handles "Layered" consultation (e.g., Jacket over Shirt). |
| 27 | Metric standardizer | AI provides instructions in both CM and IN based on user settings. |
| 28 | Multilingual Tailor | Support Hausa, Swahili, and French tailoring terminology. |
| 29 | Error Recovery | AI identifies "Impossible Seams" in the 3D model. |
| 30 | Context Persistence | Save the consultation log to Supabase `garment_chat_history`. |

### Track C: Frontend "Ask AI" Studio (Phases 31–45)
**Building the luxury chat interface in the dashboard.**

| Phase | Deliverable | Description |
|-------|------------|-------------|
| 31 | Floating Chat Launcher | Mint-green "Ask AI" button on the Scan Result screen. |
| 32 | Glass-Panel UI | Luxury translucent chat window with blur effect. |
| 33 | Mesh Reference Pins | Click a point on the 3D model to ask: "What is this part?" |
| 34 | SSE Client Integration | Real-time text streaming from the Kaggle backend. |
| 35 | Pattern Thumbnail Preview | AI sends mini-SVG snippets of pieces it is discussing. |
| 36 | Voice-to-Tailor | Web Speech API integration for hands-free sewing questions. |
| 37 | Suggested Questions | "How do I start?", "Best fabric for this?", "Assembly order?" |
| 38 | Message Bubble Styling | "Artisan" vs "User" distinct visual styles. |
| 39 | Image Upload in Chat | Allow users to snap a photo of their fabric for AI analysis. |
| 40 | Code/Metric Formatting | Display measurements in bold, distinct colors within chat. |
| 41 | Loading State Animation | Neural "Thinking" pulse animation. |
| 42 | Chat History View | Expandable sidebar to see previous consultation sessions. |
| 43 | Feedback Loop (Rating) | Thumbs up/down on AI advice for future fine-tuning. |
| 44 | Mobile Optimization | Responsive chat drawer for mobile tailoring. |
| 45 | Export Chat to PDF | Append the consultation log to the final Tailor Brief. |

### Track D: Hardening & Production (Phases 46–50)
**Latency, Security, and Final Polish.**

| Phase | Deliverable | Description |
|-------|------------|-------------|
| 46 | Inference Cache | Cache tokens for identical garments to save GPU cycles. |
| 47 | Content Moderation | Sanitize prompts to ensure professional tailoring focus. |
| 48 | Latency Guard | Fallback to "Standard Instructions" if Kaggle tunnel > 10s. |
| 49 | Production Deploy | Push updated `notebook.ipynb` and `measurement-screen.js`. |
| 50 | MISSION COMPLETE | Launch "KORRA AI Master Tailor." |

---

## Status (as of 2026-07-11)
- **Drafting Complete**: 50-Phase plan established.
- **Next Step**: Begin Phase 1 (SafeTensor Loader) in the Kaggle Backend.
