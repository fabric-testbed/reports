#!/bin/sh
# Ensure the log directory is writable by appuser (UID 10001)
# when /var/log/mcp is a bind-mounted host volume.
if [ -d /var/log/mcp ]; then
    chown -R appuser:appuser /var/log/mcp 2>/dev/null || true
fi

exec gosu appuser "$@"
