#!/usr/bin/env python3
"""
GitHub Account Backup Script

This script backs up all your original repositories and gists from GitHub
to a local backup directory organized by date. All output is logged to both
console and a backup.log file.

Requirements:
- GitHub personal access token (in .token file or via --token argument)
- Git installed on system
- Python packages: PyGithub, requests, gitpython

Features:
- Backs up all original repositories (excludes forks)
- Backs up all gists (sorted by creation date)
- Clones all branches and tags
- Submodules are NOT resolved (can be done later if needed)
- Comprehensive logging to backup/date/backup.log
- Automatic zip compression (can be disabled with --no-zip)
- Gist folders named with creation date: YYYY-MM-DD_gist_id

Usage:
    # Recommended: Create .token file with your GitHub token
    echo "your_github_token_here" > .token
    python github_backup.py [--username USERNAME] [--no-zip]
    
    # Alternative: Use command line token
    python github_backup.py --token YOUR_GITHUB_TOKEN [--username USERNAME] [--no-zip]
"""

import argparse
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
import requests
from github import Github
from git import Repo, GitCommandError
import shutil
import logging
import zipfile


class GitHubBackup:
    def __init__(self, token, username=None, enable_compression=True):
        """Initialize GitHub backup with authentication token."""
        self.github = Github(token)
        self.token = token
        self.user = self.github.get_user() if username is None else self.github.get_user(username)
        self.username = self.user.login
        self.enable_compression = enable_compression
        
        # Create backup directory with current date
        self.backup_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.backup_dir = Path("backup") / self.backup_date
        self.repos_dir = self.backup_dir / "repositories"
        self.gists_dir = self.backup_dir / "gists"
        
        # Create directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.gists_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.log_file = self.backup_dir / "backup.log"
        self.logger = self._setup_logger()
        
        self.log(f"Backing up GitHub account: {self.username}")
        self.log(f"Backup directory: {self.backup_dir}")
    
    def _setup_logger(self):
        """Setup logger to write to both console and file."""
        logger = logging.getLogger('github_backup')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(message)s', 
                                         datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log(self, message):
        """Log message to both console and file."""
        self.logger.info(message)

    def backup_repositories(self):
        """Backup all original repositories (excluding forks)."""
        self.log("\n" + "="*50)
        self.log("BACKING UP REPOSITORIES")
        self.log("="*50)
        
        repos = list(self.user.get_repos())
        original_repos = [repo for repo in repos if not repo.fork]
        
        self.log(f"Found {len(repos)} total repositories")
        self.log(f"Backing up {len(original_repos)} original repositories (excluding forks)")
        
        # Print list of repositories to be backed up
        if original_repos:
            self.log("\nRepositories to be backed up:")
            self.log("-" * 60)
            for i, repo in enumerate(original_repos, 1):
                privacy_status = "PRIVATE" if repo.private else "PUBLIC"
                self.log(f"{i:3d}. {repo.name}")
                self.log(f"     URL: {repo.html_url}")
                self.log(f"     Status: {privacy_status}")
                if repo.description:
                    self.log(f"     Description: {repo.description}")
                self.log("")
            self.log("-" * 60)
            self.log(f"Total: {len(original_repos)} repositories")
            self.log("")
        
        repo_metadata = []
        
        for i, repo in enumerate(original_repos, 1):
            self.log(f"\n[{i}/{len(original_repos)}] Backing up: {repo.name}")
            
            try:
                # Create repository directory
                repo_path = self.repos_dir / repo.name
                
                # Clone repository with all branches and submodules
                self._clone_repository(repo, repo_path)
                
                # Save repository metadata
                metadata = self._get_repo_metadata(repo)
                repo_metadata.append(metadata)
                
                # Save metadata to file
                metadata_file = repo_path / "repo_metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, default=str)
                
                self.log(f"SUCCESS: Successfully backed up {repo.name}")
                
            except Exception as e:
                self.log(f"ERROR: Error backing up {repo.name}: {str(e)}")
                continue
        
        # Save overall repositories metadata
        with open(self.repos_dir / "repositories_summary.json", 'w', encoding='utf-8') as f:
            json.dump(repo_metadata, f, indent=2, default=str)
        
        self.log(f"\nSUCCESS: Repository backup completed!")

    def _clone_repository(self, repo, repo_path):
        """Clone a repository with all branches and submodules."""
        clone_url = repo.clone_url
        
        # Use token for authentication in clone URL
        auth_url = clone_url.replace("https://", f"https://{self.token}@")
        
        try:
            # Clone repository
            self.log(f"  Cloning {repo.name}...")
            cloned_repo = Repo.clone_from(auth_url, repo_path, branch=repo.default_branch)
            
            # Fetch all branches
            self.log(f"  Fetching all branches...")
            origin = cloned_repo.remotes.origin
            origin.fetch()
            
            # Create local branches for all remote branches
            for ref in origin.refs:
                if ref.name != f"origin/{repo.default_branch}":
                    branch_name = ref.name.split('/')[-1]
                    try:
                        cloned_repo.create_head(branch_name, ref)
                    except GitCommandError:
                        # Branch might already exist
                        pass
            
            # Note: Submodules are not resolved to keep backup size manageable
            # They can be resolved later if needed using: git submodule update --init --recursive
                
        except Exception as e:
            raise Exception(f"Failed to clone repository: {str(e)}")

    def _get_repo_metadata(self, repo):
        """Extract comprehensive metadata from a repository."""
        metadata = {
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description,
            'url': repo.html_url,
            'clone_url': repo.clone_url,
            'ssh_url': repo.ssh_url,
            'default_branch': repo.default_branch,
            'language': repo.language,
            'languages': dict(repo.get_languages()) if hasattr(repo, 'get_languages') else {},
            'size': repo.size,
            'stargazers_count': repo.stargazers_count,
            'watchers_count': repo.watchers_count,
            'forks_count': repo.forks_count,
            'open_issues_count': repo.open_issues_count,
            'created_at': repo.created_at,
            'updated_at': repo.updated_at,
            'pushed_at': repo.pushed_at,
            'private': repo.private,
            'archived': repo.archived,
            'disabled': repo.disabled,
            'topics': repo.get_topics(),
            'license': repo.license.name if repo.license else None,
        }
        
        try:
            # Get branches
            branches = [branch.name for branch in repo.get_branches()]
            metadata['branches'] = branches
        except:
            metadata['branches'] = []
        
        try:
            # Get tags
            tags = [tag.name for tag in repo.get_tags()]
            metadata['tags'] = tags
        except:
            metadata['tags'] = []
        
        return metadata

    def backup_gists(self):
        """Backup all gists."""
        self.log("\n" + "="*50)
        self.log("BACKING UP GISTS")
        self.log("="*50)
        
        gists = list(self.user.get_gists())
        # Sort gists by creation date (oldest first)
        gists.sort(key=lambda g: g.created_at)
        self.log(f"Found {len(gists)} gists to backup")
        
        # Print list of gists to be backed up
        if gists:
            self.log("\nGists to be backed up:")
            self.log("-" * 60)
            for i, gist in enumerate(gists, 1):
                privacy_status = "PUBLIC" if gist.public else "PRIVATE"
                creation_date = gist.created_at.strftime("%Y-%m-%d")
                folder_name = f"{creation_date}_{gist.id}"
                self.log(f"{i:3d}. {gist.id} (created: {creation_date})")
                self.log(f"     Folder: {folder_name}")
                self.log(f"     URL: {gist.html_url}")
                self.log(f"     Status: {privacy_status}")
                if gist.description:
                    self.log(f"     Description: {gist.description}")
                if gist.files:
                    file_list = ", ".join(gist.files.keys())
                    self.log(f"     Files: {file_list}")
                self.log("")
            self.log("-" * 60)
            self.log(f"Total: {len(gists)} gists")
            self.log("")
        
        gist_metadata = []
        
        for i, gist in enumerate(gists, 1):
            creation_date = gist.created_at.strftime("%Y-%m-%d")
            folder_name = f"{creation_date}_{gist.id}"
            self.log(f"\n[{i}/{len(gists)}] Backing up gist: {gist.id} ({creation_date})")
            
            try:
                # Create gist directory with date prefix
                gist_dir = self.gists_dir / folder_name
                gist_dir.mkdir(exist_ok=True)
                
                # Save gist files
                for filename, file_obj in gist.files.items():
                    file_path = gist_dir / filename
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_obj.content)
                
                # Save gist metadata
                metadata = {
                    'id': gist.id,
                    'description': gist.description,
                    'public': gist.public,
                    'html_url': gist.html_url,
                    'git_pull_url': gist.git_pull_url,
                    'git_push_url': gist.git_push_url,
                    'created_at': gist.created_at,
                    'updated_at': gist.updated_at,
                    'comments': gist.comments,
                    'files': {name: {
                        'filename': name,
                        'language': file_obj.language,
                        'size': file_obj.size,
                        'type': file_obj.type
                    } for name, file_obj in gist.files.items()}
                }
                
                gist_metadata.append(metadata)
                
                # Save metadata to file
                metadata_file = gist_dir / "gist_metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, default=str)
                
                self.log(f"SUCCESS: Successfully backed up gist {gist.id}")
                
            except Exception as e:
                self.log(f"ERROR: Error backing up gist {gist.id}: {str(e)}")
                continue
        
        # Save overall gists metadata
        with open(self.gists_dir / "gists_summary.json", 'w', encoding='utf-8') as f:
            json.dump(gist_metadata, f, indent=2, default=str)
        
        self.log(f"\nSUCCESS: Gist backup completed!")

    def create_backup_summary(self):
        """Create a summary of the backup."""
        self.log("\n" + "="*50)
        self.log("CREATING BACKUP SUMMARY")
        self.log("="*50)
        
        summary = {
            'backup_date': self.backup_date,
            'username': self.username,
            'backup_directory': str(self.backup_dir),
            'log_file': str(self.log_file),
            'repositories': {
                'count': len(list(self.repos_dir.glob('*'))) - 1,  # Exclude summary file
                'directory': str(self.repos_dir)
            },
            'gists': {
                'count': len(list(self.gists_dir.glob('*'))) - 1,  # Exclude summary file
                'directory': str(self.gists_dir)
            }
        }
        
        summary_file = self.backup_dir / "backup_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.log(f"SUCCESS: Backup summary saved to: {summary_file}")
        self.log(f"SUCCESS: Backup log saved to: {self.log_file}")
        self.log(f"\nBACKUP COMPLETED SUCCESSFULLY!")
        self.log(f"Total repositories backed up: {summary['repositories']['count']}")
        self.log(f"Total gists backed up: {summary['gists']['count']}")
        self.log(f"Backup location: {self.backup_dir}")
        
        return summary

    def compress_backup(self):
        """Compress the backup directory into a zip file."""
        if not self.enable_compression:
            self.log("Compression disabled, skipping zip creation")
            return None
            
        self.log("\n" + "="*50)
        self.log("COMPRESSING BACKUP")
        self.log("="*50)
        
        zip_filename = f"{self.backup_dir.name}.zip"
        zip_path = self.backup_dir.parent / zip_filename
        
        try:
            # First, collect all files to compress and calculate total size
            self.log("Analyzing files for compression...")
            all_files = []
            total_size = 0
            
            for file_path in self.backup_dir.rglob('*'):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    all_files.append((file_path, file_size))
                    total_size += file_size
            
            self.log(f"Found {len(all_files)} files to compress")
            self.log(f"Total uncompressed size: {total_size / (1024*1024):.1f} MB")
            self.log(f"Creating zip archive: {zip_path}")
            self.log("Compression progress:")
            
            compressed_size_so_far = 0
            failed_files = []
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=4) as zipf:
                for i, (file_path, file_size) in enumerate(all_files, 1):
                    try:
                        # Calculate relative path within the backup directory
                        arcname = file_path.relative_to(self.backup_dir.parent)
                        
                        # Show progress for larger files or every 50 files
                        show_progress = (file_size > 1024*1024) or (i % 50 == 0) or (i == len(all_files))
                        
                        if show_progress:
                            progress_pct = (i / len(all_files)) * 100
                            size_mb = file_size / (1024*1024)
                            if size_mb >= 1:
                                self.log(f"  [{i:4d}/{len(all_files)}] ({progress_pct:5.1f}%) Compressing: {arcname} ({size_mb:.1f} MB)")
                            else:
                                self.log(f"  [{i:4d}/{len(all_files)}] ({progress_pct:5.1f}%) Compressing: {arcname}")
                        
                        # Add file to zip
                        zipf.write(file_path, arcname)
                        compressed_size_so_far += file_size
                        
                    except Exception as e:
                        error_msg = f"Failed to compress {file_path}: {str(e)}"
                        self.log(f"  WARNING: {error_msg}")
                        failed_files.append((str(file_path), str(e)))
                        continue
            
            # Get final compressed size info
            if zip_path.exists():
                final_compressed_size = zip_path.stat().st_size
                compression_ratio = (1 - final_compressed_size / total_size) * 100 if total_size > 0 else 0
                
                self.log(f"\nSUCCESS: Backup compressed successfully")
                self.log(f"Files processed: {len(all_files) - len(failed_files)}/{len(all_files)}")
                if failed_files:
                    self.log(f"Failed files: {len(failed_files)}")
                self.log(f"Original size: {total_size / (1024*1024):.1f} MB")
                self.log(f"Compressed size: {final_compressed_size / (1024*1024):.1f} MB")
                self.log(f"Compression ratio: {compression_ratio:.1f}%")
                self.log(f"Zip file location: {zip_path}")
                
                result = {
                    'zip_file': str(zip_path),
                    'original_size_bytes': total_size,
                    'compressed_size_bytes': final_compressed_size,
                    'compression_ratio_percent': round(compression_ratio, 1),
                    'files_processed': len(all_files) - len(failed_files),
                    'total_files': len(all_files),
                    'failed_files': len(failed_files)
                }
                
                if failed_files:
                    result['failed_file_details'] = failed_files
                
                return result
            else:
                self.log("ERROR: Zip file was not created successfully")
                return None
                        
        except Exception as e:
            self.log(f"ERROR: Failed to compress backup: {str(e)}")
            # If partial zip file exists, try to clean it up
            if zip_path.exists():
                try:
                    zip_path.unlink()
                    self.log(f"Cleaned up partial zip file: {zip_path}")
                except:
                    pass
            return None

    def run_backup(self):
        """Run the complete backup process."""
        try:
            self.log(f"Starting GitHub backup for user: {self.username}")
            
            # Backup repositories
            self.backup_repositories()
            
            # Backup gists
            self.backup_gists()
            
            # Create summary
            summary = self.create_backup_summary()
            
            # Compress backup if enabled
            compression_info = self.compress_backup()
            
            # Update summary with compression info if compression was performed
            if compression_info:
                summary['compression'] = compression_info
                # Update the summary file with compression info
                summary_file = self.backup_dir / "backup_summary.json"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, default=str)
                self.log(f"Updated backup summary with compression info")
            
        except Exception as e:
            self.log(f"Backup failed: {str(e)}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Backup GitHub account repositories and gists')
    parser.add_argument('--token', help='GitHub personal access token (optional if .token file exists)')
    parser.add_argument('--username', help='GitHub username (defaults to authenticated user)')
    parser.add_argument('--no-zip', action='store_true', help='Disable zip compression of backup (enabled by default)')
    
    args = parser.parse_args()
    
    # Get token from command line or .token file
    token = args.token
    if not token:
        try:
            with open('.token', 'r', encoding='utf-8') as f:
                token = f.read().strip()
            if not token:
                print("Error: .token file is empty")
                sys.exit(1)
            print("Using token from .token file")
        except FileNotFoundError:
            print("Error: No token provided via --token and .token file not found")
            print("Either provide --token argument or create a .token file with your GitHub token")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading .token file: {str(e)}")
            sys.exit(1)
    else:
        print("Using token from command line argument")
    
    # Check if git is available
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Git is not installed or not available in PATH")
        sys.exit(1)
    
    # Run backup
    enable_compression = not args.no_zip
    backup = GitHubBackup(token, args.username, enable_compression)
    backup.run_backup()


if __name__ == "__main__":
    main() 