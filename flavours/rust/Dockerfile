FROM rust:1.60.0-bullseye

# vim: required by driver.py's write_vim step type, which execs `vim`
# directly with no auto-install. git: common repo-inspection commands.
RUN apt-get update \
    && apt-get install -y --no-install-recommends vim git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
