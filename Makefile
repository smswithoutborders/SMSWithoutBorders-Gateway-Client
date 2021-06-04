# lsb_release -> check versions of linux
# cat /etc/*release
# cat /etc/issue
# cat /etc/issue.net
# cat /etc/lsb-release
SHELL := $(shell which bash)
venv_path=.venv
pip=pip3

CONFIGS_PATH=package/configs
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
	git submodule update --init --recursive

install:install_deps
	# sudo ln -s "$(pwd)" $(INSTALL_PATH)
	sudo cp -rv "$(PWD)" $(INSTALL_PATH)
	if [ -f /etc/debian_version ]; then \
		if [ -f "$(INSTALL_PATH)"/system/debian/deku.service ]; then \
		sudo ln -s "$(INSTALL_PATH)"/install/system/debian/deku.service $(SYSTEMD_PATH)/deku.service; \
		fi \
	fi
	
	if [ -f /etc/manjaro-release ]; then \
		if [ -f "$(INSTALL_PATH)"/system/arch/deku.service ]; then \
		sudo ln -s "$(INSTALL_PATH)"/install/system/arch/deku.service $(SYSTEMD_PATH)/deku.service; \
		fi \
	fi
	sudo systemctl daemon-reload

run: 
	test -f $(SYSTEMD_PATH)/deku.service && \
	sudo systemctl start deku.service && \
	sudo systemctl enable deku.service

remove:
	sudo rm -rv $(INSTALL_PATH)
	sudo rm -v $(SYSTEMD_PATH)/deku.service
	sudo systemctl daemon-reload
	sudo systemctl kill deku.service
	sudo systemctl disable deku.service
