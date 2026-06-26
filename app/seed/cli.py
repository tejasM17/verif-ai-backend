import argparse
import json
import sys
from typing import Optional

from app.core.seed_database import (
    counts, drop_all_seed_collections, ensure_seed_indexes,
)
from app.seed.checkpoint import Checkpoint
from app.seed.config import (
    SEED_DATA_DIR, apply_cli_overrides, reload_config, seed_config,
)
from app.seed.logger import get_logger
from app.seed.runners.orchestrator import (
    resume_seed, run_full_seed, status_report,
)

logger = get_logger("seed.cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.seed",
        description="Recruiter Seeding System — generates 5k companies, 50k recruiters, 250k jobs.",
    )
    sub = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--target-companies", type=int, default=None)
    common.add_argument("--target-recruiters", type=int, default=None)
    common.add_argument("--target-jobs", type=int, default=None)
    common.add_argument("--workers", type=int, default=None)
    common.add_argument("--batch-size", type=int, default=None)
    common.add_argument("--skip-firebase", action="store_true")
    common.add_argument("--dry-run", action="store_true")
    common.add_argument("--stage", type=str, default=None, help="Run only this stage then exit")

    p_run = sub.add_parser("run", parents=[common], help="Run all seed stages from scratch")
    p_run.add_argument("--no-firebase", action="store_true", help="Skip Firebase auth import step")
    p_run.add_argument("--rtdb-mirror", action="store_true", help="Mirror recruiter profiles to Firebase RTDB")

    p_resume = sub.add_parser("resume", parents=[common], help="Resume from checkpoint")
    p_resume.add_argument("--no-firebase", action="store_true")

    p_status = sub.add_parser("status", parents=[common], help="Print current checkpoint + collection counts")
    p_rollback = sub.add_parser("rollback", parents=[common], help="Drop all seeded collections and clear checkpoint")
    p_rollback.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    p_verify = sub.add_parser("verify", parents=[common], help="Verify seeded collection counts >= targets")
    p_firebase = sub.add_parser("firebase-sync", parents=[common], help="Run or retry Firebase auth import")
    p_firebase.add_argument("--retry", action="store_true", help="Retry only pending records")

    return parser


def _print_json(obj: dict) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    def _opt(name: str):
        return getattr(args, name, None)

    apply_cli_overrides(
        target_companies=_opt("target_companies"),
        target_recruiters=_opt("target_recruiters"),
        target_jobs=_opt("target_jobs"),
        workers=_opt("workers"),
        batch_size=_opt("batch_size"),
        skip_firebase=bool(_opt("skip_firebase")) or bool(_opt("no_firebase")),
        dry_run=bool(_opt("dry_run")),
        stage_filter=_opt("stage"),
    )
    if getattr(args, "rtdb_mirror", False):
        apply_cli_overrides(rtdb_mirror=True)
    reload_config()

    cmd = args.command or "run"

    if cmd == "run":
        ensure_seed_indexes()
        results = run_full_seed()
        _print_summary(results)
        return 0

    if cmd == "resume":
        results = resume_seed()
        _print_summary(results)
        return 0

    if cmd == "status":
        report = status_report()
        _print_json(report)
        return 0

    if cmd == "rollback":
        if not args.yes:
            print("WARNING: this drops all seeded collections. Pass --yes to skip this prompt.")
            return 2
        dropped = drop_all_seed_collections()
        Checkpoint(seed_config.checkpoint_path).reset()
        print(f"dropped {len(dropped)} collections; checkpoint reset")
        return 0

    if cmd == "verify":
        return _verify()

    if cmd == "firebase-sync":
        from app.seed.firebase.bulk_auth import retry_firebase_auth, run_firebase_auth
        result = retry_firebase_auth() if args.retry else run_firebase_auth()
        _print_summary({"firebase_auth": result})
        return 0

    parser.print_help()
    return 1


def _print_summary(results: dict) -> None:
    print()
    print("=" * 78)
    print(" SEED SUMMARY ".center(78, "="))
    print("=" * 78)
    print(f"{'STAGE':<30} {'STATUS':<12} {'INSERTED':>12} {'FAILED':>10} {'SKIPPED':>10}")
    print("-" * 78)
    for name, stage in results.items():
        if stage is None:
            print(f"{name:<30} {'missing':<12} {0:>12} {0:>10} {0:>10}")
            continue
        print(
            f"{name:<30} {stage.status:<12} {stage.inserted:>12} {stage.failed:>10} {stage.skipped:>10}"
        )
    print("-" * 78)
    try:
        print()
        print(" COLLECTION COUNTS ".center(78, "-"))
        for name, count in counts().items():
            print(f"  {name:<32} {count:>10}")
    except Exception as exc:
        print(f"  (could not fetch counts: {exc})")
    print("=" * 78)
    print(f"checkpoint: {seed_config.checkpoint_path}")
    print(f"logs:       {seed_config.log_path}")
    print(f"errors:     {seed_config.error_log_path}")


def _verify() -> int:
    cfg = seed_config
    targets = {
        "countries": 14,
        "states": 50,
        "cities": 300,
        "skills": cfg.target_skills,
        "companies": cfg.target_companies,
        "recruiters": cfg.target_recruiters,
        "jobs": cfg.target_jobs,
    }
    actual = counts()
    failed = []
    print(f"{'COLLECTION':<30} {'EXPECTED':>12} {'ACTUAL':>12} {'OK':>6}")
    print("-" * 64)
    for coll, target in targets.items():
        actual_count = actual.get(coll, 0)
        ok = actual_count >= target
        if not ok:
            failed.append(coll)
        print(f"{coll:<30} {target:>12} {actual_count:>12} {'YES' if ok else 'NO':>6}")
    if failed:
        print()
        print(f"VERIFY FAILED for: {', '.join(failed)}")
        return 1
    print()
    print("VERIFY OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())