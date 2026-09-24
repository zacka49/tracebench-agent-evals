from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .analysis import build_report
from .cases import write_cases
from .runner import run_config
from .schemas import RunConfig
from .storage import EpisodeStore


def load_config(path: Path) -> RunConfig:
    return RunConfig.model_validate(yaml.safe_load(path.read_text("utf-8")))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="tracebench")
    commands = root.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate")
    generate.add_argument("--output", type=Path, default=Path("tasks/cases.json"))
    generate.add_argument("--count", type=int, default=20)
    generate.add_argument("--seed", type=int, default=20260924)
    validate = commands.add_parser("validate")
    validate.add_argument("--config", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--no-resume", action="store_true")
    report = commands.add_parser("report")
    report.add_argument("--db", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--data-root", type=Path, default=Path("service-data"))
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "generate":
        cases = write_cases(args.output, args.count, args.seed)
        print(f"Wrote {len(cases)} cases to {args.output}")
    elif args.command == "validate":
        config = load_config(args.config)
        print(config.model_dump_json(indent=2))
    elif args.command == "run":
        config = load_config(args.config)
        records = run_config(config, args.output, resume=not args.no_resume)
        markdown, html_path = build_report(records, args.output)
        succeeded = sum(record.status == "succeeded" for record in records)
        print(f"Completed {succeeded}/{len(records)} episodes")
        print(f"Report: {markdown} ({html_path})")
    elif args.command == "serve":
        import uvicorn

        from .api import create_app

        uvicorn.run(create_app(args.data_root), host=args.host, port=args.port)
    elif args.command == "report":
        with EpisodeStore(args.db) as store:
            records = store.records()
        markdown, html_path = build_report(records, args.output)
        print(f"Report: {markdown} ({html_path})")


if __name__ == "__main__":
    main()
