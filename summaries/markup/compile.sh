#!/bin/bash
# A very simple bash script for running wht compiler, by Tavro

echo Compiling all summaries...
decade=100
suffix='-summary.wht'
until [ $decade -gt 2000 ]
do
	name=$decade$suffix
	python3 wht-compiler.py $name
	((decade += 100))
done
echo Ran compiler script on all files...
echo Done!
