# shoreline-task

This project provides a GBDX task to detect shorelines and predict tides.

To make accessible to GBDX, make sure to add `tdgpdeploy` as a collaborator.

1. Build the Docker image

```console
$ docker build -t venicegeo/shoreline-task .
```

2. Push it to Docker Hub

```console
$ docker push venicegeo/shoreline-task
```

3. Bump task version number and register

- [Registering a task](notebooks/Register-Tide-Task.ipynb)

4. Create and execute a workflow

- [Executing a workflow](notebooks/Tide-Prediction.ipynb)
