plugin.video.tvatom_tv_subscriber/addon.xml.md5: plugin.video.tvatom_tv_subscriber/addon.xml plugin.video.tvatom_tv_subscriber/default.py plugin.video.tvatom_tv_subscriber/resources/settings.xml
	openssl md5 plugin.video.tvatom_tv_subscriber/addon.xml |cut -d ' ' -f2 > plugin.video.tvatom_tv_subscriber/addon.xml.md5
	git add plugin.video.tvatom_tv_subscriber/addon.xml plugin.video.tvatom_tv_subscriber/addon.xml.md5
	./addons_xml_generator.py
	mkdir -p ../zip/plugin.video.tvatom_tv_subscriber/ 2>/dev/null
	zip -r ../zip/plugin.video.tvatom_tv_subscriber/plugin.video.tvatom_tv_subscriber-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_tv_subscriber/addon.xml`.zip plugin.video.tvatom_tv_subscriber
	git add ../zip/plugin.video.tvatom_tv_subscriber/plugin.video.tvatom_tv_subscriber-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_tv_subscriber/addon.xml`.zip
	git commit -a --allow-empty-message -m "plugin.video.tvatom_tv_subscriber-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_tv_subscriber/addon.xml`"

addons.xml.md5: addons.xml
	./addons_xml_generator.py

