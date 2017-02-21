CWD=$(shell pwd)
CHECK=check
CHECK_EUID=check_euid
CHECK_EUID_KVM_PLAYER=check_euid_kvm_player
ENV=$(CWD)/env

default: help

help:
	@echo ----------------------
	@echo Prepare:
	@echo sudo make apt
	@echo ----------------------
	@echo Setup:
	@echo make submodules
	@echo make runner
	@echo sudo make acis
	@echo make assets
	@echo make validate
	@echo
	@echo All in one:
	@echo sudo MY_USER= make setup
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
	@echo sudo make release_aci
	@echo ----------------------

apt:
	test $(shell id -u -r) -eq 0
	DEBIAN_FRONTEND=noninteractive INSTALL="-y" ./apt.sh

$(ENV):
	virtualenv $(ENV) --system-site-packages

pip: $(ENV)
	$(ENV)/bin/pip install -r requirements.txt

acserver:
	test $(shell id -u -r) -eq 0
	# Check if the port is available
	curl 127.0.0.1 && exit 1 || true
	./runtime/runtime.acserver &

acis: acserver
	make -C lldp || pkill acserver && exit 1
	make -C hyperkube || pkill acserver && exit 1
	# Find a better way to stop it
	pkill acserver

assets:
	make -C matchbox/assets/coreos
	make -C matchbox/assets/coreos serve
	make -C matchbox/assets/rkt
	make -C matchbox/assets/rkt serve
	make -C matchbox/assets/etcd
	make -C matchbox/assets/etcd serve
	make -C matchbox/assets/cni
	make -C matchbox/assets/cni serve
	make -C matchbox/assets/fleet
	make -C matchbox/assets/fleet serve
	# Self
	make -C matchbox/assets/discoveryC

clean: check_clean
	make -C matchbox/assets/cni fclean
	make -C matchbox/assets/coreos fclean
	make -C matchbox/assets/discoveryC fclean
	make -C matchbox/assets/hyperkube fclean
	make -C matchbox/assets/lldp fclean
	make -C matchbox/assets/rkt fclean

clean_after_assets:
	rm -v cni/cni.tar.gz
	make -C discoveryC clean
	make -C hyperkube clean
	make -C lldp clean

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

setup_runtime: submodules
	make -C runtime

aci_enjoliver: acserver
	make -C enjoliver test || pkill acserver && exit 1
	# Find a better way to stop it
	pkill acserver

front:
	make -C app/static

config:
	mkdir -pv $(HOME)/.config/enjoliver
	touch $(HOME)/.config/enjoliver/config.env
	touch $(HOME)/.config/enjoliver/config.json

dev_setup:
	echo "Need MY_USER for non root operations"
	test $(MY_USER)
	test $(shell id -u -r) -eq 0
	su - $(MY_USER) -c "make -C $(CWD) submodules"
	su - $(MY_USER) -c "make -C $(CWD) setup_runtime"
	su - $(MY_USER) -c "make -C $(CWD) front"
	su - $(MY_USER) -c "make -C $(CWD) pip"
	make -C $(CWD) acis
	su - $(MY_USER) -c "make -C $(CWD) assets"
	su - $(MY_USER) -c "make -C $(CWD) validate"
	su - $(MY_USER) -c "make -C $(CWD) config"

prod_setup:
	echo "Need MY_USER for non root operations"
	test $(MY_USER)
	test $(shell id -u -r) -eq 0
	su - $(MY_USER) -c "make -C $(CWD) submodules"
	su - $(MY_USER) -c "make -C $(CWD) setup_runtime"
	su - $(MY_USER) -c "make -C $(CWD) front"
	su - $(MY_USER) -c "make -C $(CWD) pip"
	su - $(MY_USER) -c "make -C $(CWD) assets"
	su - $(MY_USER) -c "make -C $(CWD) validate"