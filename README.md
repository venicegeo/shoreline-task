# dg-shoreline-task

This project provides a GBDX task to detect shorelines and predict tides.

To build the image.

```bash
$ docker build -t dg-shoreline-task .
```

To make accessible to GBDX, make sure to add `tdgpdeploy` as a collaborator.

Jupyter notebooks are available in the `notebooks` folder. We have one for
registering the new task (this could be a script too), and another for creating
and executing a workflow that uses the task.

- [Registering a task](notebooks/Register-Tide-Task.ipynb)
- [Executing a workflow](notebooks/Tide-Prediction.ipynb)
