FROM debian:bookworm-slim
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends asterisk asterisk-modules ca-certificates && rm -rf /var/lib/apt/lists/*
EXPOSE 5060/udp 10000-10100/udp
CMD ["asterisk","-f","-vvv"]
