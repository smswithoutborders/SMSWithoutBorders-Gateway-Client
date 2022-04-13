pwd := $(shell pwd)
python=python3
pip=pip3

venv_path=venv
build_path=$(pwd)/installer/files
#
# Not available in arch based distros
# systemd_path=/usr/local/lib/systemd/system
systemd_path=/etc/systemd/system

path_rabbitmq=deps/rabbitmq
path_rabbitmq_builds=deps/rabbitmq/builds

inbound_state=$(shell systemctl is-active swob_inbound.service)
outbound_state=$(shell systemctl is-active swob_outbound.service)
rabbitmq_state=$(shell systemctl is-active swob_rabbitmq.service)

gen_configs:
	@echo "Copying config files..."
	@cp -nv .configs/example.config.ini .configs/config.ini
	@cp -nv .configs/events/example.rules.ini .configs/events/rules.ini
	@cp -nv .configs/isp/example.operators.ini .configs/isp/operators.ini
	@# @cp -nv .configs/extensions/example.config.ini .configs/extensions/config.ini
	@cp -nv .configs/extensions/example.authorize.ini .configs/extensions/authorize.ini
	@cp -nv .configs/extensions/example.labels.ini .configs/extensions/labels.ini
	@cp -nv .configs/extensions/platforms/example.telegram.ini .configs/extensions/platforms/telegram.ini
	@cp -nv .configs/remote_control/example.remote_control_auth.ini .configs/remote_control/remote_control_auth.ini
	@ln -s -f ../../.configs/pre-commit .git/hooks/pre-commit
	
	@echo "Creating deps build path $(build_path)"
	@mkdir -p $(build_path)
	@echo "Creating rabbitmq build path $(path_rabbitmq_builds)"
	@mkdir -p $(path_rabbitmq_builds)
	@echo "Generating service files"
	@$(python) installer/generate.py
	@echo "Compiling binaries..."
	@mkdir -p src/bins
	@gcc src/seeders.c -o src/bins/seeders.bin 
	@echo "Done configuration"

ubuntu:
	@echo "[*] Installing wget"
	@sudo apt install wget
	@echo "[*] Adding key.."
	@wget -O- https://packages.erlang-solutions.com/ubuntu/erlang_solutions.asc | sudo apt-key add -
	@echo "deb https://packages.erlang-solutions.com/ubuntu focal contrib" | sudo tee /etc/apt/sources.list.d/erlang-solution.list
	@sudo apt update
	@echo "[*] Installing erlang dependencies"
	@sudo apt-get install -y erlang-base \
                        erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets \
                        erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key \
                        erlang-runtime-tools erlang-snmp erlang-ssl \
                        erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl
	

rabbitmq_checks:deps/rabbitmq/version.lock deps/rabbitmq/init.sh
	@echo "rabbitmq checks passed"

init_rabbitmq:
	@$(path_rabbitmq)/init.sh

start_rabbitmq:init_rabbitmq
	@echo "+ Starting rabbitmq service"
	@sudo systemctl start swob_rabbitmq.service

enable_rabbitmq:
	@sudo systemctl enable swob_rabbitmq.service
	@echo "+ Enabling rabbitmq service"

enable:enable_rabbitmq
	@sudo systemctl enable swob_inbound.service
	@echo "+ Starting gateway service..."
	@sudo systemctl enable swob_outbound.service
	@echo "+ Starting cluster service..."

start:
	@sudo systemctl start swob_inbound.service
	@echo "+ Starting gateway service..."
	@sudo systemctl start swob_outbound.service
	@echo "+ Starting cluster service..."

init_systemd:
	@echo "copying service files to $(systemd_path)"
	@sudo ln -s $(build_path)/*.service $(systemd_path)/
	@sudo systemctl daemon-reload

install:requirements.txt init_systemd rabbitmq_checks start_rabbitmq
	@$(python) -m venv $(venv_path)
	@( \
		. $(venv_path)/bin/activate; \
		$(pip) install -r requirements.txt \
	)
	@git submodule update --init --recursive
	@echo "completed successfully"

restart:
	@sudo systemctl restart swob_inbound.service
	@systemctl is-active swob_inbound.service
	@sudo systemctl restart swob_outbound.service
	@systemctl is-active swob_outbound.service

clear:
	@rm -f src/services/locks/*.lock
	@rm -f src/services/status/*.ini

clean:
	@#rm -rf $(venv_path)
	@rm -f $(path_rabbitmq)/*.sh
	@rm -f src/services/logs/service.log

remove:
	@echo "Stopping services..."
	@if [ "$(inbound_state)" = "active" ]; then \
		echo "- gateway"; \
		sudo systemctl kill swob_inbound.service; \
	fi
	@if [ "$(outbound_state)" = "active" ]; then \
		echo "- cluster"; \
		sudo systemctl kill swob_outbound.service; \
	fi
	@if [ "$(rabbitmq_state)" = "active" ]; then \
		echo "- rabbitmq"; \
		sudo systemctl kill swob_rabbitmq.service; \
	fi
	@echo "Disabling services..."
	@if [ "$(systemctl is-enabled swob_inbound.service)" = "enabled" ]; then \
		sudo systemctl disable swob_inbound.service; \
	fi
	@if [ "$(systemctl is-enabled swob_outbound.service)" = "enabled" ]; then \
		sudo systemctl disable swob_outbound.service; \
	fi
	@if [ "$(systemctl is-enabled swob_rabbitmq.service)" = "enabled" ]; then \
		sudo systemctl disable swob_rabbitmq.service; \
	fi
	@sudo rm -fv $(systemd_path)/swob_*.service
	@rm -rfv $(build_path)
	@rm -rfv $(path_rabbitmq_builds)
	@rm -f $(path_rabbitmq)/*.sh
	@rm -rf rabbitmq_server*
	@rm -rf src/bins
	@sudo systemctl daemon-reload
	@echo "complete"
update:
	@git submodule update --recursive --remote

fuckit:remove clean
	@echo "Alright developer, have a go at it!"

now:gen_configs install
	@echo "Good as new"
