#!/bin/sh

# Helper script to run Pebble as a client connected to the Pebble daemon in the workload container.
# For example:
# ```
# $ ./pebble.sh zinc-k8s/0 services
# Service  Startup  Current  Since
# zinc     enabled  active   today at 02:59 UTC
# ```

UNIT="$1"
shift
juju ssh "$UNIT" PEBBLE_SOCKET=/charm/containers/zinc/pebble.socket /charm/bin/pebble "$@"