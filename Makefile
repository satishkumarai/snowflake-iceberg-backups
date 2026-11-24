ENV ?= dev
.PHONY: lint test it plan apply
lint: ; ruff check src tests && sqlfluff lint sql --dialect snowflake
test: ; pytest -q
it:   ; pytest -q -m integration tests/integration
plan: ; icebackup plan --env $(ENV)
apply:; icebackup apply --env $(ENV)
