

BIND_TO?=0.0.0.0
BIND_PORT?=8000

MANAGE=python manage.py
GAE_SDK_ROOT=python /usr/local/google_appengine
TEST=$(MANAGE) test $(TEST_OPTIONS)

# targets
.PHONY: manage run mailserver first_syncdb syncdb shell test test_with_coverage clean migrate init_migrate loaddata help


run:
	@echo Starting ...
	$(MANAGE) runserver $(BIND_TO):$(BIND_PORT)

mailserver:
	python -m smtpd -n -c DebuggingServer 0.0.0.0:1025

syncdb:
	@echo Syncing...
	$(MANAGE) syncdb
	@echo Done

update:
	@echo Deploy .....
	$(GAE_SDK_ROOT)/appcfg.py update .

update_indexes:
	@echo Deploy .....
	$(GAE_SDK_ROOT)/appcfg.py update_indexes .

rshell:
	@echo Remote shell .....
	"$(GAE_SDK_ROOT)/remote_api_shell.py -s qwetqwtrqqwtewqr.appspot.com"

rem_create_superuser:
	python manage.py remote create_superuser


