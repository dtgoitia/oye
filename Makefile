PROJECT_NAME:=oye
WEBAPP_NAME:=$(PROJECT_NAME)-webapp
API_NAME:=$(PROJECT_NAME)-api-dev

set_up_development_environment:
	@echo ""
	@echo Installing git hooks...
	make install_dev_tools

	@echo ""
	@echo ""
	@echo Installing Python dependencies outside of the container, so that the IDE can detect them
	@# this step is necessary because otherwise docker compose creates a node_modules
	@# folder with root permissions and outside-container build fails
	cd api;~/.pyenv/versions/3.11.2/bin/python -m venv .venv/
	bash api/bin/dev/install_dev_deps

	@echo ""
	@echo ""
	@echo Creating development docker images...
	make rebuild_api

	@echo ""
	@echo ""
	@echo To start api:     make run_api

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
	bash api/bin/dev/lint

test_api:
	docker compose run --rm $(API_NAME) pytest -v .

compile_api_development_dependencies:
	bash api/bin/dev/compile_dev_deps

compile_api_production_dependencies:
	bash api/bin/dev/compile_prod_deps

install_api_development_dependencies:
	bash api/bin/dev/install_dev_deps

rebuild_api:
	docker compose down
	docker image rm $(API_NAME) || (echo "No $(API_NAME) found, all good."; exit 0)
	docker compose build --no-cache $(API_NAME)

shell_into_api_container:
	docker compose run --rm $(API_NAME) /bin/bash

delete_local_db:
	find ./api -maxdepth 1 -type f -name $(DB_PATH) -delete
	touch ./api/$(DB_PATH)
