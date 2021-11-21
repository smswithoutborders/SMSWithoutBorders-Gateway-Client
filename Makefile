pwd := $(shell pwd)
python=python3
pip=pip3

venv_path=venv
build_path=$(pwd)/installer/files
systemd_path=/usr/lib/systemd/system
path_rabbitmq=third_party/rabbitmq
path_rabbitmq_builds=third_party/rabbitmq/builds

gateway_state=$(shell systemctl is-active deku_gateway.service)
cluster_state=$(shell systemctl is-active deku_cluster.service)
rabbitmq_state=$(shell systemctl is-active deku_rabbitmq.service)

gen_configs:
	@cp -nv .configs/example.config.ini .configs/config.ini
	@cp -nv .configs/events/example.rules.ini .configs/events/rules.ini
	@cp -nv .configs/isp/example.operators.ini .configs/isp/operators.ini
	@# @cp -nv .configs/extensions/example.config.ini .configs/extensions/config.ini
	@cp -nv .configs/extensions/example.authorize.ini .configs/extensions/authorize.ini
	@cp -nv .configs/extensions/example.labels.ini .configs/extensions/labels.ini
	@cp -nv .configs/extensions/platforms/example.telegram.ini .configs/extensions/platforms/telegram.ini
	@mkdir -p $(build_path)
	@mkdir -p $(path_rabbitmq_builds)
	@$(python) installer/generate.py

rabbitmq_checks:third_party/rabbitmq/version.lock third_party/rabbitmq/init.sh
	@echo "Checks passed"

init_rabbitmq:
	@$(path_rabbitmq)/init.sh

start_rabbitmq:init_rabbitmq
	@echo "+ Starting rabbitmq service"
	@sudo systemctl start deku_rabbitmq.service

enable_rabbitmq:
	@sudo systemctl enable deku_rabbitmq.service
	@echo "+ Enabling rabbitmq service"

enable:enable_rabbitmq
	@sudo systemctl enable deku_gateway.service
	@echo "+ Starting gateway service..."
	@sudo systemctl enable deku_cluster.service
	@echo "+ Starting cluster service..."

start:
	@sudo systemctl start deku_gateway.service
	@echo "+ Starting gateway service..."
	@sudo systemctl start deku_cluster.service
	@echo "+ Starting cluster service..."

init_systemd:
	@sudo ln -s $(build_path)/*.service $(systemd_path)/
	@sudo systemctl daemon-reload

install:requirements.txt init_systemd rabbitmq_checks start_rabbitmq
	@$(python) -m virtualenv $(venv_path)
	@( \
		. $(venv_path)/bin/activate; \
		$(pip) install -r requirements.txt \
	)
	@git submodule update --init --recursive
	@echo "completed successfully"

restart:
	@sudo systemctl restart deku_gateway.service
	@systemctl is-active deku_gateway.service
	@sudo systemctl restart deku_cluster.service
	@systemctl is-active deku_cluster.service

clean:
	@#rm -rf $(venv_path)
	@rm -f $(path_rabbitmq)/*.sh

remove:
	@echo "Stopping services..."
	@if [ "$(gateway_state)" = "active" ]; then \
		echo "- gateway"; \
		sudo systemctl kill deku_gateway.service; \
	fi
	@if [ "$(cluster_state)" = "active" ]; then \
		echo "- cluster"; \
		sudo systemctl kill deku_cluster.service; \
	fi
	@if [ "$(rabbitmq_state)" = "active" ]; then \
		echo "- rabbitmq"; \
		sudo systemctl kill deku_rabbitmq.service; \
	fi
	@echo "Disabling services..."
	@if [ "$(systemctl is-enabled deku_gateway.service)" = "enabled" ]; then \
		sudo systemctl disable deku_gateway.service; \
	fi
	@if [ "$(systemctl is-enabled deku_cluster.service)" = "enabled" ]; then \
		sudo systemctl disable deku_cluster.service; \
	fi
	@if [ "$(systemctl is-enabled deku_rabbitmq.service)" = "enabled" ]; then \
		sudo systemctl disable deku_rabbitmq.service; \
	fi
	@sudo rm -rfv $(systemd_path)/deku_*.service
	@sudo rm -rfv $(build_path)
	@sudo rm -rfv $(path_rabbitmq_builds)
	@rm -f $(path_rabbitmq)/*.sh
	@rm -rf rabbitmq_server*
	@sudo systemctl daemon-reload
	@echo "complete"
update:
	@git submodule update --recursive --remote

fuckit:remove clean
	@echo "Alright developer, have a go at it!"

now:gen_configs install
	@echo "Good as new"
