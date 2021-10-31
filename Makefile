python=python3
pip=pip3
venv_path := $$HOME/.virtualenvs/deku
configs:
	cp .configs/example.config.ini .configs/config.ini
	cp .configs/events/example.rules.ini .configs/events/rules.ini
	cp .configs/isp/example.operators.ini .configs/isp/operators.ini
	cp .configs/extensions/example.config.ini .configs/extensions/config.ini
	cp .configs/extensions/example.authorize.ini .configs/extensions/authorize.ini
	cp .configs/extensions/example.labels.ini .configs/extensions/labels.ini
	cp .configs/extensions/platforms/example.telegram.ini .configs/extensions/platforms/telegram.ini
	git submodule update --init --recursive

install:configs
	$(python) -m virtualenv $(venv_path)
	( \
		. $(venv_path)/bin/activate; \
		$(pip) install -r requirements.txt \
	)

reset:configs


uninstall:
	rm -rf $(venv_path)
	# rm -rf .configs
