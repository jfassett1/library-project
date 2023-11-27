#!/bin/bash
echo "Refreshing Database"
python ./library_project/initialization/refresh_db.py
echo "Initializing Database"
python ./library_project/initialization/initialize_db.py


$SHELL