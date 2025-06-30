
.PHONY: run
run:
	@echo "Running the program..."
	. venv/bin/activate && python3 arbor_message_forwarder.py

.PHONY: debug_run
debug_run:
	make mark_last_not_forwarded
	make run

.PHONY: mark_last_not_forwarded
mark_last_not_forwarded:
	@echo "Marking last message as not forwarded in the database..."
	# load the DATABASE_PATH from the .env file
	. ./.env && \
	sqlite3 "$$DATABASE_PATH" 'UPDATE messages SET forwarded=0 WHERE rowid=(SELECT MAX(rowid) FROM messages);'

.PHONY: sqlite
sqlite:
	@echo "Opening SQLite database..."
	# load the DATABASE_PATH from the .env file
	. ./.env && \
	sqlite3 "$$DATABASE_PATH"

.PHONY: install-crontab
install-crontab:
	@echo "Installing crontab..."
	EDITOR="$$PWD/crontab-editor.sh"; PPWD="$$PWD"; export EDITOR PPWD; crontab -e
	@echo "Crontab installed; new crontab:"
	crontab -l

.PHONY: install
install: mrproper
	python3.10 -m venv venv
	. venv/bin/activate && ( \
            pip install -r requirements.txt \
        )

.PHONY: mrproper
mrproper:
	rm -rf venv/