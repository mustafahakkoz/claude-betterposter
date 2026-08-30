# betterportraitposter build + pre-print verification.
#
# Tectonic is the default: it is a Homebrew formula, so it installs into
# user-owned /opt/homebrew with no sudo, and resolves LaTeX packages itself.
# Override with `make pdf TEX=latexmk` for a local TeX Live / BasicTeX.

SHELL := /bin/bash
export PATH := /opt/homebrew/bin:/Library/TeX/texbin:$(PATH)

TEX     ?= tectonic
MAIN    ?= main
CHECK   ?= scripts/check_poster.py
CEILING ?= 250

help:  ## Show this help
	@grep -E '^[.a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

pdf:  ## Build the poster
	@if [ "$(TEX)" = "tectonic" ]; then \
	  tectonic -X compile --keep-logs $(MAIN).tex; \
	else \
	  latexmk -pdf $(MAIN).tex; \
	fi

watch:  ## Rebuild on every save
	@if [ "$(TEX)" = "tectonic" ]; then tectonic -X watch; \
	else latexmk -pdf -pvc $(MAIN).tex; fi

clean:  ## Remove auxiliary files (keeps the PDF)
	@command -v latexmk >/dev/null && latexmk -C || true
	rm -f $(MAIN).aux $(MAIN).log $(MAIN).out $(MAIN).fls \
	      $(MAIN).fdb_latexmk $(MAIN).synctex.gz
	find . -type f -name '.DS_Store' -delete

check:  ## All five pre-print checks (size, words, figures, fonts, qr)
	@python3 $(CHECK) --root . --tex $(MAIN).tex --ceiling $(CEILING)

check-%:  ## Run one check, e.g. make check-fonts
	@python3 $(CHECK) --root . --tex $(MAIN).tex --ceiling $(CEILING) --only $*

words:  ## Word count, dumping every word it counted
	@python3 $(CHECK) --root . --tex $(MAIN).tex --only words -v

colors:  ## Sample the colours that ACTUALLY rendered (not the ones you computed)
	@python3 scripts/contrast.py --sample $(MAIN).pdf

tools:  ## Install everything the checks need
	brew install tectonic poppler zbar && python3 -m pip install --user Pillow

.PHONY: help pdf watch clean check words colors tools
