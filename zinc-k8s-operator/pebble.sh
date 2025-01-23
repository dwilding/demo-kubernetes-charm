#!/bin/sh

UNIT="$1"
shift
# Run Pebble in the charm container of the unit, connected to the workload container via the shared socket
juju exec --unit="zinc-k8s/$UNIT" -- PEBBLE_SOCKET=/charm/containers/zinc/pebble.socket /charm/bin/pebble "$@"