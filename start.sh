#!/bin/bash

echo "starting..."

cd src
/usr/local/bin/python run.py

tail -f /dev/null