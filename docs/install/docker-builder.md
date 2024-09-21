# Docker Builder

UNDER CONSTRUCTION - COMING SOON!

Use this tool to build the docker compose / docker cli command for running Trailarr app that works with your setup.

## Instructions

1. Select whether you want to use Trailarr with Docker Compose or Docker CLI.
2. Choose the operating system you are using to run Docker.
3. Select whether you want to connect Radarr to Trailarr.
    1. 
4. Select whether you want to connect Sonarr to Trailarr.

## Inputs

### Docker

Do you want to use Trailarr with Docker Compose or Docker CLI?

<input type="radio" id="docker-compose" name="docker" value="docker-compose" checked>
<label for="docker-compose">Docker Compose</label>
<input type="radio" id="docker-cli" name="docker" value="docker-cli">
<label for="docker-cli">Docker CLI</label><br>

<div id="docker-cli-selected" class="d-none" markdown>

???+ tip "Docker Compose Recommended"
    It is recommended to use Docker Compose to run the application, as it makes updating easier. See the [Docker Compose](./docker-compose.md) guide for more information.

</div>

### Operating System
Which operating system are you using to run Docker?

<input type="radio" id="linux" name="os" value="linux" checked>
<label for="linux">Linux</label>
<input type="radio" id="windows" name="os" value="windows">
<label for="windows">Windows</label><br>

??? tip "Unraid/Mac"
    If you are using Mac or Unraid, select Linux as the operating system.


### Radarr

- Do you want to connect Radarr to Trailarr?

    <input type="radio" id="radarr-yes" name="radarr" value="yes">
    <label for="radarr-yes">Yes</label>
    <input type="radio" id="radarr-no" name="radarr" value="no" checked>
    <label for="radarr-no">No</label><br>

    <!-- Radarr Details -->
    <div id="radarr-container" class="d-none">

    - Are you running Radarr as a Docker container?

    <div class="container">
    <input type="radio" id="radarr-docker" name="radarr-docker" value="yes" checked>
    <label for="radarr-docker">Yes</label>
    <input type="radio" id="radarr-direct" name="radarr-docker" value="no">
    <label for="radarr-direct">No</label><br>
    </div>

    <!-- Radarr as Container -->
    <div id="radarr-docker-container">

    - Where is your Radarr Media stored on the local system?

    <div class="container">
    _This is the path to the Movies folder that you can open in your file explorer._<br>
    <label for="local-path-radarr">Local Path:</label>
    <input type="text" id="local-path-radarr" name="radarr-path" class="media-path" placeholder="/mnt/disk1/media/movies" spellcheck="false" autocorrect="off"><br>
    </div>

    - Where is your Radarr media stored inside the container?

    <div class="container">
    _This is the path to the Movies folder inside your Radarr container. Also known as the Radarr Root Folder._<br>
    <label for="container-path-radarr">Container Path:</label>
    <input type="text" id="container-path-radarr" name="radarr-path" class="media-path" placeholder="/media/movies"><br>
    </div>

    ??? example
        For example, if you have volumes mapped in your docker command like:
        ```yaml
        /mnt/disk1/media/movies:/media/movies
        ```
        Then the `Local Path` should be:
        ```yaml
        /mnt/path/to/movies
        ```
        And the `Container Path` should be:
        ```yaml
        /media/movies
        ```
    </div>
    <!-- END - Radarr as container -->

    <!-- Radarr on Host -->
    <div id="radarr-direct-container" class="d-none">

    - Where is your Radarr Media stored on the local system?

    <div class="container">
    _This is the path to the Movies folder that you can open in your file explorer._<br>
    <label for="path-radarr">Media Path:</label>
    <input type="text" id="local-path-radarr" name="radarr-path" class="media-path" placeholder="/mnt/path/to/movies"><br>
    </div>

    !!! info
        The path should be the location where your Radarr library media is stored (a.k.a Radarr Root Folder).
    
    </div>
    <!-- END - Radarr on Host -->

    </div>

### Sonarr

- Do you want to connect Sonarr to Trailarr?

    <input type="radio" id="sonarr-yes" name="sonarr" value="yes">
    <label for="sonarr-yes">Yes</label>
    <input type="radio" id="sonarr-no" name="sonarr" value="no" checked>
    <label for="sonarr-no">No</label><br>

    <!-- Sonarr Details -->
    <div id="sonarr-container" class="d-none">

    - Are you running Sonarr as a Docker container?

    <div class="container">
    <input type="radio" id="sonarr-docker" name="sonarr-docker" value="yes" checked>
    <label for="sonarr-docker">Yes</label>
    <input type="radio" id="sonarr-direct" name="sonarr-docker" value="no">
    <label for="sonarr-direct">No</label><br>
    </div>

    <!-- Sonarr as Container -->
    <div id="sonarr-docker-container">

    - Where is your Sonarr Media stored on the local system?

    <div class="container">
    _This is the path to the Movies folder that you can open in your file explorer._<br>
    <label for="local-path-sonarr">Local Path:</label>
    <input type="text" id="local-path-sonarr" name="sonarr-path" class="media-path" placeholder="/mnt/disk1/media/movies" spellcheck="false" autocorrect="off"><br>
    </div>

    - Where is your Sonarr media stored inside the container?

    <div class="container">
    _This is the path to the Movies folder inside your Sonarr container. Also known as the Sonarr Root Folder._<br>
    <label for="container-path-sonarr">Container Path:</label>
    <input type="text" id="container-path-sonarr" name="sonarr-path" class="media-path" placeholder="/media/movies"><br>
    </div>

    ??? example
        For example, if you have volumes mapped in your docker command like:
        ```yaml
        /mnt/disk1/media/movies:/media/movies
        ```
        Then the `Local Path` should be:
        ```yaml
        /mnt/path/to/movies
        ```
        And the `Container Path` should be:
        ```yaml
        /media/movies
        ```
    </div>
    <!-- END - Sonarr as container -->

    <!-- Sonarr on Host -->
    <div id="sonarr-direct-container" class="d-none">

    - Where is your Sonarr Media stored on the local system?

    <div class="container">
    _This is the path to the Movies folder that you can open in your file explorer._<br>
    <label for="path-sonarr">Media Path:</label>
    <input type="text" id="local-path-sonarr" name="sonarr-path" class="media-path" placeholder="/mnt/path/to/movies"><br>
    </div>
    </div>
    <!-- END - Sonarr on Host -->

    </div>


## Output

<div id="docker-compose-container" markdown>

### Docker Compose

Use the below docker-compose to run Trailarr app.

```yaml
version: '3.7'

```

</div>

<div id="docker-cli-container" class="d-none" markdown>

### Docker CLI


Use the below docker command to run Trailarr app.

<span id="docker-output-cli" markdown=""></span>
```bash
docker run -d \
    --name=trailarr \
    -e TZ=America/New_York \
    -e PUID=1000 \
    -e PGID=1000 \
    -p 7889:7889 \
    -v <LOCAL_APPDATA_FOLDER>:/config \
    -v <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER> \
    -v <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER> \
    --restart unless-stopped \
    nandyalu/trailarr:latest
```

</div>
<style>
    .d-none {
        display: none;
    }
    input[type="radio"] {
        margin: 1rem;
    }
    .media-path {
        margin: 1rem;
        height: 1.5rem;
        width: 30vw;
        min-width: 200px;
        max-width: 500px;
        color: #448aff;
        font-size: larger;
    }
    .container {
        margin: 1rem;
    }
</style>
<script>
    let isDockerCompose = true;
    let isLunx = true;
    let radarrEnabled = false;
    let sonarrEnabled = false;
    function setDockerRadioValueListener() {
        const radios = document.querySelectorAll(`input[name="docker"]`);
        const displayName = name.charAt(0).toUpperCase() + name.slice(1);
        const dockerCliSelected = document.getElementById('docker-cli-selected');
        const composeElement = document.getElementById('docker-compose-container');
        const cliElement = document.getElementById('docker-cli-container');
        radios.forEach(radio => {
            radio.addEventListener('change', (event) => {
                let selectedValue = event.target.value;
                console.log(`${displayName}: ${selectedValue}`);
                this.isDockerCompose = selectedValue == 'docker-compose';
                dockerCliSelected.style.display = selectedValue == 'docker-cli' ? 'block' : 'none';
                composeElement.style.display = selectedValue == 'docker-compose' ? 'block' : 'none';
                cliElement.style.display = selectedValue == 'docker-cli' ? 'block' : 'none';
            });
        });
        return null;
    }
    function setOSRadioValueListener() {
        const radios = document.querySelectorAll(`input[name="os"]`);
        radios.forEach(radio => {
            radio.addEventListener('change', (event) => {
                let selectedValue = event.target.value;
                console.log(selectedValue);
                this.isLinux = selectedValue == 'linux';
            });
        });
        return null;
    }
    function setArrRadioValueListener() {
        const arrTypes = [
            { name: 'radarr', enabledProp: 'radarrEnabled' },
            { name: 'sonarr', enabledProp: 'sonarrEnabled' }
        ];
        arrTypes.forEach(({ name, enabledProp }) => {
            console.log(`Setting up listener for ${name}`);
            const radios = document.querySelectorAll(`input[name="${name}"]`);
            const containerElement = document.getElementById(`${name}-container`);
            radios.forEach(radio => {
                radio.addEventListener('change', (event) => {
                    let selectedValue = event.target.value;
                    console.log(`${name}: ${selectedValue}`);
                    this[enabledProp] = selectedValue === 'yes';
                    containerElement.style.display = selectedValue === 'yes' ? 'block' : 'none';
                });
            });
        });
        return null;
    }
    function setArrDockerOrHostListener() {
        const arrTypes = [
            { name: 'radarr', enabledProp: 'radarrEnabled' },
            { name: 'sonarr', enabledProp: 'sonarrEnabled' }
        ];
        arrTypes.forEach(({ name, enabledProp }) => {
            const radios = document.querySelectorAll(`input[name="${name}-docker"]`);
            const dockerElement = document.getElementById(`${name}-docker-container`);
            const hostElement = document.getElementById(`${name}-direct-container`);
            radios.forEach(radio => {
                radio.addEventListener('change', (event) => {
                    let selectedValue = event.target.value;
                    console.log(`${name}-selection: ${selectedValue}`);
                    this[enabledProp] = selectedValue === 'yes';
                    dockerElement.style.display = selectedValue === 'yes' ? 'block' : 'none';
                    hostElement.style.display = selectedValue === 'no' ? 'block' : 'none';
                });
            });
        });
        return null;
    }
    function getArrPath(name) {
        const path = document.getElementById(`${name}-path`).value;
        console.log(path);
    }
    // Set up event listeners for radio buttons
    setDockerRadioValueListener(); // docker-compose or docker-cli
    setOSRadioValueListener(); // linux or windows
    setArrRadioValueListener(); // radarr and sonarr sections
    setArrDockerOrHostListener(); // radarr and sonarr docker or host

</script>