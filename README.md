# trailarr2


# Contributing:

Open the repo in a Dev container by using the badge below:

[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/UNCode101/trailarr2)

If you already have VS Code and Docker installed, you can click the badge above or [here](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/UNCode101/trailarr2) to get started. Clicking these links will cause VS Code to automatically install the Dev Containers extension if needed, clone the source code into a container volume, and spin up a dev container for use.

Make necessary changes and run the test application by running VS Code Task (Ctrl + Shift + P -> Run Task): `fastapi: run`, it will build everything and start Trailarr app at http://localhost:7888

Whenever any changes are made to database models, run

````
alembic revision --autogenerate -m "small comment on what changed"
````

