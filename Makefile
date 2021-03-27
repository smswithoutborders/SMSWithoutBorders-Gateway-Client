SHELL := /usr/bin/bash
venv_path=.venv
pip=pip3

CONFIGS_PATH=configs
INSTALL_PATH=/usr/local/bin/deku
SYSTEMD_PATH=/usr/lib/systemd/system

EXAMPLE_CONFIG_FILE=example.config.ini
EXAMPLE_CONFIG_MYSQL_FILE=example.config.mysql.ini

CONFIG_FILE=config.ini
CONFIG_MYSQL_FILE=config.mysql.ini

PWD := $(shell pwd)

copy_configs:
	cp -iv $(CONFIGS_PATH)/$(EXAMPLE_CONFIG_FILE) $(CONFIGS_PATH)/$(CONFIG_FILE)
	cp -iv $(CONFIGS_PATH)/$(EXAMPLE_CONFIG_MYSQL_FILE) $(CONFIGS_PATH)/$(CONFIG_MYSQL_FILE)

install_deps:requirements.txt
	sudo $(pip) install -r requirements.txt
install:install_deps
	# sudo ln -s "$(pwd)" $(INSTALL_PATH)
	sudo cp -rv "$(PWD)" $(INSTALL_PATH)
	sudo ln -s "$(INSTALL_PATH)"/system/deku.service $(SYSTEMD_PATH)/ 
	sudo systemctl daemon-reload

run: 
	test -f $(SYSTEMD_PATH)/deku.service && \
	sudo systemctl start deku.service

remove:
	sudo rm -rv $(INSTALL_PATH)
	sudo rm -v $(SYSTEMD_PATH)/deku.service
	sudo systemctl daemon-reload
	sudo systemctl kill deku.service
	sudo systemctl disable deku.service
