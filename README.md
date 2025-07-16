# GitHub Account Backup Script

A comprehensive Python script to backup your entire GitHub account including all original repositories (excluding forks) and gists to local storage.

## Features

- **Complete Repository Backup**: Clones all your original repositories with full history
- **Gist Backup**: Downloads all your gists with metadata
- **Branch & Tag Support**: Backs up all branches and tags
- **Fork Filtering**: Excludes forked repositories, only backs up originals
- **Metadata Preservation**: Saves comprehensive metadata for repositories and gists
- **Date Organization**: Organizes backups by date and time
- **Progress Tracking**: Real-time progress updates during backup
- **Comprehensive Logging**: All output logged to both console and backup.log file
- **Submodule Handling**: Submodules are NOT resolved to keep backup size manageable
- **Gist Organization**: Gists sorted by creation date with folders named `YYYY-MM-DD_gist_id`
- **Automatic Compression**: Creates zip archive of backup (can be disabled with --no-zip)

## Prerequisites

1. **Git**: Must be installed and available in your system PATH
2. **Python 3.7+**: Required for the script
3. **GitHub Personal Access Token**: For API authentication

### Creating a GitHub Personal Access Token

1. Go to GitHub Settings -> Developer settings -> Personal access tokens
2. Click "Generate new token" (classic)
3. Give it a name like "GitHub Backup Script"
4. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `gist` (Access to gists)
   - `user` (Access to user profile information)
5. Click "Generate token" and copy the token

## Installation

1. Clone or download this repository
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage with .token file (Recommended)

1. Create a `.token` file in the same directory as the script:
   ```bash
   echo "your_github_token_here" > .token
   ```

2. Run the backup:
   ```bash
   python github_backup.py
   ```

### Alternative: Command Line Token

```bash
python github_backup.py --token YOUR_GITHUB_TOKEN
```

### Backup Specific User (if you have access)

```bash
python github_backup.py --username TARGET_USERNAME
```

### Disable Compression

```bash
python github_backup.py --no-zip
```

### Command Line Options

- `--token` (optional): Your GitHub personal access token (not needed if .token file exists)
- `--username` (optional): Target username to backup (defaults to authenticated user)
- `--no-zip` (optional): Disable zip compression of backup (compression enabled by default)

**Note**: The script will first try to use the token from `--token` argument, then fall back to reading from `.token` file if no argument is provided.

## Output Structure

The script creates a backup directory structure like this:

```
backup/
├── 2024-01-15_14-30-22.zip        # Compressed backup archive (if enabled)
└── 2024-01-15_14-30-22/           # Backup timestamp
    ├── backup_summary.json        # Overall backup summary (includes compression info)
    ├── backup.log                 # Complete backup log with timestamps
    ├── repositories/               # All repositories
    │   ├── repositories_summary.json
    │   ├── repo1/
    │   │   ├── repo_metadata.json  # Repository metadata
    │   │   └── [repository files]  # Full git repository
    │   └── repo2/
    │       ├── repo_metadata.json
    │       └── [repository files]
    └── gists/                      # All gists (sorted by creation date)
        ├── gists_summary.json
        ├── 2020-05-15_abc123def456/    # YYYY-MM-DD_gist_id format
        │   ├── gist_metadata.json      # Gist metadata
        │   └── [gist files]            # Gist content files
        └── 2023-12-01_fed654cba321/
            ├── gist_metadata.json
            └── [gist files]
```

## What Gets Backed Up

### Repositories (Original Only)
- [YES] Full git history and all commits
- [YES] All branches and tags
- [NO] Submodules (not resolved to keep backup size manageable)
- [YES] Repository metadata (description, language, stars, etc.)
- [YES] Topics and license information
- [NO] Forked repositories (filtered out)

### Gists
- [YES] All gist files and content
- [YES] Gist metadata (description, public/private status, etc.)
- [YES] File information (language, size, type)
- [YES] Sorted by creation date (oldest first)
- [YES] Folder names include creation date: `YYYY-MM-DD_gist_id`

## Metadata Files

Each backup includes comprehensive metadata:

### Repository Metadata (`repo_metadata.json`)
- Repository details (name, description, URLs)
- Statistics (stars, forks, watchers, issues)
- Dates (created, updated, last push)
- Branches and tags list
- Programming languages used
- Topics and license information

### Gist Metadata (`gist_metadata.json`)
- Gist ID and description
- Public/private status
- File information and languages
- Creation and update dates

## Error Handling

The script includes robust error handling:
- Continues backup process even if individual repositories fail
- Logs detailed error messages for troubleshooting
- Validates prerequisites before starting
- Graceful handling of rate limits and network issues

## Security Notes

- Your GitHub token is used only for API authentication
- Tokens are not stored or logged anywhere (except in your local .token file)
- Use tokens with minimal required permissions
- Consider using a dedicated token for backup purposes
- **IMPORTANT**: Never commit your `.token` file to version control
- The included `.gitignore` file prevents accidental commits of `.token`

## Tips

1. **Large Repositories**: Backup may take time for accounts with many/large repositories
2. **Rate Limits**: GitHub API has rate limits; the script handles these automatically
3. **Storage Space**: Ensure sufficient disk space for all repositories
4. **Incremental Backups**: Run regularly to create versioned backups
5. **Private Repositories**: Ensure your token has access to private repositories if needed
6. **Submodules**: If you need submodules, navigate to a repository and run: `git submodule update --init --recursive`
7. **Backup Logs**: Check `backup.log` for detailed operation logs with timestamps
8. **Compression**: Zip compression is enabled by default - use `--no-zip` to disable if you prefer uncompressed backups
9. **Gist Organization**: Gists are sorted chronologically and folders show creation dates for easy organization
10. **Compression Progress**: Detailed progress shown during zip creation with file counts and large file indicators

## Troubleshooting

### Common Issues

1. **"Git not found"**: Install Git and ensure it's in your system PATH
2. **Authentication errors**: Verify your GitHub token is correct and has required permissions
3. **Network errors**: Check internet connection and GitHub status
4. **Permission errors**: Ensure write permissions in the backup directory
5. **Compression appears stuck**: The compression process shows detailed progress - large repositories may take time to compress. Check the log for current file being processed
6. **Compression fails on specific files**: Individual file failures are logged but don't stop the backup process

### Getting Help

If you encounter issues:
1. Check the error messages in the console output
2. Verify your GitHub token permissions
3. Ensure Git is properly installed
4. Check available disk space

## Example Output

```
Using token from .token file
Backing up GitHub account: yourusername
Backup directory: backup\2024-01-15_14-30-22

==================================================
BACKING UP REPOSITORIES
==================================================
Found 25 total repositories
Backing up 18 original repositories (excluding forks)

[1/18] Backing up: my-awesome-project
  Cloning my-awesome-project...
  Fetching all branches...
SUCCESS: Successfully backed up my-awesome-project

[2/18] Backing up: another-repo
  Cloning another-repo...
  Fetching all branches...
SUCCESS: Successfully backed up another-repo

...

==================================================
BACKING UP GISTS
==================================================
Found 12 gists to backup

Gists to be backed up:
------------------------------------------------------------
  1. abc123def456 (created: 2020-05-15)
     Folder: 2020-05-15_abc123def456
     URL: https://gist.github.com/abc123def456
     Status: PUBLIC
     Description: Useful code snippet
     Files: script.py, README.md

...

[1/12] Backing up gist: abc123def456 (2020-05-15)
SUCCESS: Successfully backed up gist abc123def456

...

==================================================
CREATING BACKUP SUMMARY
==================================================
SUCCESS: Backup summary saved to: backup\2024-01-15_14-30-22\backup_summary.json
SUCCESS: Backup log saved to: backup\2024-01-15_14-30-22\backup.log

BACKUP COMPLETED SUCCESSFULLY!
Total repositories backed up: 18
Total gists backed up: 12
Backup location: backup\2024-01-15_14-30-22

==================================================
COMPRESSING BACKUP
==================================================
Analyzing files for compression...
Found 1247 files to compress
Total uncompressed size: 245.8 MB
Creating zip archive: backup\2024-01-15_14-30-22.zip
Compression progress:
  [  50/1247] ( 4.0%) Compressing: 2024-01-15_14-30-22/repositories/large-repo/.git/objects/pack/pack-abc123.pack (15.2 MB)
  [ 100/1247] ( 8.0%) Compressing: 2024-01-15_14-30-22/repositories/another-repo/dist/bundle.js
  [ 150/1247] (12.1%) Compressing: 2024-01-15_14-30-22/repositories/website/images/hero.jpg (2.1 MB)
  ...
  [1247/1247] (100.0%) Compressing: 2024-01-15_14-30-22/backup_summary.json

SUCCESS: Backup compressed successfully
Files processed: 1245/1247
Failed files: 2
Original size: 245.8 MB
Compressed size: 89.3 MB
Compression ratio: 63.7%
Zip file location: backup\2024-01-15_14-30-22.zip
Updated backup summary with compression info
``` 