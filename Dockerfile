FROM arm32v7/python:3.7-buster

ENV container docker
ENV LC_ALL C
ENV DEBIAN_FRONTEND noninteractive

# install system packages
RUN apt-get update && apt-get install -y \
    libatlas-base-dev \
    python3-pigpio && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
#RUN pip install pigpio && systemctl enable pigpiod && systemctl start pigpiod
# get pigpio
#RUN git clone https://github.com/joan2937/pigpio.git && \
#    cd pigpio && \
#    make -j6 && \
#    make install
#RUN systemctl enable pigpiod && systemctl start pigpio


#WORKDIR /home/pi/
# Copy vent files to docker
#COPY . pvp_src

ADD vent /pvp_src
ADD setup.py /pvp_src
WORKDIR /pvp_src
RUN pip install .

ENTRYPOINT pigpiod & && python3 -m vent.main --simulation
