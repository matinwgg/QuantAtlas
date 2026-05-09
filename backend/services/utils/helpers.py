def validate_strategy(strategy: str):
    allowed = ["sma", "momentum", "mean_reversion"]

    if strategy not in allowed:
        raise ValueError(f"Strategy must be one of {allowed}")