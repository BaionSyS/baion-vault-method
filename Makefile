.PHONY: verify test lint tutorial links boundary diagnostics release-surface

verify:
	./verify_repo.sh

test:
	PYTHONPATH=src python -m unittest discover -s tests -t . -v

lint:
	PYTHONPATH=src python -m bvm_lint examples/tutorial-vault --strict

tutorial:
	PYTHONDONTWRITEBYTECODE=1 python examples/tutorial-vault/WORKING/tools/run_probe.py --check
	PYTHONDONTWRITEBYTECODE=1 python examples/tutorial-vault/WORKING/tools/run_positive_control.py --check

links:
	python scripts/check_markdown_links.py .

boundary:
	python scripts/check_public_boundary.py .

diagnostics:
	python scripts/check_diagnostic_parity.py .

release-surface:
	python scripts/check_release_surface.py .
