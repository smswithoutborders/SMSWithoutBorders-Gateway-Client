pwd := $(shell pwd)
python=python3
pip=pip3

venv_path=venv
build_path=$(pwd)/installer/files
systemd_path=/usr/lib/systemd/system
path_rabbitmq=third_party/rabbitmq

gateway_state=$(shell systemctl is-active deku_gateway.service)
cluster_state=$(shell systemctl is-active deku_cluster.service)

gen_configs:
	@cp -nv .configs/example.config.ini .configs/config.ini
	@cp -nv .configs/events/example.rules.ini .configs/events/rules.ini
	@cp -nv .configs/isp/example.operators.ini .configs/isp/operators.ini
	@# @cp -nv .configs/extensions/example.config.ini .configs/extensions/config.ini
	@cp -nv .configs/extensions/example.authorize.ini .configs/extensions/authorize.ini
	@cp -nv .configs/extensions/example.labels.ini .configs/extensions/labels.ini
	@cp -nv .configs/extensions/platforms/example.telegram.ini .configs/extensions/platforms/telegram.ini
	@mkdir -p $(build_path)
	@$(python) installer/generate.py

rabbitmq_checks:third_party/rabbitmq/version.lock third_party/rabbitmq/init.sh third_party/rabbitmq/start.sh
	@echo "Checks passed"

init_rabbitmq:
	@$(path_rabbitmq)/init.sh

start_rabbitmq:
	@$(path_rabbitmq)/start.sh

start:start_rabbitmq
	@sudo systemctl start deku_gateway.service
	@echo "Starting gateway service: " $(gateway_state)
	@sudo systemctl start deku_cluster.service
	@echo "Starting cluster service: " $(cluster_state)

init_systemd:
	@if ! [ -L $(systemd_path)/deku_gateway.service ]; then \
		echo "+ Creating Gateway service..."; \
		sudo ln -s $(build_path)/deku_gateway.service $(systemd_path)/deku_gateway.service; \
	fi
	@if ! [ -L $(systemd_path)/deku_cluster.service ]; then \
		echo "+ Creating Cluster service..."; \
		sudo ln -s $(build_path)/deku_cluster.service $(systemd_path)/deku_cluster.service; \
	fi
	@sudo systemctl daemon-reload

install:requirements.txt init_systemd rabbitmq_checks init_rabbitmq
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
	@echo "Disabling services..."
	@if [ "$(systemctl is-enabled deku_gateway.service)" = "enabled" ]; then \
		sudo systemctl disable deku_gateway.service; \
	fi
	@if [ "$(systemctl is-enabled deku_cluster.service)" = "enabled" ]; then \
		sudo systemctl disable deku_cluster.service; \
	fi
	@if [ -L $(systemd_path)/deku_gateway.service ]; then \
		sudo rm -v $(systemd_path)/deku_gateway.service; \
	fi
	@if [ -L $(systemd_path)/deku_cluster.service ]; then \
		sudo rm -v $(systemd_path)/deku_cluster.service; \
	fi
	@sudo systemctl daemon-reload
	@echo "complete"
