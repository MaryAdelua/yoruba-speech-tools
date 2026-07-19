FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-devel

ARG VITS_COMMIT=2e561ba58618d021b5b8323d3765880f7e0ecfdb
ARG FAIRSEQ_COMMIT=3d262bb25690e4eb2e7d3c1309b1e9c406ca4b99

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git ffmpeg ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY execution/condition_b/requirements.lock.txt /tmp/requirements.lock.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.lock.txt && \
    python -m pip install --no-cache-dir torchaudio==2.1.2

RUN git clone https://github.com/jaywalnut310/vits.git /opt/vits && \
    git -C /opt/vits checkout "${VITS_COMMIT}" && \
    git clone --filter=blob:none https://github.com/facebookresearch/fairseq.git /opt/fairseq && \
    git -C /opt/fairseq checkout "${FAIRSEQ_COMMIT}"

# The pinned VITS setup.py names the extension "monotonic_align.core" while
# its outer package imports that nested module. Create the package directory
# explicitly so --inplace writes the extension where __init__.py expects it.
RUN cd /opt/vits/monotonic_align && \
    mkdir -p monotonic_align && \
    touch monotonic_align/__init__.py && \
    python setup.py build_ext --inplace && \
    PYTHONPATH=/opt/vits python -c "import monotonic_align"

ENV PYTHONPATH=/opt/vits:/opt/fairseq
WORKDIR /workspace/yoruba-speech-tools

CMD ["python", "execution/condition_b/preflight_environment.py"]
