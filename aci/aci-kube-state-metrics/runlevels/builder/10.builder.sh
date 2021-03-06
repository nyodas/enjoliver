#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -e
set -o pipefail

export LC_ALL=C
export GOPATH=/go
export PATH=${GOPATH}/bin:/usr/local/go/bin:${PATH}

mkdir -pv ${GOPATH}/src/github.com/kubernetes/kube-state-metrics
cd ${GOPATH}/src/github.com/kubernetes/kube-state-metrics

curl -L https://github.com/kubernetes/kube-state-metrics/archive/v${ACI_VERSION}.tar.gz | tar -xzf - --strip-components=1
make build
mv -v kube-state-metrics ${ROOTFS}/usr/bin/kube-state-metrics
