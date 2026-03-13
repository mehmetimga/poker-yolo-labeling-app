# Future Work

## What's Built (Current State)
- Full labeling app: FastAPI + React + Konva.js canvas + SQLite
- 52-label taxonomy (v4) with descriptions, 6 groups, BetRivers-specific
- 16 schema definitions covering all poker game states
- Template system: copy annotations from previously labeled images by schema
- Schema scoring: auto-suggest matching schema based on current annotations
- YOLO model inference integration (Ultralytics)
- Export: YOLO format + JSON metadata
- Autosave, undo/redo, keyboard shortcuts
- Image queue with status filters (new/in_progress/labeled/reviewed/approved)
- Hover tooltips for label descriptions (sidebar + canvas + annotation list)
- Docker Compose deployment with nginx

---

## Phase 3: Smarter Annotation Workflow

### Auto-labeling Pipeline
- **Pre-annotation on import**: Run YOLO inference automatically when images are imported, so labelers start with predicted boxes instead of blank canvas
- **Accept/reject flow**: Show model predictions as "pending" annotations with confidence scores, let labelers accept/reject/adjust each one instead of drawing from scratch
- **Active learning**: Prioritize low-confidence images for human review, skip high-confidence ones

### Similarity-Based Copy
- **pHash / embedding search**: Find visually similar images (same table layout, same game state) and suggest copying annotations from the closest match
- **FAISS index**: Build a vector index of labeled images for fast nearest-neighbor lookup
- **Cluster view**: Group similar screenshots together so labelers can batch-label them

### Keyboard-First Speed Mode
- **Quick label mode**: After drawing a box, auto-advance to next label in schema order (no dropdown clicking)
- **Tab to cycle**: Tab through annotations to review/adjust each one
- **Spacebar to confirm**: Accept current annotations and move to next image

---

## Phase 4: Training Loop Integration

### Dataset Management
- **Train/val/test split**: Automatically split labeled images into training sets with stratified sampling by schema
- **Version control**: Track dataset versions — which images were in each training run
- **Augmentation preview**: Show augmented versions (rotation, brightness, crop) to verify labels survive transforms

### Model Training Integration
- **One-click training**: Trigger YOLO training from the app UI with configurable hyperparameters
- **Training dashboard**: Show loss curves, mAP, per-class AP in the app
- **Model comparison**: Compare metrics across training runs side by side
- **Auto-retrain**: When N new images are labeled, automatically kick off a new training run

### Model Quality Feedback
- **Prediction vs ground truth overlay**: Show model predictions alongside human labels to spot systematic errors
- **Per-label accuracy**: Track which labels the model struggles with (e.g., bet_amount vs stack_amount confusion)
- **Error mining**: Surface images where model predictions diverge most from human labels

---

## Phase 5: Multi-User & Quality Control

### Reviewer Workflow
- **Reviewer role**: Separate labeler vs reviewer permissions
- **Review queue**: Reviewers see labeled images, can approve/reject/add comments
- **Inter-annotator agreement**: Compare labels from multiple labelers on the same image
- **Audit trail**: Full history of who labeled/reviewed/changed what and when

### Collaboration
- **Assignment system**: Assign batches of images to specific labelers
- **Progress dashboard**: Track labeling velocity per person, completion rates, quality scores
- **Comments**: Leave notes on specific annotations (e.g., "is this a quick_bet_button or confirm_button?")

---

## Phase 6: Bot Integration (End Goal)

### Screen Capture Pipeline
- **Live capture**: Continuously screenshot BetRivers poker client at configurable intervals
- **Dedup**: Skip duplicate/near-duplicate frames using pHash
- **Auto-classify**: Run inference on each frame to determine game state (schema)

### Game State Engine
- **State machine**: Map detected labels to structured game state (hero cards, pot size, available actions, player stacks)
- **OCR integration**: Read text from detected regions (pot amount, stack sizes, card values) using Tesseract or PaddleOCR
- **Action detection**: Determine what action buttons are available and their values

### Decision Engine Interface
- **API output**: Expose structured game state as JSON for the bot's decision engine
- **Latency tracking**: Monitor end-to-end time from screenshot to game state (target: <500ms)
- **Confidence gating**: Only act when detection confidence is above threshold, otherwise wait for next frame
