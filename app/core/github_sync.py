"""
GitHub integration module for syncing prompts and configuration.
"""

import git
from git import Repo, GitCommandError
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.core.config import get_config

logger = logging.getLogger(__name__)


class GitHubSync:
    """Manages GitHub repository operations for PromptBuilder."""

    def __init__(self):
        self.config = get_config()
        self.repo_path = self.config.PROJECT_ROOT
        self.repo: Optional[Repo] = None
        self._init_repo()

    def _init_repo(self):
        """Initialize or get existing git repository."""
        try:
            self.repo = Repo(self.repo_path)
            logger.info(f"Git repository initialized at {self.repo_path}")
        except git.InvalidGitRepositoryError:
            logger.warning("Not a git repository, creating new one")
            try:
                self.repo = Repo.init(self.repo_path)
                logger.info("New git repository created")
            except Exception as e:
                logger.error(f"Failed to create git repository: {e}")
                self.repo = None

    def is_configured(self) -> bool:
        """Check if GitHub is properly configured."""
        return (
            self.repo is not None and
            self.config.has_github_configured()
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current repository status."""
        if not self.repo:
            return {"error": "Repository not initialized"}

        try:
            status = {
                "branch": self.repo.active_branch.name,
                "is_dirty": self.repo.is_dirty(),
                "untracked_files": self.repo.untracked_files,
                "modified_files": [item.a_path for item in self.repo.index.diff(None)],
                "staged_files": [item.a_path for item in self.repo.index.diff("HEAD")],
                "has_remote": len(self.repo.remotes) > 0
            }

            if status["has_remote"]:
                status["remote_url"] = self.repo.remotes.origin.url

            return status
        except Exception as e:
            logger.error(f"Error getting repository status: {e}")
            return {"error": str(e)}

    def add_files(self, file_patterns: List[str] = None):
        """
        Add files to staging area.

        Args:
            file_patterns: List of file patterns to add. If None, adds all changes.
        """
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        try:
            if file_patterns:
                self.repo.index.add(file_patterns)
            else:
                self.repo.git.add(A=True)

            logger.info(f"Files added to staging area")
            return True
        except Exception as e:
            logger.error(f"Error adding files: {e}")
            return False

    def commit(self, message: str, add_all: bool = False) -> bool:
        """
        Create a commit.

        Args:
            message: Commit message
            add_all: If True, stage all changes before committing
        """
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        try:
            if add_all:
                self.add_files()

            if not self.repo.is_dirty() and not self.repo.untracked_files:
                logger.info("No changes to commit")
                return True

            self.repo.index.commit(message)
            logger.info(f"Committed: {message}")
            return True
        except Exception as e:
            logger.error(f"Error creating commit: {e}")
            return False

    def commit_prompt(self, prompt_file: Path, sports: List[str]) -> bool:
        """
        Commit a generated prompt with automated message.

        Args:
            prompt_file: Path to the prompt file
            sports: List of sports for this prompt
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sports_str = ", ".join(sports)

        message = f"""Generated prompt for {sports_str} - {timestamp}

📊 Generated with PromptBuilder
Co-Authored-By: PromptBuilder <noreply@promptbuilder.com>"""

        try:
            # Add the specific prompt file
            relative_path = prompt_file.relative_to(self.repo_path)
            self.repo.index.add([str(relative_path)])

            # Commit
            return self.commit(message, add_all=False)
        except Exception as e:
            logger.error(f"Error committing prompt: {e}")
            return False

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """
        Push commits to remote repository.

        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
        """
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        if not self.config.github_token:
            logger.error("GitHub token not configured")
            return False

        try:
            if not branch:
                branch = self.repo.active_branch.name

            # Set up remote URL with token
            remote_obj = self._get_or_create_remote(remote)

            # Push
            logger.info(f"Pushing to {remote}/{branch}...")
            push_info = remote_obj.push(branch)[0]

            if push_info.flags & push_info.ERROR:
                logger.error(f"Push failed: {push_info.summary}")
                return False

            logger.info("Push successful")
            return True
        except Exception as e:
            logger.error(f"Error pushing to remote: {e}")
            return False

    def _get_or_create_remote(self, remote_name: str = "origin"):
        """Get or create a remote."""
        if remote_name in [r.name for r in self.repo.remotes]:
            return self.repo.remote(remote_name)

        # Create new remote
        username = self.config.github_username
        repo_name = self.config.github_repo
        token = self.config.github_token

        # Use HTTPS URL with token
        remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"

        try:
            remote = self.repo.create_remote(remote_name, remote_url)
            logger.info(f"Created remote: {remote_name}")
            return remote
        except Exception as e:
            logger.error(f"Error creating remote: {e}")
            raise

    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """
        Pull changes from remote repository.

        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
        """
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        try:
            if not branch:
                branch = self.repo.active_branch.name

            remote_obj = self._get_or_create_remote(remote)

            logger.info(f"Pulling from {remote}/{branch}...")
            remote_obj.pull(branch)

            logger.info("Pull successful")
            return True
        except Exception as e:
            logger.error(f"Error pulling from remote: {e}")
            return False

    def create_branch(self, branch_name: str, checkout: bool = True) -> bool:
        """
        Create a new branch.

        Args:
            branch_name: Name of the new branch
            checkout: If True, checkout the new branch
        """
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        try:
            new_branch = self.repo.create_head(branch_name)
            logger.info(f"Created branch: {branch_name}")

            if checkout:
                new_branch.checkout()
                logger.info(f"Checked out branch: {branch_name}")

            return True
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return False

    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout an existing branch."""
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        try:
            self.repo.heads[branch_name].checkout()
            logger.info(f"Checked out branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Error checking out branch: {e}")
            return False

    def get_recent_commits(self, count: int = 10) -> List[Dict[str, str]]:
        """Get recent commit history."""
        if not self.repo:
            return []

        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=count):
                commits.append({
                    "hash": commit.hexsha[:7],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d %H:%M:%S")
                })
            return commits
        except Exception as e:
            logger.error(f"Error getting commits: {e}")
            return []

    def sync_config(self) -> bool:
        """Sync configuration files to GitHub."""
        config_files = ["config.json", ".env.example"]
        message = f"Update configuration - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        try:
            # Add config files
            existing_files = [f for f in config_files if (self.repo_path / f).exists()]
            if not existing_files:
                logger.info("No config files to sync")
                return True

            self.repo.index.add(existing_files)

            # Commit if there are changes
            if self.repo.is_dirty():
                return self.commit(message, add_all=False)
            else:
                logger.info("No config changes to sync")
                return True
        except Exception as e:
            logger.error(f"Error syncing config: {e}")
            return False

    def init_remote_repo(self) -> bool:
        """Initialize connection to remote repository."""
        if not self.config.has_github_configured():
            logger.error("GitHub credentials not configured")
            return False

        try:
            # Check if remote already exists
            if "origin" in [r.name for r in self.repo.remotes]:
                logger.info("Remote already configured")
                return True

            # Create remote
            self._get_or_create_remote("origin")

            # Try to fetch to verify connection
            try:
                self.repo.remotes.origin.fetch()
                logger.info("Remote repository connected successfully")
                return True
            except GitCommandError:
                # Repository might not exist yet on GitHub
                logger.warning("Remote repository not accessible. It may need to be created on GitHub first.")
                return True

        except Exception as e:
            logger.error(f"Error initializing remote repository: {e}")
            return False


# Singleton instance
_github_sync: Optional[GitHubSync] = None


def get_github_sync() -> GitHubSync:
    """Get the GitHub sync singleton."""
    global _github_sync
    if _github_sync is None:
        _github_sync = GitHubSync()
    return _github_sync
