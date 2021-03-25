CONFIGS_PATH=src/configs
MYSQL_CONFIGS_PATH=src/libs/configs

CONFIG_FILE=config.ini
EXAMPLE_CONFIG_FILE=example.config.ini

venv_path=.venv

copy_configs:
	cp -iv $(CONFIGS_PATH)/$(EXAMPLE_CONFIG_FILE) $(CONFIGS_PATH)/$(CONFIG_FILE)
	cp -iv $(MYSQL_CONFIGS_PATH)/$(EXAMPLE_CONFIG_FILE) $(MYSQL_CONFIGS_PATH)/$(CONFIG_FILE)

install_dependencies:
	pip install virtualenv

install: install_dependencies $(venv_path)/bin/activate requirements.txt
	. $(venv_path)/bin/activate; \
	pip install -r requirements.txt

reset:
	rm -iv $(CONFIGS_PATH)/$(EXAMPLE_CONFIG_FILE) $(CONFIGS_PATH)/$(CONFIG_FILE)
	rm -iv $(MYSQL_CONFIGS_PATH)/$(EXAMPLE_CONFIG_FILE) $(MYSQL_CONFIGS_PATH)/$(CONFIG_FILE)

