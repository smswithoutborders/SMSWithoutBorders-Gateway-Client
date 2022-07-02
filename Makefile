pwd := $(shell pwd)
python=python3
pip=pip3

venv_path=venv
build_path=$(pwd)/installer/files
#
# Not available in arch based distros
# systemd_path=/usr/local/lib/systemd/system
systemd_path=/etc/systemd/system

inbound_state=$(shell systemctl is-active swob_inbound.service)
outbound_state=$(shell systemctl is-active swob_outbound.service)

gen_configs:
	@cp -nv .configs/example.config.ini .configs/config.ini
	@echo "[*] Copied config files..."
	
	@mkdir -p $(build_path)
	@echo "[*] Created dependencies build path $(build_path)"
	@$(python) installer/generate.py
	@echo "[*] Generated service files"


enable:
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
	@sudo ln -s $(build_path)/*.service $(systemd_path)/
	@sudo systemctl daemon-reload
	@echo "[*] Copied service files to $(systemd_path)"

install:requirements.txt init_systemd 
	@$(python) -m venv $(venv_path)
	@( \
		. $(venv_path)/bin/activate; \
		$(pip) install -r requirements.txt \
	)
	@git submodule update --init --recursive --remote
	@echo "[*] Installation completed successfully"

restart:
	@sudo systemctl restart swob_inbound.service
	@systemctl is-active swob_inbound.service
	@sudo systemctl restart swob_outbound.service
	@systemctl is-active swob_outbound.service

clear:
	@rm -f src/services/locks/*.lock
	@rm -f src/services/status/*.ini

clean:
	@sudo rm -f src/services/logs/service.log

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
	@echo "Disabling services..."
	@if [ "$(systemctl is-enabled swob_inbound.service)" = "enabled" ]; then \
		sudo systemctl disable swob_inbound.service; \
	fi
	@if [ "$(systemctl is-enabled swob_outbound.service)" = "enabled" ]; then \
		sudo systemctl disable swob_outbound.service; \
	fi
	@sudo rm -fv $(systemd_path)/swob_*.service
	@rm -rfv $(build_path)
	@sudo systemctl daemon-reload
	@echo "complete"
update:
	@git submodule update --recursive --remote

fuckit:clear remove clean
	@echo "Alright developer, have a go at it!"

now:gen_configs install
	@echo "Good as new"
