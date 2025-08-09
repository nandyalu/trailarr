# Entrypoint Script Modules

This directory contains modular components for the Docker container entrypoint script. The main `entrypoint.sh` script orchestrates these modules for better maintainability and organization.

## Module Overview

### 1. `banner.sh`
**Purpose**: Display startup banner and initial configuration information
- Shows the ASCII art TRAILARR logo
- Displays app version and configuration parameters (APP_DATA_DIR, PUID, PGID, TZ)
- Sets up initial logging output formatting

**Functions**: `display_startup_banner()`

### 2. `timezone.sh`
**Purpose**: Configure system timezone
- Sets the container timezone based on the `TZ` environment variable
- Updates system time and reconfigures timezone data
- Displays before/after timestamps for verification

**Functions**: `configure_timezone()`

### 3. `directories.sh`
**Purpose**: Setup application directories and handle data migration
- Creates and configures the APP_DATA_DIR folder structure
- Handles database migration from legacy `/data` location
- Sets up temporary directories and permissions
- Runs yt-dlp update script

**Functions**: `setup_directories()`

### 4. `gpu_detection.sh`
**Purpose**: Detect and configure GPU hardware acceleration
- Detects NVIDIA, Intel, and AMD GPUs
- Maps GPU devices and checks availability
- Tests VAAPI capabilities for Intel/AMD GPUs
- Checks user permissions for GPU access
- Contains the most complex GPU detection logic

**Functions**: 
- `detect_gpu_devices()`
- `check_nvidia_gpu()`
- `check_intel_gpu()`
- `check_amd_gpu()`
- `check_gpu_permissions()`
- `setup_gpu_detection()` (main orchestrator)

### 5. `user_groups.sh`
**Purpose**: Manage user accounts and GPU groups
- Creates application user and group with specified PUID/PGID
- Configures GPU-related groups for hardware acceleration access
- Handles group membership for render, video, and device-specific groups
- Sets final file permissions and ownership

**Functions**: 
- `setup_user_and_groups()`
- `group_exists()` (utility function)
- `configure_gpu_groups()`
- `finalize_user_setup()`

### 6. `env_file.sh`
**Purpose**: Generate environment configuration file
- Writes GPU detection results to the `.env` file
- Updates environment variables for application use
- Preserves existing non-GPU environment variables

**Functions**: `generate_env_file()`

### 7. `startup.sh`
**Purpose**: Start the application as non-root user
- Switches to the application user using gosu
- Configures GPU group memberships for the application process
- Executes the final start.sh script
- Contains the exec command that transfers control to the application

**Functions**: `start_application()`

## Execution Order

The main `entrypoint.sh` script calls these modules in this specific order:

1. `display_startup_banner()` - Show initial information
2. `configure_timezone()` - Set up timezone
3. `setup_directories()` - Create directory structure
4. `setup_gpu_detection()` - Detect GPU hardware
5. `setup_user_and_groups()` - Create user accounts
6. `configure_gpu_groups()` - Set up GPU access groups
7. `generate_env_file()` - Write environment configuration
8. `finalize_user_setup()` - Set final permissions
9. `start_application()` - Launch the application

## Benefits of Modular Design

- **Maintainability**: Each module has a single responsibility
- **Testability**: Individual components can be tested in isolation
- **Readability**: Logical separation makes the code easier to understand
- **Reusability**: Modules can potentially be reused in other contexts
- **Debugging**: Issues can be isolated to specific functional areas

## Development Guidelines

- Each module should source `/app/scripts/box_echo.sh` for consistent logging
- Use descriptive function names that clearly indicate their purpose
- Export variables that need to be available to other modules
- Keep modules focused on their specific responsibility
- Document any dependencies between modules

## Environment Variables

Key environment variables used across modules:
- `APP_VERSION` - Application version for display
- `APP_DATA_DIR` - Data directory location
- `PUID`/`PGID` - User/group IDs for the application user
- `TZ` - Timezone configuration
- `GPU_*` variables - GPU detection results (set by gpu_detection.sh)
- `APPUSER`/`APPGROUP` - Application user/group names (set by user_groups.sh)
