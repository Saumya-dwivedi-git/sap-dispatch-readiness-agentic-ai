import argparse
import json
from datetime import date, datetime
from pathlib import Path

from sdra_agentic_core import SdraDispatchReadinessAgent
from sdra_readiness_engine import SdraReadinessEngine
from sdra_sap_gateway import SdraSapGateway


def parse_args():
    parser = argparse.ArgumentParser(description="Run SDRA_DISPATCH_READINESS_AGENT against SAP services")
    parser.add_argument("--config", default="../config/sdra_agent_config.example.json", help="Path to SDRA config JSON")
    parser.add_argument("--planning-date", default="TODAY", help="Planning date in YYYY-MM-DD or TODAY")
    parser.add_argument("--check-config", action="store_true", help="Validate SAP connection environment variables only")
    return parser.parse_args()


def load_config(config_path: Path):
    with config_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_planning_date(value: str) -> date:
    if value.upper() == "TODAY":
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def main():
    args = parse_args()
    src_dir = Path(__file__).resolve().parent
    base_dir = src_dir.parent
    config_path = (src_dir / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)
    config = load_config(config_path)

    gateway = SdraSapGateway(config, base_dir)
    missing = gateway.validate_connection_settings()
    if args.check_config:
        if missing:
            print("SDRA_DISPATCH_READINESS_AGENT config check failed.")
            print("Missing environment variables:")
            for name in missing:
                print(f"- {name}")
            return 2
        print("SDRA_DISPATCH_READINESS_AGENT config check passed.")
        return 0

    if missing:
        raise RuntimeError("Missing required SAP environment variables: " + ", ".join(missing))

    planning_date = resolve_planning_date(args.planning_date)
    horizon_days = int(config["runtime"].get("planning_horizon_days", 0))
    agent = SdraDispatchReadinessAgent(gateway, SdraReadinessEngine())
    result = agent.run(planning_date, horizon_days)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
