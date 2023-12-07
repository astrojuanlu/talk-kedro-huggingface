FROM axonasif/workspace-python:debug2

RUN pyenv install 3.11.3 \
    && pyenv global 3.11.3

RUN wget https://dl.min.io/server/minio/release/linux-amd64/archive/minio_20231120224007.0.0_amd64.deb -O minio.deb \
    && sudo dpkg -i minio.deb

RUN wget https://dl.min.io/client/mc/release/linux-amd64/mc \
    && chmod +x mc \
    && sudo mv mc /usr/local/bin/mc
