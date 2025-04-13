# RemotelyPy Configuration Profiles

This document explains how to use configuration profiles in RemotelyPy to save and load different settings for both client and controller modes.

## Overview

Configuration profiles allow you to save commonly used settings and quickly switch between different configurations without having to specify all command-line arguments each time.

Profiles are stored in the following locations:

- Client profiles: `~/.remotelypy/client_profiles/`
- Controller profiles: `~/.remotelypy/controller_profiles/`

## Using Profiles with the Command Line

### Client Mode

#### Saving a profile

```bash
# Connect to a server and save the settings as a profile
./main.py client --host example.com --port 5555 --ssl --cert /path/to/cert.pem --save-profile my-server
```

#### Loading a profile

```bash
# Connect using saved settings
./main.py client --profile my-server
```

#### Overriding profile settings

```bash
# Load a profile but override specific settings
./main.py client --profile my-server --port 6666
```

#### Listing available profiles

```bash
./main.py client --list-profiles
```

#### Deleting a profile

```bash
./main.py client --delete-profile my-server
```

### Controller Mode

#### Saving a profile

```bash
# Start a controller and save the settings as a profile
./main.py controller --host 0.0.0.0 --port 5555 --ssl --cert /path/to/cert.pem --key /path/to/key.pem --save-profile secure-server
```

#### Loading a profile

```bash
# Start a controller using saved settings
./main.py controller --profile secure-server
```

#### Overriding profile settings

```bash
# Load a profile but override specific settings
./main.py controller --profile secure-server --port 6666
```

#### Listing available profiles

```bash
./main.py controller --list-profiles
```

#### Deleting a profile

```bash
./main.py controller --delete-profile secure-server
```

## Using the Profile Manager Utility

RemotelyPy includes a dedicated profile manager utility for more advanced profile management:

```bash
# List all profiles
python assets/profile_manager.py list

# Show details of a specific profile
python assets/profile_manager.py show --mode client --name my-server

# Delete a profile
python assets/profile_manager.py delete --mode controller --name secure-server

# Export a profile to a file
python assets/profile_manager.py export --mode client --name my-server --output my-server.json

# Import a profile from a file
python assets/profile_manager.py import --mode client --name imported-server --input my-server.json
```

## Examples

### Example 1: Managing Multiple Client Connections

```bash
# Save a profile for connecting to a production server
./main.py client --host prod.example.com --port 5555 --ssl --cert /path/to/prod-cert.pem --save-profile production

# Save a profile for connecting to a development server
./main.py client --host dev.example.com --port 5555 --save-profile development

# Connect to production server
./main.py client --profile production

# Connect to development server
./main.py client --profile development
```

### Example 2: Different Controller Configurations

```bash
# Save a profile for a secure public-facing controller
./main.py controller --host 0.0.0.0 --port 5555 --ssl --cert /path/to/cert.pem --key /path/to/key.pem --save-profile public

# Save a profile for a local development controller
./main.py controller --host 127.0.0.1 --port 5555 --save-profile local

# Start the public-facing controller
./main.py controller --profile public

# Start the local development controller
./main.py controller --profile local
```

## Technical Details

Profiles are stored as JSON files and contain all the command-line arguments that were specified when the profile was saved. When loading a profile, any arguments specified on the command line will override the values from the profile.
