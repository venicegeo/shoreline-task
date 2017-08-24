FROM continuumio/miniconda

COPY environment.yml /

ADD ./data /opt/data

RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends build-essential

RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends libcurl4-openssl-dev

RUN tar -xzvf /opt/data/fdh.sqlite.tar.gz -C /opt/data

RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends libssl-dev

RUN conda update -y conda && \
    conda env create -f environment.yml && \
    conda clean -tipsy

# RUN /bin/bash -c "source activate shoreline"

ADD ./bin /

ENV PATH /opt/conda/envs/shoreline/bin:$PATH
