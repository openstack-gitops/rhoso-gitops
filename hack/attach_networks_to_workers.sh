#!/usr/bin/env bash
STACKNAME=${STACKNAME:-stackops}
for net in ctlplane internalapi storage tenant
do
  # for each node add a network
  for node in $(oc get nodes -l node-role.kubernetes.io/worker -o jsonpath="{.items[*].metadata.name}")
  do
    echo "Adding $net to $node"
    openstack server add network "$node" "$STACKNAME-$net" ; sleep 2
  done

  # give the API a bit of a breather
  echo "Let API and network attach catch up (20 seconds)"
  sleep 20

  # look at what networks were added
  echo "-- Networks added for $net"
  for node in $(oc get nodes -l node-role.kubernetes.io/worker -o jsonpath="{.items[*].metadata.name}")
  do
    echo -e "$node: $(oc get nns "$node" -o jsonpath='{.status.currentState.interfaces[*].name}')\n"
  done
done
