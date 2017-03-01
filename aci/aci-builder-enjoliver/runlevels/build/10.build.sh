#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y -q curl python3.5 python3-dev build-essential python-virtualenv git file openssh-client tar npm libpq-dev
ln -vs /usr/lib/python2.7/dist-packages/virtualenv.py /usr/local/bin/virtualenv
chmod +x /usr/local/bin/virtualenv

go version
