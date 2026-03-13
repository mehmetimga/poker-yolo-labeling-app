from pydantic_settings import BaseSettings


class DecisionSettings(BaseSettings):
    # Botrunner connection
    botrunner_host: str = "localhost"
    botrunner_port: int = 8100

    # API
    api_port: int = 8200

    # Game parameters
    big_blind: float = 0.50
    small_blind: float = 0.25

    # Strategy
    active_layers: str = "rules"  # "rules", "rules,odds", "rules,odds,position"
    cbet_frequency: float = 0.65
    bet_size_fraction: float = 0.60

    # Confidence gates
    min_schema_confidence: float = 0.5
    min_card_confidence: float = 0.6

    # Logging
    log_decisions_to_file: bool = True
    decision_log_path: str = "decisions.jsonl"

    model_config = {"env_prefix": "DECISION_"}


settings = DecisionSettings()
