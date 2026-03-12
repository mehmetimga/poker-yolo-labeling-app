# Poker YOLO Labeling App — Full Product & Engineering Specification

## 1. Purpose

Build a full annotation platform for poker mobile application screenshots that supports:

* manual bounding-box labeling for YOLO datasets
* predefined object label taxonomy
* predefined poker screen schemas / game states
* schema-aware annotation suggestions
* similar-screen retrieval and label reuse
* model-assisted pre-annotations in later phases
* export to YOLO format plus richer metadata JSON
* review, correction, and dataset management workflows

This app is intended to reduce manual labeling effort for poker UI automation, game-state detection, and computer-vision model training.

---

## 2. Problem Statement

The poker mobile application has recurring but not identical screens. There are around 15 known high-level schemas (screen states / UI layouts), but the content inside the images changes:

* numbers change
* cards change
* chips change
* active players change
* action buttons may differ
* timers may appear/disappear
* popups may appear
* names and avatars may differ
* screen resolution or cropping may vary

A generic labeling tool is not enough. The app must support:

1. drawing boxes and assigning labels quickly
2. reusing prior knowledge from similar screens
3. recognizing likely schema/game-state matches
4. suggesting missing expected labels based on schema
5. eventually auto-suggesting boxes via trained models

---

## 3. Core Goals

### 3.1 Functional goals

* Load folders of images or datasets
* Draw, edit, resize, move, delete rectangles
* Assign labels from a predefined taxonomy
* Save labels in YOLO format
* Save richer metadata in JSON
* Assign or auto-suggest one of ~15 screen schemas
* Suggest labels based on region, history, and schema
* Find similar already-labeled images
* Copy labels from similar images or previous frame
* Support review workflow and quality control
* Support keyboard shortcuts for fast labeling
* Support multi-user readiness in future, even if MVP is single-user

### 3.2 Business / practical goals

* drastically reduce annotation time
* standardize labeling across poker datasets
* prepare training data for YOLO object detection
* support downstream poker UI automation and game-state recognition
* provide extensible foundation for later active learning and auto-labeling

---

## 4. Non-Goals for MVP

Do not build these in the first version unless they come nearly free:

* full distributed annotation platform with complex RBAC
* full model training pipeline inside the app
* OCR pipeline embedded into the first release
* video labeling timeline editor
* segmentation / polygon annotation
* keypoint annotation
* enterprise billing / SaaS multi-tenancy

These can be phase 2 or 3.

---

## 5. User Personas

### 5.1 Primary user

Poker CV/AI engineer or QA automation engineer who needs to label poker mobile app screenshots.

### 5.2 Secondary user

Reviewer / data-quality owner who validates annotations and schema consistency.

### 5.3 Future user

Data scientist training detectors, classifiers, or game-state models.

---

## 6. High-Level Product Concept

The application should combine three capabilities:

### A. Annotation tool

Classic object detection labeling interface.

### B. Schema-aware assistant

The app knows a set of predefined poker screen schemas and can suggest which schema best matches a partially labeled image.

### C. Similarity / reuse engine

The app can find previously labeled screens that look similar and allow copying their labels, then editing differences.

This combination is the key product idea.

---

## 7. Object Label Taxonomy

The app must support a configurable taxonomy, not hardcoded labels.

Recommended starter label groups:

### 7.1 Table / layout structure

* poker_table
* seat
* hero_seat
* dealer_button
* community_cards_area
* hero_cards_area
* pot_area
* player_info_panel

### 7.2 Cards / game objects

* hero_card
* board_card
* facedown_card
* pot_amount
* stack_amount
* bet_amount
* blind_indicator

### 7.3 Action controls

* fold_button
* call_button
* check_button
* raise_button
* bet_button
* all_in_button
* slider
* quick_bet_button
* confirm_button
* cancel_button

### 7.4 Status / state indicators

* timer
* active_turn_indicator
* waiting_label
* winner_banner
* hand_result_popup
* reconnect_popup
* buyin_popup
* lobby_button
* chat_button
* settings_button

### 7.5 Optional text/UI elements (only if useful)

* table_name
* tournament_name
* balance_label
* blinds_label

Important: avoid over-labeling decorative or low-value elements in MVP.

---

## 8. Schema / Game-State Model

The app must support around 15 predefined screen schemas. These are high-level image-level states, not individual object labels.

Examples:

* table_preflop_my_turn
* table_preflop_waiting
* table_flop_my_turn
* table_turn_my_turn
* table_river_waiting
* all_in_popup
* buyin_popup
* tournament_lobby
* cash_lobby
* table_loading
* result_popup

Each schema should be defined by:

* required labels
* optional labels
* expected rough spatial regions
* expected counts or count ranges
* penalties for contradictory labels

### 8.1 Example schema definition

```json
{
  "name": "table_preflop_my_turn",
  "required": [
    { "label": "hero_card", "count": 2, "region": "bottom_center" },
    { "label": "fold_button", "count": 1, "region": "bottom" },
    { "label": "call_button", "count": 1, "region": "bottom" },
    { "label": "raise_button", "count": 1, "region": "bottom" }
  ],
  "optional": [
    { "label": "pot_amount", "count": 1, "region": "center" },
    { "label": "dealer_button", "count": 1 },
    { "label": "seat", "count_min": 2, "count_max": 9 }
  ],
  "forbidden": [
    { "label": "winner_banner" },
    { "label": "buyin_popup" }
  ]
}
```

---

## 9. Main Workflows

### 9.1 Manual annotation workflow

1. User opens image
2. User draws rectangle
3. User assigns label from dropdown / search / hotkey
4. Annotation is saved locally in memory
5. User continues until screen is sufficiently labeled
6. User optionally assigns schema manually or accepts suggested schema
7. User saves

### 9.2 Assisted schema workflow

1. User labels a few core objects
2. App computes schema match scores
3. App suggests top matching schemas
4. App shows missing expected labels for selected schema
5. User accepts schema or overrides it

### 9.3 Similar-image reuse workflow

1. User opens unlabeled image
2. App finds nearest labeled images
3. User previews top matches
4. User copies annotations from one match
5. User adjusts changed boxes only
6. User saves

### 9.4 Review workflow

1. Reviewer opens labeled images from a queue
2. Reviewer checks boxes, labels, schema, and confidence
3. Reviewer approves / rejects / edits
4. Dataset status updates accordingly

### 9.5 Future auto-annotation workflow

1. Detection model produces candidate boxes
2. App shows them with confidence scores
3. User accepts, edits, or rejects
4. Corrections are saved for retraining

---

## 10. Functional Requirements

### 10.1 Dataset management

* Import folder of images
* Support common image formats: png, jpg, jpeg, webp
* Create/open project
* Project stores:

  * label taxonomy
  * schema definitions
  * image list
  * annotations
  * review statuses
* Filter images by:

  * unlabeled
  * partially labeled
  * labeled
  * reviewed
  * schema
  * confidence

### 10.2 Annotation canvas

* Pan / zoom
* Draw rectangle
* Select rectangle
* Move / resize rectangle
* Delete rectangle
* Duplicate rectangle
* Toggle label visibility
* Color-code labels
* Display box label text
* Snap/guide behavior optional
* Support keyboard shortcuts

### 10.3 Label assignment

* Searchable label dropdown
* Recent labels list
* Hotkeys for common labels
* Optional label aliases
* Validation against schema if schema selected

### 10.4 Schema engine

* Load schema config from JSON/YAML
* Score current image against all schemas
* Return top N schema matches
* Show missing required labels
* Show contradictory / suspicious labels
* Allow manual override

### 10.5 Similarity engine

* Find most similar previously labeled images
* Prefer same project/dataset
* Show thumbnail previews
* Enable copy-all annotations
* Enable partial-copy (selected labels only)

### 10.6 Persistence

* Save YOLO txt files
* Save JSON metadata files
* Autosave draft state
* Allow export/import of project state

### 10.7 Review / QA

* Annotation status per image
* Reviewer comments optional
* Mark as approved / rejected / needs work
* Show incomplete images
* Show images with low schema confidence

### 10.8 Analytics / stats

* Number of images labeled
* Count by label
* Count by schema
* Count by review status
* Missing-label frequency
* Annotation throughput stats optional

---

## 11. Non-Functional Requirements

### 11.1 Performance

* App must remain responsive on large image sets
* Canvas interactions should feel immediate
* Similarity query should ideally return in under ~1 second for moderate datasets

### 11.2 Reliability

* Autosave drafts
* No lost annotations on navigation or refresh
* Explicit save + recover unsaved session support

### 11.3 Extensibility

* Label taxonomy configurable
* Schema definitions configurable
* Suggestion logic pluggable
* Model inference optional and modular

### 11.4 Portability

* Should run locally on developer laptop
* Prefer Dockerized deployment
* Should support both single-machine and simple team deployment later

---

## 12. Recommended Tech Stack

### Frontend

* React
* TypeScript
* Vite or Next.js
* Konva.js or Fabric.js for annotation canvas
* Zustand or Redux Toolkit for state management
* Tailwind CSS for UI
* React Query for server data fetching

### Backend

* FastAPI (recommended) or Go if preferred
* Python is recommended because later CV/model integration is easier

### Storage

* SQLite for MVP metadata
* Local filesystem for images and exported labels
* JSON config files for schemas and taxonomy

### Similarity / embeddings

* Start with simple feature-based or image-embedding approach
* FAISS or simple nearest-neighbor index later

### Packaging

* Docker / Docker Compose

Recommended MVP stack:

* React + TypeScript + Konva + FastAPI + SQLite + local filesystem

---

## 13. System Architecture

### 13.1 Frontend responsibilities

* project browser
* image list / queue
* annotation canvas
* label panel
* schema suggestion panel
* similar-image panel
* export/review screens

### 13.2 Backend responsibilities

* serve project and image metadata
* persist annotations
* run schema scoring
* run similarity search
* handle import/export
* optionally run model inference later

### 13.3 Suggested modules

#### Frontend modules

* ProjectPage
* ImageQueuePanel
* AnnotationCanvas
* BoundingBoxLayer
* LabelSidebar
* SchemaSuggestionPanel
* SimilarImagesPanel
* ReviewPanel
* ExportPanel

#### Backend modules

* project_service
* annotation_service
* schema_service
* similarity_service
* export_service
* inference_service (future)
* stats_service

---

## 14. Suggested Folder Structure

```text
app/
  frontend/
    src/
      components/
      features/
        annotation/
        labels/
        schemas/
        projects/
        review/
        export/
      pages/
      hooks/
      lib/
      types/
  backend/
    app/
      api/
      models/
      schemas/
      services/
      repositories/
      utils/
      config/
    data/
    tests/
  shared/
    schemas/
    taxonomy/
  docker/
  docs/
```

---

## 15. Data Model

### 15.1 Core entities

#### Project

* id
* name
* description
* created_at
* updated_at
* image_root_path
* taxonomy_version
* schema_version

#### ImageRecord

* id
* project_id
* filename
* filepath
* width
* height
* hash
* status
* assigned_schema
* suggested_schema
* schema_confidence
* review_status
* created_at
* updated_at

#### Annotation

* id
* image_id
* label
* x_min
* y_min
* x_max
* y_max
* normalized_x_center
* normalized_y_center
* normalized_width
* normalized_height
* source (manual / copied / model / imported)
* confidence_optional
* created_at
* updated_at

#### SchemaDefinition

* name
* required_rules
* optional_rules
* forbidden_rules
* version

#### SimilarityMatch

* source_image_id
* matched_image_id
* score

---

## 16. File Formats

### 16.1 YOLO txt export

Each image should export a corresponding `.txt`:

```text
<class_id> <x_center> <y_center> <width> <height>
```

All coordinates normalized to [0,1].

### 16.2 Metadata JSON export

Each image should also have richer metadata.

Example:

```json
{
  "image": "frame_001.png",
  "project": "poker-mobile-v1",
  "assigned_schema": "table_preflop_my_turn",
  "suggested_schemas": [
    { "name": "table_preflop_my_turn", "score": 0.94 },
    { "name": "table_flop_my_turn", "score": 0.41 }
  ],
  "review_status": "approved",
  "annotations": [
    {
      "label": "fold_button",
      "bbox_xyxy": [110, 1180, 290, 1260],
      "bbox_yolo": [0.18, 0.92, 0.14, 0.06],
      "source": "manual"
    }
  ]
}
```

### 16.3 Taxonomy config

Configurable label definitions, colors, aliases, optional shortcuts.

### 16.4 Schema config

Configurable schema definitions as JSON/YAML.

---

## 17. Schema Matching Logic

Start with a rule-based engine.

### 17.1 Inputs

* current annotations
* image dimensions
* selected schema definitions

### 17.2 Scoring principles

* required label present: strong positive score
* required label in expected region: extra positive score
* correct count: positive score
* optional label present: medium positive score
* forbidden label present: strong negative score
* missing required label: strong negative score

### 17.3 Output

For each schema, return:

* schema name
* total score
* normalized confidence
* missing labels
* conflicting labels
* reasons / explanation

### 17.4 Example response

```json
{
  "top_matches": [
    {
      "schema": "table_preflop_my_turn",
      "score": 0.93,
      "missing": ["dealer_button"],
      "conflicts": []
    },
    {
      "schema": "table_flop_my_turn",
      "score": 0.44,
      "missing": ["board_card"],
      "conflicts": []
    }
  ]
}
```

---

## 18. Region Model

To make schemas robust across resolutions, use normalized spatial regions.

### 18.1 Suggested regions

* top_left
* top_center
* top_right
* center_left
* center
* center_right
* bottom_left
* bottom_center
* bottom_right
* full_bottom_strip
* center_table

### 18.2 Implementation idea

Represent regions in normalized coordinates.

Example:

```json
{
  "bottom_center": { "x_min": 0.25, "y_min": 0.75, "x_max": 0.75, "y_max": 1.0 }
}
```

Then check annotation box center against these zones.

---

## 19. Similarity / Reuse Engine

This is one of the highest-value features.

### 19.1 MVP version

Use simple image-level features or perceptual hash to find similar screens.

Potential approaches:

* perceptual hash (pHash)
* color histogram + layout heuristics
* downsampled image embedding

### 19.2 Improved version

Use image embeddings from a lightweight vision model and nearest-neighbor retrieval.

### 19.3 User actions

* view top 5 similar screens
* copy all boxes
* copy only boxes for selected labels
* copy schema only

### 19.4 Important usability rule

After copy, all copied annotations should be clearly marked as copied and editable.

---

## 20. Suggested APIs

### Projects

* `GET /projects`
* `POST /projects`
* `GET /projects/{id}`
* `POST /projects/{id}/import-images`

### Images

* `GET /projects/{id}/images`
* `GET /images/{id}`
* `GET /images/{id}/file`

### Annotations

* `GET /images/{id}/annotations`
* `PUT /images/{id}/annotations`
* `POST /images/{id}/annotations/autosave`

### Schemas

* `GET /schemas`
* `POST /schemas/score`
* `PUT /images/{id}/schema`

### Similarity

* `GET /images/{id}/similar`
* `POST /images/{id}/copy-annotations-from/{source_id}`

### Review

* `PUT /images/{id}/review-status`

### Export

* `POST /projects/{id}/export/yolo`
* `POST /projects/{id}/export/metadata`

### Future inference

* `POST /images/{id}/predict`
* `POST /projects/{id}/reindex-similarity`

---

## 21. UI / UX Requirements

### 21.1 Main layout

Recommended three-column layout:

* left: image queue / filters
* center: annotation canvas
* right: labels, schema suggestions, similar images, metadata

### 21.2 Keyboard shortcuts

Must support fast workflow.

Suggested shortcuts:

* `N`: next image
* `P`: previous image
* `B`: new box
* `Delete`: delete selected box
* `Ctrl/Cmd + S`: save
* `1..9`: common labels or tools
* `Z`: zoom tool
* `Space`: pan temporarily
* `C`: copy previous annotations

### 21.3 Helpful UI features

* highlight selected box
* show label color legend
* show label counts per image
* show schema confidence bar
* show missing expected labels
* show source of annotation: manual/copied/model
* confirm on navigation only if unsaved changes exist

### 21.4 Accessibility / ergonomics

* large click targets
* dark mode optional
* scalable UI for laptop screens

---

## 22. Validation Rules

The app should validate:

* bounding boxes stay within image
* zero-area boxes are invalid
* labels must exist in taxonomy
* schema must exist in config
* duplicate identical boxes can optionally warn
* impossible schema contradictions can warn

Validation should warn, not block, unless data becomes corrupt.

---

## 23. Review & Quality Control

### 23.1 Image statuses

* new
* in_progress
* labeled
* reviewed
* approved
* rejected

### 23.2 Review checks

* missing key boxes
* suspicious box size/location
* schema confidence mismatch
* inconsistent labels across similar screens

### 23.3 Suggested QA reports

* images with no schema
* images with low schema confidence
* images with unusually high/low annotation count
* label imbalance report

---

## 24. Auto-Annotation Roadmap

### Phase 1

No ML. Only manual annotation + schema suggestions + similar-image copy.

### Phase 2

Train initial YOLO detector on labeled objects.

### Phase 3

Add pre-annotation flow:

* model returns candidate boxes + labels + confidence
* app shows them as suggestions
* user confirms/edits

### Phase 4

Add active learning:

* prioritize uncertain images
* prioritize images from unseen layouts
* send difficult examples to review queue

---

## 25. Suggested Development Phases

### Phase 0 — Planning

* finalize label taxonomy
* finalize initial 15 schemas
* define dataset folder structure
* define export formats

### Phase 1 — MVP

Build:

* project creation
* image import
* annotation canvas
* manual boxes
* label dropdown
* YOLO export
* metadata JSON export
* schema config loading
* schema scoring and suggestions

### Phase 2 — Productivity features

Build:

* keyboard shortcuts
* autosave
* review statuses
* filters
* recent labels
* missing-label hints
* previous-image copy

### Phase 3 — Similarity engine

Build:

* image similarity index
* nearest labeled screen retrieval
* annotation copy from similar image

### Phase 4 — ML assistance

Build:

* model inference service
* pre-annotations
* confidence filtering
* acceptance/edit workflow

### Phase 5 — Team features

Build:

* simple multi-user mode
* reviewer role
* comments / audit trail

---

## 26. Acceptance Criteria for MVP

The MVP is complete when all of the following are true:

1. User can create a project and import images
2. User can draw/edit/delete rectangles on images
3. User can assign predefined labels
4. App saves annotations and reloads them correctly
5. App exports valid YOLO txt files
6. App exports metadata JSON files
7. App can load predefined schema definitions
8. App can suggest top matching schema from partial annotations
9. App shows missing expected labels for selected schema
10. User can manually override suggested schema
11. App supports basic filtering by image status
12. Autosave prevents easy data loss

---

## 27. Stretch Goals

* OCR integration for numeric fields
* video frame ingestion
* frame-to-frame annotation propagation
* polygon segmentation support
* plugin system for custom schema rules
* collaborative labeling mode
* cloud object storage support
* diff view between copied and edited annotations

---

## 28. Testing Requirements

### Frontend tests

* canvas interaction tests
* box creation/edit/delete tests
* label assignment tests
* schema panel rendering tests

### Backend tests

* schema scoring unit tests
* YOLO export correctness tests
* metadata JSON serialization tests
* similarity retrieval tests
* project persistence tests

### Integration tests

* create project → import images → annotate → save → reload → export

### Manual QA scenarios

* box edits persist after refresh
* copy annotations from similar image works
* invalid boxes are rejected or warned
* schema suggestions update after annotation changes

---

## 29. Developer Guidance / Implementation Notes

### 29.1 Important implementation principle

Keep business logic out of the canvas component where possible.

* canvas handles interaction and rendering
* application state holds annotations
* backend/services handle schema scoring and persistence

### 29.2 Avoid hardcoding poker assumptions in UI code

Store taxonomy and schemas in configuration files.

### 29.3 Keep file formats explicit and versioned

Add version fields to JSON metadata and config.

### 29.4 Build for correction, not perfect automation

The fastest usable tool is one that makes correction easy.

---

## 30. Suggested Initial Backlog

### Epic 1 — Project & dataset management

* create/open project
* import image folder
* image queue and filters

### Epic 2 — Annotation canvas

* render image
* create/edit/delete boxes
* zoom/pan/select

### Epic 3 — Labels and taxonomy

* load taxonomy config
* searchable label list
* color mapping and hotkeys

### Epic 4 — Save/export

* save annotations
* reload annotations
* export YOLO and JSON

### Epic 5 — Schema engine

* load schema config
* score schemas
* display suggestions and missing labels

### Epic 6 — Review workflow

* mark statuses
* filtering by review state

### Epic 7 — Similarity engine

* compute image features
* nearest-neighbor search
* copy labels from match

### Epic 8 — Future ML assistance

* inference endpoint
* suggestion acceptance flow

---

## 31. Example Task Breakdown for Cursor / Claude Code

### Backend tasks

1. Create FastAPI project structure
2. Implement project CRUD
3. Implement image import service
4. Implement annotation persistence service
5. Implement YOLO export service
6. Implement metadata JSON export service
7. Implement schema scoring service
8. Implement similarity search service placeholder
9. Add SQLite models and migrations
10. Add tests

### Frontend tasks

1. Create React app with TypeScript
2. Build project list/open screen
3. Build image queue sidebar
4. Build annotation canvas using Konva
5. Build label sidebar and box inspector
6. Build schema suggestions panel
7. Build save/autosave workflow
8. Build export controls
9. Build filters and review status UI
10. Add keyboard shortcuts

### Config/data tasks

1. Create initial taxonomy JSON
2. Create initial 15 schema JSON definitions
3. Create sample dataset folder structure
4. Create mock annotation files for testing

---

## 32. Dataset Folder Structure Suggestion

```text
datasets/
  poker-mobile-v1/
    images/
      frame_0001.png
      frame_0002.png
    labels_yolo/
      frame_0001.txt
      frame_0002.txt
    metadata/
      frame_0001.json
      frame_0002.json
    config/
      taxonomy.json
      schemas.json
```

---

## 33. Example Taxonomy Config

```json
{
  "version": 1,
  "labels": [
    { "id": 0, "name": "hero_card", "color": "#ef4444", "shortcut": "1" },
    { "id": 1, "name": "board_card", "color": "#3b82f6", "shortcut": "2" },
    { "id": 2, "name": "fold_button", "color": "#22c55e", "shortcut": "3" },
    { "id": 3, "name": "call_button", "color": "#eab308", "shortcut": "4" },
    { "id": 4, "name": "raise_button", "color": "#a855f7", "shortcut": "5" }
  ]
}
```

---

## 34. Risks / Challenges

### 34.1 Risk: taxonomy grows uncontrollably

Mitigation: keep labels task-driven and versioned.

### 34.2 Risk: schemas are too rigid

Mitigation: use required/optional/forbidden rules and normalized regions instead of exact coordinates.

### 34.3 Risk: copied annotations create hidden errors

Mitigation: clearly mark copied boxes and require lightweight review.

### 34.4 Risk: canvas UX becomes slow or frustrating

Mitigation: prioritize keyboard shortcuts and precise interaction from early stage.

### 34.5 Risk: trying to add ML too early

Mitigation: make rule-based assistance excellent first.

---

## 35. Final Build Recommendation

Build the app in this order:

1. manual annotation foundation
2. schema-aware suggestion engine
3. save/export correctness
4. workflow speed improvements
5. similar-screen retrieval and copy
6. ML-assisted pre-annotation

The key principle is: **optimize for correction and reuse, not perfect automation on day one**.

---

## 36. Deliverables Expected from the Coding Agent

The coding agent should produce:

* full frontend app
* full backend app
* Docker setup
* README with local run instructions
* sample taxonomy config
* sample schema config
* sample seed project
* tests for schema scoring and YOLO export
* clear architecture notes

---

## 37. What to Tell Cursor / Claude Code

Use this document as the product and engineering specification. Build the MVP first, with clean modular architecture, configuration-driven labels and schemas, and production-quality code organization. Prioritize fast annotation UX, correct export formats, schema-aware suggestions, and extensibility for future similarity search and model-assisted labeling.
