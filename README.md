# DESKO-CFT machine vision

![Example](http://178.169.86.32:8802/s/cBJ5JEcGyYEycJX)

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