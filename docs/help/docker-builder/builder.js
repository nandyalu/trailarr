let connectionCount = 0;
let connectionDivs = [];

// Get the add connection button
const addConnectionButton = document.getElementById('addConnection');

// Get the original connection div already in document
const connection0 = document.getElementById('connection0'); // connection0 is the original connection div
addConnection(); // Add 1 connection div to start with

/**
 * Add event listeners to radio buttons in the connection div
 * 
 * @param {string} connectionId - The id of the connection div
 * @returns {void}
 */
function addRadioEventListeners(connectionId) {
  console.log(`Adding event listeners to radio buttons in ${connectionId}`);
  const connection = document.getElementById(connectionId);

  // Add event listener to connection type radio buttons [Radarr/Sonarr]
  // and show connection container div on selecting any of the radio buttons
  const connectionTypeRadios = connection.querySelectorAll(`input[name=${connectionId}Type]`);
  const containerTypeDivId = `${connectionId}ContainerDiv`;
  connectionTypeRadios.forEach(radioButton => {
    radioButton.addEventListener('click', event => {
      const radioName = event.target.name;
      const radioValue = event.target.value;
      console.log(`Radio button ${radioName} changed to ${radioValue}`);
      // Show the container type div by removing class 'hidden'
      showDiv(containerTypeDivId);
    });
  });

  // Add event listener to connection container radio buttons
  // and show connection container div on selecting any of the radio buttons
  const connectionContainerRadios = connection.querySelectorAll(`input[name=${connectionId}Container]`);
  const hostPathDivId = `${connectionId}HostPathDiv`;
  const dockerPathDiv = `${connectionId}DockerPathDiv`;
  connectionContainerRadios.forEach(radioButton => {
    radioButton.addEventListener('change', event => {
      const radioName = event.target.name;
      const radioValue = event.target.value;
      console.log(`Radio button ${radioName} changed to ${radioValue}`);
      // If the radio button value is 'connection1DockerYes', show the container path input
      if (radioValue === `yes`) {
        showDiv(dockerPathDiv);
      } else {
        hideDiv(dockerPathDiv);
      }
      // Show the host path div
      showDiv(hostPathDivId);
    });
  });
}

/**
 * Show a hidden div by removing the 'hidden' class,
 * and adding the 'blinking' class to show a blinking effect
 * 
 * @param {string} divId - The id of the div to show
 * @returns {void}
 */
function showDiv(divId) {
  const div = document.getElementById(divId);
  if (div.classList.contains('hidden')) {
    div.classList.remove('hidden');
    // Scroll div into view
    div.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Show blinking effect on div
    div.classList.add('blinking');
  }
}

/**
 * Hide a div by adding the 'hidden' class
 * 
 * @param {string} divId - The id of the div to hide
 * @returns {void}
 */
function hideDiv(divId) {
  const div = document.getElementById(divId);
  if (!div.classList.contains('hidden')) {
    div.classList.add('hidden');
  }
}

/**
 * Add a new connection div to the document when the add connection button is clicked
 * 
 * - Clones the original connection div
 * - Updates the id and name attributes to new connection number
 * - Updates the onclick method to remove the new connection div
 * - Inserts the cloned div before the add connection button
 * 
 * If the original connection div is null, alert the user and reload the page
 * 
 * @returns {void}
 */
function addConnection() {
  // Check if the original connection div is not null
  if (connection0 === null) {
    // If the original connection div is null, alert the user and reload the page
    alert('All Connections have been removed. Please start over!');
    window.location.reload();
    return;
  }

  oldConnId = connection0.id;
  // Clone the original connection div
  connectionCount++;
  newConnId = `connection${connectionCount}`;
  const newDiv = connection0.cloneNode(true);

  // Update the id and name attributes of the cloned div
  newDiv.id = newConnId;
  if (newDiv.classList.contains('hidden')) {
    newDiv.classList.remove('hidden');
  }
  newDiv.querySelectorAll('*').forEach(element => {
    if (element.id) {
      element.id = element.id.replace(oldConnId, newConnId);
    }
    if (element.name) {
      element.name = element.name.replace(oldConnId, newConnId);
    }
    if (element.htmlFor) {
      element.htmlFor = element.htmlFor.replace(oldConnId, newConnId);
    }

    // If the element is a radio button, uncheck it
    if (element.type === 'radio') {
      element.checked = false;
    } else if (element.type === 'text') {
      element.value = '';
    }
  });
  newDiv.querySelector('h2').textContent = `Connection ${connectionCount}`;

  // Update the onclick method
  let removeButton = newDiv.querySelector('button');
  removeButton.onclick = () => removeConnection(newDiv.id);


  // Insert the cloned div before the add connection button
  connection0.parentNode.insertBefore(newDiv, addConnectionButton);
  // Add event listeners to the radio buttons
  addRadioEventListeners(newDiv.id);
  connectionDivs.push(newDiv);
}

/**
 * Remove a connection div from the document
 * 
 * - Remove the div from the document
 * - Remove the div from the connectionDivs array
 * - Decrement the connection count
 * 
 * @param {string} divId - The id of the connection div to remove
 * @returns {void}
 */
function removeConnection(divId) {
  debugger;
  if (connectionCount === 0) {
    return;
  }
  const div = document.getElementById(divId);
  div.remove();
  connectionDivs = connectionDivs.filter(connectionDiv => connectionDiv.id !== divId);
  connectionCount--;
}

/**
 * Get the values of the connection div
 * 
 * - Get the connection div by id
 * - Get all the input elements in the connection div
 * - Create an object to store the values
 * - Loop through the input elements
 * - If the input type is radio, check if it is checked and add the value to the object
 * - If the input type is not radio, add the value to the object
 * 
 * @param {string} connectionId - The id of the connection div
 * @returns {object} - The values of the connection div
 */
function getConnectionValues(connectionId) {
  const connection = document.getElementById(connectionId);
  const inputs = connection.querySelectorAll('input');
  const values = {};

  inputs.forEach(input => {
    inputName = input.name;
    inputName = inputName.replace(connectionId, '');
    if (input.type === 'radio') {
      if (input.checked) {
        values[inputName] = input.value;
      }
    } else {
      values[inputName] = input.value;
    }
  });

  values['id'] = connectionId;

  return values;
}

function getUniqueDockerPath(connId, isRadarr) {
  let dockerPath = `/media/${connId}`;
  dockerPath += isRadarr ? '/movies' : '/tv';
  return dockerPath;
}

/**
 * Convert connection values to final paths
 * 
 * - Convert Windows path to Unix path
 * - Remove trailing slashes from host path and docker path
 * - Set final host path in connection values
 * - If docker path is either empty or not unique, set it to a unique path
 * - Set final docker path in connection values
 * 
 * @param {array} connectionValues - The values of all connection divs
 * @returns {array} - The connection values with final paths
 * 
 */
function convertConnectionValues(connectionValues) {
  const uniqueDockerPaths = new Set();
  connectionValues.forEach(connection => {
    const connId = connection.id;
    const isRadarr = connection.Type === 'radarr';
    let hostPath = connection.HostPath;
    let dockerPath = connection.DockerPath;

    // Convert Windows path to Unix path
    if (hostPath.includes(':')) {
      hostPath = hostPath.replace(/:/g, '').replace(/\\/g, '/');
      hostPath = `/${hostPath.charAt(0).toUpperCase()}${hostPath.slice(1)}`;
    }

    // Remove trailing slashes from hostPath and dockerPath
    hostPath = hostPath.replace(/\/+$/, '');

    // Set finalHostPath in connectionValues
    connection.HostPathFinal = hostPath;

    // Get it to a unique path
    dockerPath = getUniqueDockerPath(connId, isRadarr);

    // Remove trailing slashes from dockerPath
    dockerPath = dockerPath.replace(/\/+$/, '');

    // Set finalDockerPath in connectionValues
    connection.DockerPathFinal = dockerPath;

    // Add dockerPath to uniqueDockerPaths
    uniqueDockerPaths.add(dockerPath);
  });

  return connectionValues;
}

function endWithSlash(path) {
  if (path === '') {
    return path;
  }
  // Add a trailing slash to HostPath if it doesn't have one
  if (path.includes('/') && !path.endsWith('/')) {
    path += '/';
  }
  if (path.includes('\\') && !path.endsWith('\\')) {
    path += '\\';
  }
  return path;
}

function getParentFolder(path) {
  return path.substring(0, path.lastIndexOf('/'));
}

function generateMappings(connectionValues) {
  const pathMappings = [];
  const volumeMappings = [];

  // Iterate through each connection object
  connectionValues.forEach(connection => {
    const { id, HostPath, HostPathFinal, DockerPath, DockerPathFinal } = connection;

    // Path Mapping Rules
    if (!DockerPath) {
      // If DockerPath is empty, add a pathMapping
      pathMappings.push({
        from: endWithSlash(HostPath),
        to: endWithSlash(DockerPathFinal),
        id: id
      });
    } else {
      // If DockerPath is not empty, add pathMapping if DockerPath and DockerPathFinal are different
      dockerPathwithSlash = endWithSlash(DockerPath);
      dockerPathFinalwithSlash = endWithSlash(DockerPathFinal);
      if (dockerPathwithSlash !== dockerPathFinalwithSlash) {
        pathMappings.push({
          from: dockerPathwithSlash,
          to: dockerPathFinalwithSlash,
          id: id
        });
      }
    }

    // Add Volume Mappings
    volumeMappings.push({
      from: HostPathFinal,
      to: DockerPathFinal,
      id: id
    });
  });

  return { pathMappings, volumeMappings };
}

/**
 * Get the values of all connection divs
 * 
 * - Create an array to store the values of all connection divs
 * - Loop through the connection divs
 * - Get the values of each connection div
 * - Add the values to the array
 * 
 * @returns {array} - The values of all connection divs
 */
function generateCommand() {
  let connectionValues = [];
  connectionDivs.forEach(connectionDiv => {
    const connection = getConnectionValues(connectionDiv.id);
    connectionValues.push(connection);
  });

  // Convert connection values to final paths
  connectionValues = convertConnectionValues(connectionValues);

  // Generate path mappings and volume mappings
  const { pathMappings, volumeMappings } = generateMappings(connectionValues);

  let dockerComposeVolumes = '';
  let dockerCliVolumes = '';

  // Generate volume mappings for Docker Compose and Docker CLI commands
  volumeMappings.forEach(({ from, to, id }) => {
    dockerComposeVolumes += `      - ${from}:${to}  #${id}\n`;
    dockerCliVolumes += ` -v ${from}:${to}`;
  });

  const dockerComposeCommand = `
services:
  trailarr:
    image: nandyalu/trailarr:latest
    volumes:
${dockerComposeVolumes}`;

  const dockerCliCommand = `docker run -d --name trailarr${dockerCliVolumes} nandyalu/trailarr:latest`;

  outputComposeDiv = document.getElementById('outputComposeCode');
  outputComposeDiv.innerText = dockerComposeCommand;

  document.getElementById('outputCliCode').innerText = `${dockerCliCommand.trim()}`;
  outputPathMappingsDiv = document.getElementById('outputPathMappings');
  outputPathMappingsDiv.innerText = JSON.stringify(pathMappings, null, 2);
  outputPathMappingsDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });

  console.log(connectionValues);
  console.log(volumeMappings);
  console.log(pathMappings);
  return;
}

console.log('builder.js loaded');