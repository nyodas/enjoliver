CWD=$(shell pwd)
CHECK=check
CHECK_EUID=check_euid
CHECK_EUID_KVM_PLAYER=check_euid_kvm_player
ENV=$(CWD)/env
MY_USER=${SUDO_USER}

default: help

help:
	@echo ----------------------
	@echo Prepare:
	@echo sudo make apt
	@echo ----------------------
	@echo All in one for local usage:
	@echo sudo MY_USER= make dev_setup
	@echo
	@echo All in one for production usage:
	@echo sudo MY_USER= make prod_setup
	@echo ----------------------
	@echo Testing:
	@echo make $(CHECK)
	@echo
	@echo Ready for KVM:
	@echo sudo make $(CHECK_EUID_KVM_PLAYER)
	@echo
	@echo KVM - long:
	@echo sudo make $(CHECK_EUID)
	@echo ----------------------
	@echo Release:
	@echo sudo make aci_enjoliver
	@echo ----------------------

apt:
	test $(shell id -u -r) -eq 0
	DEBIAN_FRONTEND=noninteractive INSTALL="-y" ./apt.sh

$(ENV):
	./virtualenv.sh

pip: $(ENV)
	$(ENV)/bin/pip3 install -U setuptools
	$(ENV)/bin/pip3 install -r requirements.txt
	$(ENV)/bin/pip3 install py-vendor/ipaddr-py/

acserver:
	make -C runtime create_rack0
	test $(shell id -u -r) -eq 0
	# Check if the port is available
	curl 172.20.0.1 && exit 1 || true
	./runtime/runtime.acserver &

aci: acserver
	make -C aci core
	# Find a better way to stop it
	pkill acserver

assets:
	# Self
	make -C matchbox/assets/discoveryC

clean: check_clean
	make -C cni clean
	make -C etcd clean
	make -C fleet clean
	make -C hyperkube clean
	make -C lldp clean
	make -C rkt clean
	make -C vault clean

clean_after_assets:
	make -C discoveryC clean

fclean: clean_after_assets clean check_clean
	rm -Rf $(ENV)
	rm -Rf runtime/acserver.d/*
	rm -Rf runtime/target/*

check_clean:
	make -C app/tests/ fclean

$(CHECK):
	make -C discoveryC/ $(CHECK)
	make -C app/tests/ $(CHECK)

$(CHECK_EUID): validate
	test $(shell id -u -r) -eq 0
	make -C app/tests/ $(CHECK_EUID)

$(CHECK_EUID_KVM_PLAYER):
	test $(shell id -u -r) -eq 0
	make -C app/tests/ $(CHECK_EUID_KVM_PLAYER)

submodules:
	git submodule update --init --recursive

validate:
	@./validate.py

dev_setup_runtime: submodules
	make -C runtime dev_setup

prod_setup_runtime:
	make -C runtime prod_setup

front:
	make -C app/static

config:
	mkdir -pv $(HOME)/.config/enjoliver
	touch $(HOME)/.config/enjoliver/config.env
	touch $(HOME)/.config/enjoliver/config.json

dev_setup:
	echo "Need MY_USER for non root operations and root for dgr"
	test $(MY_USER)
	test $(shell id -u -r) -eq 0
	su - $(MY_USER) -c "make -C $(CWD) submodules"
	su - $(MY_USER) -c "make -C $(CWD) dev_setup_runtime"
	su - $(MY_USER) -c "make -C $(CWD)/app/tests testing.id_rsa"
	su - $(MY_USER) -c "make -C $(CWD) front"
	su - $(MY_USER) -c "make -C $(CWD) pip"
	su - $(MY_USER) -c "make -C $(CWD) assets"
	make -C $(CWD) aci
	make -C $(CWD)/matchbox/assets/coreos
	su - $(MY_USER) -c "make -C $(CWD)/matchbox/assets/coreos serve"
	su - $(MY_USER) -c "make -C $(CWD) validate"
	su - $(MY_USER) -c "make -C $(CWD) config"
	chown -R $(MY_USER): $(CWD)

prod_setup:
	make -C $(CWD) discoveryC
	make -C $(CWD) submodules
	make -C $(CWD) prod_setup_runtime
	make -C $(CWD) front
	make -C $(CWD) pip
	make -C $(CWD) assets
	make -C $(CWD) validate
