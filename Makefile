CONFIGS_PATH=configs

EXAMPLE_CONFIG_FILE=example.config.ini
EXAMPLE_CONFIG_MYSQL_FILE=example.config.mysql.ini

CONFIG_FILE=config.ini
CONFIG_MYSQL_FILE=config.mysql.ini


venv_path=.venv

copy_configs:
	cp -iv $(CONFIGS_PATH)/$(EXAMPLE_CONFIG_FILE) $(CONFIGS_PATH)/$(CONFIG_FILE)
	cp -iv $(CONFIGS_PATH)/$(EXAMPLE_CONFIG_MYSQL_FILE) $(CONFIGS_PATH)/$(CONFIG_MYSQL_FILE)

install_deps:
	pip install virtualenv

install: requirements.txt install_deps
	virtualenv $(venv_path); \
	. $(venv_path)/bin/activate; \
	pip install -r requirements.txt; \
	deactivate

reset:
	rm -iv $(CONFIGS_PATH)/$(EXAMPLE_CONFIG_FILE) $(CONFIGS_PATH)/$(CONFIG_FILE)
	rm -iv $(MYSQL_CONFIGS_PATH)/$(EXAMPLE_CONFIG_FILE) $(MYSQL_CONFIGS_PATH)/$(CONFIG_FILE)
