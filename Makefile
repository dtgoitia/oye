PROJECT_NAME:=oye
WEBAPP_NAME:=$(PROJECT_NAME)-webapp
API_NAME:=$(PROJECT_NAME)-api-dev
CLI_NAME:=$(PROJECT_NAME)-cli-dev
EVENT_HANDLER_NAME:=$(PROJECT_NAME)-event-handler-dev

set_up_development_environment:
	@echo ""
	@echo Installing git hooks...
	make install_dev_tools

	@echo ""
	@echo ""
	@echo Installing Python dependencies outside of the container, so that the IDE can detect them
	@# this step is necessary because otherwise docker compose creates a node_modules
	@# folder with root permissions and outside-container build fails
	cli/bin/dev/create_venv
	cli/bin/dev/install_dev_deps
	api/bin/dev/create_venv
	api/bin/dev/install_dev_deps
	event_handler/bin/dev/create_venv
	event_handler/bin/dev/install_dev_deps

	@echo ""
	@echo ""
	@echo Creating development docker images...
	make rebuild_cli
	make rebuild_api
	make rebuild_event_handler

	@echo ""
	@echo ""
	@echo "To start cli:            make run_cli"
	@echo "To start api:            make run_api"
	@echo "To start event handler:  make run_event_handler"

install_dev_tools:
	pre-commit install  # pre-commit is (default)
	pre-commit install --hook-type pre-push

uninstall_dev_tools:
	pre-commit uninstall  # pre-commit is (default)
	pre-commit uninstall --hook-type pre-push



#===============================================================================
#
#   API
#
#===============================================================================

run_api:
	docker compose up $(API_NAME)

lint_api:
	api/bin/dev/lint

test_api:
	docker compose run --rm $(API_NAME) pytest -v .

compile_and_install_api_dev_deps:
	api/bin/dev/compile_prod_deps
	api/bin/dev/compile_dev_deps
	api/bin/dev/install_dev_deps

rebuild_api:
	docker compose down
	docker image rm $(API_NAME) || (echo "No $(API_NAME) found, all good."; exit 0)
	docker compose build --no-cache $(API_NAME)

shell_into_api_container:
	docker compose run --rm $(API_NAME) /bin/bash

#===============================================================================
#
#   CLI v2
#
#===============================================================================

install_cli_globally:
	cli_v2/bin/dev/install_cli_globally

uninstall_cli_globally:
	cli_v2/bin/dev/uninstall_cli_globally

run_cli_v2:
	cli_v2/bin/run

build_cli_v2:
	cli_v2/bin/dev/build

test_cli_v2:
	cli_v2/bin/dev/test

#===============================================================================
#
#   event handler
#
#===============================================================================

run_event_handler:
	docker compose up $(EVENT_HANDLER_NAME)

lint_event_handler:
	event_handler/bin/dev/lint

test_event_handler:
	docker compose run --rm $(EVENT_HANDLER_NAME) pytest -v .

compile_and_install_event_handler_dev_deps:
	event_handler/bin/dev/compile_prod_deps
	event_handler/bin/dev/compile_dev_deps
	event_handler/bin/dev/install_dev_deps

rebuild_event_handler:
	docker compose down
	docker image rm $(EVENT_HANDLER_NAME) || (echo "No $(EVENT_HANDLER_NAME) found, all good."; exit 0)
	docker compose build --no-cache $(EVENT_HANDLER_NAME)

shell_into_event_handler_container:
	docker compose run --rm $(EVENT_HANDLER_NAME) /bin/bash
