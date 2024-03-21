#!/bin/bash

if [[ "x$1" == "x" ]]; then
	echo "Usage: install.sh PATH_TO_LFRIC"
	exit
fi

LFRIC=$1

if [[ ! -d $LFRIC/infrastructure ]]; then
	echo "'$LFRIC' does not seem to be an LFRic checkout, can't find infrastructure."
	exit
fi

# Copy the fab base class into the infrastructure build directory
cp -r infrastructure $LFRIC

# Copy the script for the miniapps
cp -r miniapps $LFRIC

# Copy the script for lfric_atm
cp -r lfric_atm $LFRIC