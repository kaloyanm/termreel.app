FROM rust:1.60.0-bullseye

# vim: required by driver.py's write_vim step type, which execs `vim`
# directly with no auto-install. git: common repo-inspection commands.
# curl/ca-certificates: fetch the presenterm release binary below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends vim git curl ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# presenterm: required by driver.py's presenterm step type, which execs
# `presenterm` directly with no auto-install. Installed from a prebuilt
# musl release binary rather than `cargo install` - sidesteps this base
# image's 2022-era Rust toolchain (possible MSRV mismatch) and avoids the
# glibc-version coupling a -unknown-linux-gnu binary would have against
# bullseye's older glibc. Pinned to a specific release for reproducible
# builds. Hardcodes x86_64, matching the rest of this repo's flavours -
# not arch-aware.
ARG PRESENTERM_VERSION=0.16.1
RUN curl -fsSL -o /tmp/presenterm.tar.gz \
      "https://github.com/mfontanini/presenterm/releases/download/v${PRESENTERM_VERSION}/presenterm-${PRESENTERM_VERSION}-x86_64-unknown-linux-musl.tar.gz" \
    && tar -xzf /tmp/presenterm.tar.gz -C /tmp \
    && mv "/tmp/presenterm-${PRESENTERM_VERSION}/presenterm" /usr/local/bin/presenterm \
    && rm -rf /tmp/presenterm.tar.gz "/tmp/presenterm-${PRESENTERM_VERSION}" \
    && presenterm --version
