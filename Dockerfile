FROM continuumio/miniconda

COPY environment.yml /

ADD ./data /opt/data

RUN tar -xzvf /opt/data/fdh.sqlite.tar.gz -C /opt/data && \
    conda update -y conda && \
    conda env create -f environment.yml && \
    conda clean -tipsy

# RUN /bin/bash -c "source activate shoreline"

ADD ./bin /

ENV PATH /opt/conda/envs/shoreline/bin:$PATH
