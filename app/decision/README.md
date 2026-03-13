# Phase 7: Poker Decision Engine

## What Is This?

The decision engine is the **brain** of the poker bot. It connects to the botrunner (Phase 6), receives real-time game state, and decides what action to take — fold, call, check, raise, or bet.

It does **not** click buttons or interact with the poker client. It only outputs decisions. Mouse automation is Phase 8.

---

## How It Works

```
BetRivers Poker Client
        │
        │ screenshots
        ▼
┌─────────────────────┐
│  Botrunner (P6)     │  ← YOLO detection + OCR
│  port 8100          │  ← Outputs GameState JSON
└────────┬────────────┘
         │ WebSocket (only hero turns)
         ▼
┌─────────────────────┐
│  Decision Engine    │  ← Poker math + strategy
│  port 8200          │  ← Outputs Decision JSON
└────────┬────────────┘
         │
         ▼
    decisions.jsonl      ← Log file for review
    REST API             ← GET /decision/latest
```

### Step-by-Step Flow

1. **Connect** — On startup, the engine connects to the botrunner WebSocket at `ws://localhost:8100/state/stream?only_hero_turn=true`. It only receives states where it's our turn to act.

2. **Deduplicate** — The state tracker checks if this is a new hand or new street. If we already decided on this street, skip it. This prevents making the same decision twice from stale frames.

3. **Confidence Gate** — Skip states where the YOLO schema confidence is below 50% or card OCR confidence is below 60%. Bad vision = bad decisions.

4. **Evaluate Hand** — Run poker math on the hero's cards + community cards:
   - **Preflop**: Look up the starting hand in a 169-hand tier chart
   - **Postflop**: Evaluate the best 5-card hand from up to 7 cards
   - **Detect draws**: Flush draws (9 outs), open-ended straight draws (8 outs), gutshots (4 outs)
   - **Estimate equity**: Rule of 2 and 4 (outs × 4% on flop, outs × 2% on turn)

5. **Decide Action** — The strategy layer picks an action based on hand strength and game context.

6. **Log** — The decision is stored in a ring buffer (last 200 decisions) and appended to `decisions.jsonl` for post-session review.

---

## Poker Math

### Preflop: 169 Starting Hands

Every possible 2-card starting hand in poker is one of 169 types (13 pairs + 78 suited combos + 78 offsuit combos). We rank them into 8 tiers:

| Tier | Example Hands | What To Do |
|------|---------------|------------|
| **1 — Premium** | AA, KK, QQ, AKs | Always raise. Re-raise if someone raises. Go all-in vs 3-bet. |
| **2 — Strong** | JJ, TT, AQs, AKo | Raise. Call a 3-bet. |
| **3 — Good** | 99, 88, KQs, AQo | Raise. Call a raise. Fold to a 3-bet. |
| **4 — Playable** | 77, 66, A5s, JTs | Raise in position. Call a raise. |
| **5 — Speculative** | 55-22, 98s, 76s | Call cheaply in late position. Fold to raises. |
| **6 — Marginal** | K2s, 54s, A8o | Only play from button/blinds. |
| **7 — Weak** | KTo, QJo, J6s | Almost always fold. |
| **8 — Trash** | Everything else | Fold. |

**How we detect the scenario:**
- No one has raised yet → **open pot** (we can raise to start the action)
- Someone raised (bet > 1 big blind) → **facing a raise**
- Large raise (bet > 10 big blinds) → **facing a 3-bet**

### Postflop: Hand Evaluation

After the flop/turn/river, we evaluate the best 5-card poker hand from up to 7 cards (2 hero + 5 community). Hand rankings from worst to best:

| Rank | Hand | Example |
|------|------|---------|
| 0 | High Card | A-K-9-7-3 (no pair) |
| 1 | One Pair | K-K-A-9-3 |
| 2 | Two Pair | K-K-9-9-A |
| 3 | Three of a Kind | K-K-K-A-9 |
| 4 | Straight | 5-6-7-8-9 |
| 5 | Flush | 5 cards same suit |
| 6 | Full House | K-K-K-9-9 |
| 7 | Four of a Kind | K-K-K-K-A |
| 8 | Straight Flush | 5-6-7-8-9 same suit |

The evaluator checks all C(7,5) = 21 combinations and picks the best.

### Draws and Outs

A "draw" means you're one card away from completing a strong hand. "Outs" are the number of cards in the deck that complete it.

| Draw | What It Means | Outs | Example |
|------|---------------|------|---------|
| Flush draw | 4 cards of one suit, need 1 more | 9 | Hero: A♥K♥, Board: 7♥2♥5♣ |
| Open-ended straight draw (OESD) | 4 in a row, can complete on either end | 8 | Hero: 8♣9♦, Board: T♠J♥3♣ |
| Gutshot | 4 within a span of 5, one gap | 4 | Hero: 8♣9♦, Board: T♠Q♥3♣ (need J) |

### Equity: Rule of 2 and 4

A quick shortcut to estimate your chance of completing a draw:

- **Flop** (2 cards to come): `equity ≈ outs × 4%`
- **Turn** (1 card to come): `equity ≈ outs × 2%`

Example: Flush draw on the flop = 9 outs × 4% = **36% equity**.

---

## Strategy: Layer 1 (Rule-Based TAG)

TAG = **T**ight **A**ggressive — play fewer hands, but play them aggressively.

### Preflop Actions

| Tier | Open Pot | Facing Raise | Facing 3-Bet |
|------|----------|-------------|--------------|
| 1 | Raise 3BB | 3-bet (3× raise) | 4-bet / all-in |
| 2 | Raise 3BB | Raise or call | Call |
| 3 | Raise 3BB | Call | Fold |
| 4 | Raise 3BB | Call | Fold |
| 5 | Min-raise | Fold | Fold |
| 6-8 | Fold | Fold | Fold |

BB = big blind ($0.50). So "Raise 3BB" = raise to $1.50.

### Postflop Actions

| Your Hand | Action |
|-----------|--------|
| **Two pair or better** (two pair, trips, straight, flush, full house, quads) | Bet 60-75% of pot. If someone bets, raise. |
| **One pair** | Bet 60% pot for value. Call small bets. Fold to large bets. |
| **Strong draw** (8+ outs: flush draw or OESD) | Bet 50% pot as a semi-bluff. Or call if someone else bets. |
| **Weak draw** (4 outs: gutshot) | Call only if very cheap (< 25% pot). |
| **Nothing** (but we raised preflop) | Continuation bet 40% pot on flop ~65% of the time. |
| **Nothing** (we didn't raise) | Check if possible. Fold if someone bets. |

### Action Matching

The strategy computes a desired action and amount, then matches it to the closest `AvailableAction` from the game state. The botrunner detects the actual buttons on screen (fold, call $X, raise to $Y), so we pick the best match. Fallback: check if available, else fold.

---

## Strategy Layers (Future)

The engine is designed with a layered architecture for progressive improvement:

| Layer | Name | Status | What It Does |
|-------|------|--------|-------------|
| **1** | Rule-Based TAG | **Implemented** | Preflop chart + postflop value/bluff decisions |
| **2** | Pot Odds + Equity | Stub | Compares pot odds to draw equity mathematically |
| **3** | Position Awareness | Stub | Adjusts ranges based on seat position relative to dealer |

Layers are chained: Layer 1 runs first. If it returns a decision, we use it. If not, Layer 2 tries, then Layer 3. This allows each layer to override or refine the previous one.

---

## Configuration

All settings use the `DECISION_` env prefix:

```bash
# Required: botrunner must be running
DECISION_BOTRUNNER_HOST=localhost
DECISION_BOTRUNNER_PORT=8100

# Game parameters (match the table you're playing)
DECISION_BIG_BLIND=0.50
DECISION_SMALL_BLIND=0.25

# Strategy tuning
DECISION_ACTIVE_LAYERS=rules          # "rules", "rules,odds", "rules,odds,position"
DECISION_CBET_FREQUENCY=0.65          # How often to c-bet with air (0.0-1.0)
DECISION_BET_SIZE_FRACTION=0.60       # Default bet as fraction of pot

# Confidence gates (skip unreliable vision data)
DECISION_MIN_SCHEMA_CONFIDENCE=0.5
DECISION_MIN_CARD_CONFIDENCE=0.6

# Logging
DECISION_LOG_DECISIONS_TO_FILE=true
DECISION_DECISION_LOG_PATH=decisions.jsonl
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service status, botrunner connection, config |
| `GET` | `/decision/latest` | Latest decision (204 if none yet) |
| `GET` | `/decision/history?limit=20` | Last N decisions (max 200) |

---

## File Structure

```
app/decision/
├── run.py                          # Entry point: python run.py
├── requirements.txt                # fastapi, uvicorn, websockets, pydantic-settings
└── decision/
    ├── main.py                     # FastAPI app + lifespan (starts WS consumer)
    ├── config.py                   # DECISION_ env settings
    │
    ├── models/
    │   ├── game_state.py           # GameState from botrunner (Pydantic)
    │   ├── card.py                 # Card(Rank, Suit) value objects
    │   └── decision.py             # Decision + HandStrength output
    │
    ├── poker/                      # Pure poker math (no I/O)
    │   ├── card.py                 # Parse CardValue → Card, hand notation
    │   ├── preflop_chart.py        # 169 hands → tier 1-8
    │   ├── hand_eval.py            # Best 5-of-7 hand evaluator
    │   ├── outs.py                 # Flush/straight draw detection
    │   └── equity.py               # Rule of 2 and 4
    │
    ├── strategy/                   # Decision logic layers
    │   ├── base.py                 # StrategyLayer protocol
    │   ├── layer1_rules.py         # TAG rules (the main brain)
    │   ├── layer2_odds.py          # Pot odds (future stub)
    │   ├── layer3_position.py      # Position (future stub)
    │   └── composer.py             # Chains layers + hand evaluation
    │
    ├── client/                     # Botrunner connection
    │   ├── ws_consumer.py          # WebSocket client with auto-reconnect
    │   └── state_tracker.py        # Dedup: one decision per street per hand
    │
    ├── api/                        # REST endpoints
    │   ├── health_router.py        # GET /health
    │   └── decision_router.py      # GET /decision/latest, /history
    │
    └── log/                        # Decision storage
        ├── decision_buffer.py      # Ring buffer (last 200 decisions)
        └── file_logger.py          # Append to decisions.jsonl
```

---

## Running

```bash
# 1. Install dependencies
cd app/decision
pip install -r requirements.txt

# 2. Start botrunner first (separate terminal)
cd app/botrunner
BOT_YOLO_MODEL_PATH=/path/to/model.pt python run.py

# 3. Start decision engine
cd app/decision
python run.py
# → Starts on port 8200
# → Connects to botrunner WebSocket
# → Logs: "Connected to botrunner WebSocket"

# 4. Check health
curl http://localhost:8200/health

# 5. View decisions (after playing a hand)
curl http://localhost:8200/decision/latest | python3 -m json.tool

# 6. Review session log
cat decisions.jsonl | python3 -m json.tool --json-lines
```

---

## Example Decision Output

```json
{
  "timestamp": 1710234567.89,
  "frame_id": "a1b2c3d4e5f6",
  "game_phase": "preflop",
  "hero_cards": ["Ah", "Ks"],
  "community_cards": [],
  "pot_size": 1.25,
  "action": "raise",
  "amount": 1.50,
  "reasoning": "Tier 1 premium hand, raise open",
  "hand_strength": {
    "category": "preflop",
    "draws": [],
    "outs": 0,
    "equity_estimate": 0.0
  },
  "strategy_layer": "layer1_rules",
  "confidence": 0.7
}
```

---

## System Architecture (All Phases)

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Labeling App   │     │  Botrunner      │     │  Decision Engine │
│  (Phase 1-5)    │     │  (Phase 6)      │     │  (Phase 7)       │
│                 │     │                 │     │                  │
│  Frontend :3000 │     │  Vision :8100   │     │  Brain :8200     │
│  Backend  :8000 │     │  YOLO + OCR     │────▶│  Poker Math      │
│  Database       │     │  Screen Capture │  WS │  TAG Strategy    │
│                 │     │                 │     │                  │
│  Train YOLO     │     │  → GameState    │     │  → Decision      │
│  Label Images   │     │    JSON         │     │    JSON          │
│  Review Quality │     │                 │     │                  │
└─────────────────┘     └─────────────────┘     └──────────────────┘
        │                       │                        │
        │  trained model.pt     │  screenshots           │  decisions.jsonl
        └───────────────────────┘                        │
                                                         ▼
                                                  Phase 8 (future)
                                                  Mouse Automation
```
