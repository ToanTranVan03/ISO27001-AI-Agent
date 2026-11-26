import argparse
import sys
from io import TextIOWrapper
from json import dumps
from os import getenv
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

from compliance_ai.admin import (
    configure_roles,
    demo_id,
    privileged_connection,
    seed_demo_identities,
)
from compliance_ai.asset_return import receive_asset
from compliance_ai.benchmark import run_benchmark
from compliance_ai.catalog import load_catalog
from compliance_ai.config import Settings
from compliance_ai.lab import preview
from compliance_ai.mfa_simulator import record_observation
from compliance_ai.rag import KnowledgeSource, ingest
from compliance_ai.simulator import GeneratorConfig, persist


def main() -> None:
    if isinstance(sys.stdout, TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Công cụ phát triển Compliance AI")
    commands = parser.add_subparsers(dest="command", required=True)
    catalog_command = commands.add_parser("validate-catalog", help="Kiểm tra danh mục nghiên cứu")
    catalog_command.add_argument("--config-dir", type=Path, default=Path("configs"))
    commands.add_parser("configure-db-roles", help="Tạo vai trò PostgreSQL giới hạn")
    commands.add_parser("seed-demo-identities", help="Tạo danh tính mô phỏng cục bộ")
    seed_demo = commands.add_parser("seed-demo", help="Tạo dữ liệu ABC mô phỏng")
    seed_demo.add_argument("--seed", default=42, type=int)
    generate = commands.add_parser("generate", help="Tạo doanh nghiệp mô phỏng")
    generate.add_argument("--companies", type=int, default=25)
    generate.add_argument("--seed", default=2026, type=int)
    generate.add_argument("--split", choices=("dev", "test"), default="test")
    mfa = commands.add_parser(
        "demo-mfa-observe", help="Ghi quan sát MFA từ nguồn định danh mô phỏng ABC"
    )
    mfa.add_argument("--employee", required=True)
    mfa.add_argument("--revision", type=int, required=True)
    mfa.add_argument("--registered", choices=("yes", "no"), required=True)
    mfa.add_argument("--enforced", choices=("yes", "no"), required=True)
    asset = commands.add_parser(
        "demo-asset-receive", help="Ghi biên nhận tài sản tại kho mô phỏng ABC"
    )
    asset.add_argument("--employee", required=True)
    asset.add_argument("--asset", type=UUID, required=True)
    asset.add_argument("--ticket", type=UUID, required=True)
    asset.add_argument("--revision", type=int, required=True)
    benchmark = commands.add_parser("benchmark", help="Đo phát hiện trên ca mô phỏng")
    benchmark.add_argument("--methods", default="M1,M2,M3,M4")
    benchmark.add_argument("--split", choices=("dev", "test"), default="test")
    benchmark.add_argument("--mode", choices=("mock", "llm"), default="mock")
    benchmark.add_argument("--limit", type=int, default=None)
    benchmark.add_argument("--max-cases", type=int)
    benchmark.add_argument("--model")
    knowledge = commands.add_parser("knowledge-ingest")
    knowledge.add_argument("--tenant", required=True, type=UUID)
    knowledge.add_argument("--file", required=True, type=Path)
    knowledge.add_argument("--metadata", required=True, type=Path)
    knowledge.add_argument("--confirm-rights", action="store_true")
    for name, flag in (("lab-check", "--read-only"), ("lab-plan", "--dry-run")):
        lab = commands.add_parser(name)
        lab.add_argument("--config", required=True, type=Path)
        lab.add_argument(flag, action="store_true", required=True)
    args = parser.parse_args()
    if args.command == "demo-asset-receive":
        Settings.load()
        try:
            with privileged_connection() as connection:
                receipt = receive_asset(
                    connection,
                    demo_id("abc"),
                    args.employee,
                    args.asset,
                    args.ticket,
                    args.revision,
                )
            print(dumps(receipt, ensure_ascii=False))
        except ValueError as error:
            parser.error(str(error))
    if args.command == "demo-mfa-observe":
        Settings.load()
        try:
            with privileged_connection() as connection:
                result = record_observation(
                    connection,
                    demo_id("abc"),
                    args.employee,
                    args.revision,
                    args.registered == "yes",
                    args.enforced == "yes",
                )
            print(dumps(result, ensure_ascii=False))
        except ValueError as error:
            parser.error(str(error))
    if args.command == "benchmark":
        load_dotenv()
        limit = args.limit if args.limit is not None else (3 if args.mode == "llm" else 25)
        max_cases = (
            args.max_cases if args.max_cases is not None else (6 if args.mode == "llm" else 165)
        )
        model = args.model or getenv("LLM_MODEL", "qwen2.5:1.5b")
        print(
            run_benchmark(
                args.mode, args.split, limit, max_cases, model, tuple(args.methods.split(","))
            ).as_posix()
        )
    if args.command == "knowledge-ingest":
        metadata = KnowledgeSource.model_validate_json(args.metadata.read_bytes())
        count = ingest(args.tenant, args.file, metadata, permit=args.confirm_rights)
        print(f"Đã xử lý {count} đoạn cho tenant đã chọn.")
    if args.command in {"lab-check", "lab-plan"}:
        print(dumps(preview(args.config, dry_run=args.command == "lab-plan"), ensure_ascii=False))
    if args.command in {"seed-demo", "generate"}:
        config = (
            GeneratorConfig(args.seed, 1, None, "demo")
            if args.command == "seed-demo"
            else GeneratorConfig(args.seed, args.companies, None, args.split)
        )
        print(dumps(persist(config), ensure_ascii=False))
    if args.command == "configure-db-roles":
        configure_roles()
    if args.command == "seed-demo-identities":
        seed_demo_identities()
    if args.command == "validate-catalog":
        catalog = load_catalog(args.config_dir)
        print(
            f"{len(catalog.controls)} mã, {len(catalog.criteria)} tiêu chí, "
            f"{len(catalog.scenarios)} họ kịch bản, {len(catalog.policies)} chính sách mẫu "
            "(research_rubric)."
        )


if __name__ == "__main__":
    main()
