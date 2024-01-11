# Force Raspberry Pi 3 for 32-bit X
FROM balenalib/raspberrypi3:bullseye

RUN apt-get update && apt-get install -y vlc vlc-plugin-* g++ python3-pip python3-setuptools python3-dev build-essential \
  xserver-xorg-core \
  x11-xserver-utils \
  xinit lxsession desktop-file-utils \
  gtk2-engines-clearlookspix \
  matchbox-keyboard \
  # For system volume
  libasound2-dev \
  # Audio
  alsa-utils \
  # Remove cursor
  unclutter \
  python3-pil \
  python3-vlc 

# disable lxpolkit popup warning
RUN mv /usr/bin/lxpolkit /usr/bin/lxpolkit.bak


# Disable screen from turning it off
RUN echo "#!/bin/bash" > /etc/X11/xinit/xserverrc \
  && echo "" >> /etc/X11/xinit/xserverrc \
  && echo 'exec /usr/bin/X -s 0 dpms -nolisten tcp "$@"' >> /etc/X11/xinit/xserverrc

# Enable udevd so that plugged dynamic hardware devices show up in our container.
ENV UDEV 1

# Set dbus environment variables
ENV DBUS_SYSTEM_BUS_ADDRESS unix:path=/host/run/dbus/system_bus_socket

COPY requirements.txt requirements.txt
RUN pip3 install -Ur requirements.txt

COPY . /code/
WORKDIR /code/

COPY *.ogv ./


CMD ["bash","pi.sh"]

