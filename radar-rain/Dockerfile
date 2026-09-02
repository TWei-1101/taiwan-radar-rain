FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION
ARG BUILD_ARCH

RUN apk add --no-cache \
    python3 \
    py3-httpx \
    py3-numpy \
    py3-paho-mqtt

COPY rootfs /

RUN chmod a+x /run.sh

LABEL \
    io.hass.name="Taiwan Radar Rain" \
    io.hass.description="CWA radar rain detection and Home Assistant MQTT sensors" \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}"

CMD ["/run.sh"]
