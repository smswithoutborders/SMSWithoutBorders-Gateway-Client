pwd := $(shell pwd)
python=python3
pip=pip3

venv_path=venv
build_path=$(pwd)/installer/files
systemd_path=/usr/lib/systemd/system

sys_service:install
	@mkdir -p $(build_path)
	@$(python) installer/generate.py
	@if ! [ -L $(systemd_path)/deku_gateway.service ]; then \
		echo "+ Creating Gateway service..."; \
		sudo ln -s $(build_path)/deku_gateway.service $(systemd_path)/deku_gateway.service; \
	fi
	@if ! [ -L $(systemd_path)/deku_cluster.service ]; then \
		echo "+ Creating Cluster service..."; \
		sudo ln -s $(build_path)/deku_cluster.service $(systemd_path)/deku_cluster.service; \
	fi
	@echo "completed successfully"

install:requirements.txt copy_configs
	@$(python) -m virtualenv $(venv_path)
	@( \
		. $(venv_path)/bin/activate; \
		$(pip) install -r requirements.txt \
	)
	@git submodule update --init --recursive

copy_configs:
	@cp -nv .configs/example.config.ini .configs/config.ini
	@cp -nv .configs/events/example.rules.ini .configs/events/rules.ini
	@cp -nv .configs/isp/example.operators.ini .configs/isp/operators.ini
	@# @cp -nv .configs/extensions/example.config.ini .configs/extensions/config.ini
	@cp -nv .configs/extensions/example.authorize.ini .configs/extensions/authorize.ini
	@cp -nv .configs/extensions/example.labels.ini .configs/extensions/labels.ini
	@cp -nv .configs/extensions/platforms/example.telegram.ini .configs/extensions/platforms/telegram.ini

remove:
	@rm -rf $(venv_path)
	@sudo rm -v $(systemd_path)/deku*.service
	@sudo systemctl daemon-reload
	@sudo systemctl kill deku.service
	@sudo systemctl disable deku.service
	@echo "complete"
