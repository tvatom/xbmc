plugin.video.tvatom_tv_subscriber/addon.xml.md5: plugin.video.tvatom_tv_subscriber/addon.xml
	openssl md5 plugin.video.tvatom_tv_subscriber/addon.xml |cut -d ' ' -f2 > plugin.video.tvatom_tv_subscriber/addon.xml.md5
	git add plugin.video.tvatom_tv_subscriber/addon.xml plugin.video.tvatom_tv_subscriber/addon.xml.md5
	./addons_xml_generator.py
	git commit -a --allow-empty-message -m ""

addons.xml.md5: addons.xml
	./addons_xml_generator.py

