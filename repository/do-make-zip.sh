#!/bin/bash
version=`awk -F'"' '/addon id/{print $6}' repository.tvatom.gotham/addon.xml`
[ -e repository.tvatom.gotham-${version}.zip ] && exit
zip -r repository.tvatom.gotham-${version}.zip repository.tvatom.gotham
git add repository.tvatom.gotham-${version}.zip
