# DESKO-CFT machine vision

![Example](http://178.169.86.32:8802/apps/files_sharing/publicpreview/cBJ5JEcGyYEycJX?x=1871&y=631&a=true&file=viber%2520image%25202021-02-05%2520%252C%252009.13.23.jpg&scalingup=0)
![Example-ui](http://178.169.86.32:8802/s/Tc74L3qaWERbXtd/download)

#### Конфигурация виртуального VNC дисплея Jetson Xavier NX:

```
# Setting resolution:
Section "Screen"
   Identifier    "Default Screen"
   Monitor        "Configured Monitor"
   Device        "Default Device"
   SubSection "Display"
       Depth    24
       Virtual 1024 748
   EndSubSection
EndSection
```