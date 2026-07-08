#!/usr/bin/env python3
"""Container entrypoint: chown the bind-mounted data dir, then drop from root
to the unprivileged app user before exec'ing the real command.

A plain Dockerfile `USER` directive isn't enough here: `/backend/data` is a
host bind mount (see docker-compose.yaml), so it keeps whatever ownership the
host directory already has, regardless of what the image sets at build time -
without this, the app user could get a permission error on first write.

Uses a plain setuid/setgid + execvp instead of gosu/su-exec so the image
doesn't need an extra installed tool; execvp performs a real execve, so the
final process still becomes PID 1 with correct signal handling.
"""
import os
import pwd
import sys

APP_USER = "appuser"
DATA_DIR = "/backend/data"


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    pw = pwd.getpwnam(APP_USER)
    for root, dirs, files in os.walk(DATA_DIR):
        os.chown(root, pw.pw_uid, pw.pw_gid)
        for name in dirs + files:
            os.chown(os.path.join(root, name), pw.pw_uid, pw.pw_gid)

    os.environ["HOME"] = pw.pw_dir
    os.initgroups(APP_USER, pw.pw_gid)
    os.setgid(pw.pw_gid)
    os.setuid(pw.pw_uid)

    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
