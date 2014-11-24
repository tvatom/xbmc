#!/bin/bash
version=`awk -F'"' '/addon id/{print $6}' repository.tvatom.gotham/addon.xml`
z=repository.tvatom.gotham-${version}.zip
if [ ! -e $z ]; then
  zip -r $z repository.tvatom.gotham
  git add $z
  echo "<a href=\"$z\">$z</a><br/>" > repo.html
  git add repo.html
fi
