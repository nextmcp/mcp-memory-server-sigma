# service_name is replaced at build time
ARG SERVICE_NAME
ARG USERNAME="${SERVICE_NAME}"
ARG WORKDIR="/srv/${USERNAME}"
ARG PYTHON_VERSION="3.12"

FROM amazonlinux:2023 AS base
ARG PYTHON_VERSION
ARG WORKDIR
ARG USERNAME

ENV DNF_PACKAGES="python${PYTHON_VERSION} python${PYTHON_VERSION}-pip util-linux jq"

RUN dnf update -y && \
    dnf install -y ${DNF_PACKAGES} && \
    dnf clean all

RUN mkdir -p ${WORKDIR}

RUN echo "${USERNAME}:x:9001:9001:${USERNAME}:${WORKDIR}:/bin/bash" >> /etc/passwd && \
    echo "${USERNAME}:x:9001:" >> /etc/group && \
    echo "${USERNAME}:*:19387:0:99999:7:::" >> /etc/shadow && \
    echo "${USERNAME}:::" >> /etc/gshadow && \
    chown -R "${USERNAME}:${USERNAME}" "${WORKDIR}" && \
    chmod 2755 "${WORKDIR}" 

SHELL [ "/bin/bash", "-c" ]

FROM base AS builder
ARG WORKDIR
ARG PYTHON_VERSION
ARG USERNAME

USER ${USERNAME}
WORKDIR ${WORKDIR}
COPY src/requirements.txt .
RUN pip${PYTHON_VERSION} install --no-cache-dir --user -r requirements.txt && \
    pip${PYTHON_VERSION} install --no-cache-dir --user ddtrace

FROM base AS requirements-checker
ARG PYTHON_VERSION
ARG REQUIREMENTS_IN="src/requirements.in"
# Install pip-tools to the main lcoation so it doesn't get copied when we copy into the app image
RUN pip${PYTHON_VERSION} install --disable-pip-version-check --root-user-action=ignore --no-cache-dir pip-tools
# Set us up so we can run pip-compile on demand, but not necessarily for every build.
WORKDIR /
ENV CUSTOM_COMPILE_COMMAND="./update_requirements_txt.sh"
COPY ${REQUIREMENTS_IN} .
ENTRYPOINT ["pip-compile", "requirements.in", "--output-file", "compiled-pip-requirements.txt", "--quiet"]

FROM base AS application
ARG SERVICE_NAME
ARG USERNAME
ARG WORKDIR
ARG PYTHON_VERSION

WORKDIR ${WORKDIR}

ENV USERNAME="${USERNAME}"
ENV WORKDIR="${WORKDIR}"
ENV PORT=8000
# set JSON_LOGGING="True" to force json logging
ENV JSON_LOGGING_ENABLED="False"
# set BIND_PUBLIC_HOST="True" to bind uvicorn to 0.0.0.0, otherwise will only bind to localhost and only be accessible via host.docker.internal
ENV BIND_PUBLIC_HOST="False"
ENV PYTHON_VERSION="${PYTHON_VERSION}"
ENV SERVICE_NAME="${SERVICE_NAME}"
ENV DD_SERVICE="${SERVICE_NAME}"
ENV DD_SOURCE=python
ENV DD_TAGS="source:python,service:${SERVICE_NAME}"

ENV PATH=${PATH}:${WORKDIR}/.local/bin

USER ${USERNAME}

COPY --from=builder --chown=${USERNAME}:${USERNAME} ${WORKDIR}/.local ./.local
COPY ./src/th_logging .
COPY ./src/${SERVICE_NAME} .
COPY --chmod=755 ./docker/entrypoint.sh .

EXPOSE ${PORT}
ENTRYPOINT ["./entrypoint.sh"]
