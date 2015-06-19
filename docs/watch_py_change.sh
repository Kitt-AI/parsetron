#! /bin/sh
# pip install watchdog
watchmedo shell-command --patterns="*.py" --command='make html' -w ../parsetron
