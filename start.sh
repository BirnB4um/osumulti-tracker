#!/bin/bash

echo "starting..."

cd src
/usr/local/bin/python API.py &
/usr/local/bin/python run.py
