FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libssl-dev git python3-pip pkg-config libcairo2-dev gcc python3-dev \
    libgirepository1.0-dev python3-gst-1.0 gir1.2-gst-plugins-bad-1.0 gstreamer1.0-plugins-bad \
    gstreamer1.0-nice libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev \
    libgstreamer-plugins-bad1.0-dev gstreamer1.0-tools python3-pyee python3-numpy python3-websockets

# Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN cargo install cargo-c

RUN mkdir /src

#Compile gstreamer webrtc plugin.
WORKDIR  /src

RUN git clone -b 0.12.8 --depth 1 https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git
WORKDIR  /src/gst-plugins-rs
RUN cargo cbuild -p gst-plugin-webrtc --prefix=/usr
RUN cargo cinstall -p gst-plugin-webrtc --prefix=/usr


COPY gst-signalling-py /src/gst-signalling-py
WORKDIR  /src/gst-signalling-py

RUN pip install --no-deps --break-system-packages .

WORKDIR  /root
RUN mkdir /root/output

ENTRYPOINT [ "gst-webrtc-video-recorder" ]