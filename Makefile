RM := rm -rf
PYTHON := uv run
RUFF := $(PYTHON) ruff

PKG_FILES := pyproject.toml
PKG_LOCK := uv.lock
ENV_DIR := .venv
ENV_LOCK := $(ENV_DIR)/pyvenv.cfg

.PHONY: all format lint clean purge test dev

all: venv

format:
	$(RUFF) check --fix
	$(RUFF) format

lint:
	$(RUFF) check
	$(RUFF) format --check

clean:
	$(RM) ./dist ./build ./*.egg-info

purge: clean
	$(RM) -rf $(ENV_DIR)

test:
	$(PYTHON) -m compileall bot

dev:
	$(PYTHON) --env-file=.env.dev -m wcpan.watchdog -- python3 -m bot

venv: $(ENV_LOCK)

$(ENV_LOCK): $(PKG_LOCK)
	uv sync
	touch $@

$(PKG_LOCK): $(PKG_FILES)
	uv lock
	touch $@
