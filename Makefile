.PHONY: run
run:
	@echo "Running the program..."
	. venv/bin/activate && python3 arbor_message_forwarder.py

.PHONY: install-crontab
install-crontab:
	@echo "Installing crontab..."
	EDITOR="$$PWD/crontab-editor.sh"; PPWD="$$PWD"; export EDITOR PPWD; crontab -e
	@echo "Crontab installed; new crontab:"
	crontab -l