"""Run one build notification from the command line."""

import argparse

from devtools_notifications import InfraiRealtime, new_build, publish_build


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a developer build notification")
    parser.add_argument("project")
    parser.add_argument("commit")
    parser.add_argument("--status", choices=["succeeded", "failed"], default="succeeded")
    parser.add_argument("--actor", default="local-developer")
    parser.add_argument("--account-id", default="developer-tools")
    args = parser.parse_args()
    result = publish_build(InfraiRealtime(), new_build(args.project, args.commit, args.status, args.actor), args.account_id)
    print(result["data"])


if __name__ == "__main__":
    main()

