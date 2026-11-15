from __future__ import annotations
import argparse, logging
from . import __version__
from .db import initialize, connect
from .logging_setup import configure_logging
from .repositories import add_repository, list_repositories
from .capabilities import add_capability, list_capabilities
from .discovery import search_github

def build_parser():
    parser=argparse.ArgumentParser(prog="hive",description="HIVE software capability registry")
    parser.add_argument("--version",action="version",version=f"HIVE {__version__}")
    sub=parser.add_subparsers(dest="command")
    sub.add_parser("init",help="Initialize the local HIVE database")
    sub.add_parser("status",help="Show local HIVE database status")
    repo=sub.add_parser("repo",help="Manage repositories")
    rs=repo.add_subparsers(dest="repo_command",required=True)
    add=rs.add_parser("add",help="Add a GitHub repository URL"); add.add_argument("url")
    rs.add_parser("list",help="List registered repositories")
    discover=sub.add_parser("discover",help="Search GitHub and save repository metadata")
    discover.add_argument("query"); discover.add_argument("--limit",type=int,default=10)
    cap=sub.add_parser("capability",help="Manage capability records")
    cs=cap.add_subparsers(dest="cap_command",required=True)
    ca=cs.add_parser("add"); ca.add_argument("repository_id",type=int); ca.add_argument("name")
    ca.add_argument("--description"); ca.add_argument("--evidence-level",
      choices=sorted(["claimed","inferred","build_verified","test_verified","benchmarked"]),default="claimed")
    ca.add_argument("--evidence"); cs.add_parser("list")
    return parser

def main(argv=None):
    configure_logging(); parser=build_parser(); args=parser.parse_args(argv)
    if args.command=="init":
        print(f"HIVE database initialized: {initialize()}")
    elif args.command=="status":
        path=initialize()
        with connect() as c:
            repos=c.execute("SELECT COUNT(*) FROM repositories").fetchone()[0]
            caps=c.execute("SELECT COUNT(*) FROM capabilities").fetchone()[0]
        print(f"HIVE {__version__}\nDatabase: {path}\nRepositories: {repos}\nCapabilities: {caps}")
    elif args.command=="repo" and args.repo_command=="add":
        initialize(); print(f"Repository saved with ID {add_repository(args.url)}")
    elif args.command=="repo" and args.repo_command=="list":
        initialize(); rows=list_repositories()
        if not rows: print("No repositories registered.")
        for r in rows:
            print(f"[{r['id']}] {r['owner']}/{r['name']} | {r['language'] or 'unknown'} | stars={r['stars'] if r['stars'] is not None else 'unknown'} | {r['url']}")
    elif args.command=="discover":
        initialize()
        try:
            results=search_github(args.query,args.limit); print(f"Saved {len(results)} repositories:")
            for r in results: print(f"[{r['id']}] {r['full_name']} | {r['language'] or 'unknown'} | stars={r['stars']}")
        except Exception as exc:
            logging.exception("GitHub discovery failed"); parser.exit(1,f"Discovery failed: {exc}\n")
    elif args.command=="capability" and args.cap_command=="add":
        initialize()
        try: print(f"Capability saved with ID {add_capability(args.repository_id,args.name,args.description,args.evidence_level,args.evidence)}")
        except ValueError as exc: parser.error(str(exc))
    elif args.command=="capability" and args.cap_command=="list":
        initialize(); rows=list_capabilities()
        if not rows: print("No capabilities registered.")
        for r in rows: print(f"[{r['id']}] repo={r['repository_id']} {r['owner']}/{r['repository']} | {r['name']} | {r['evidence_level']} | {r['evidence'] or 'no evidence recorded'}")
    else: parser.print_help()

if __name__=="__main__": main()
