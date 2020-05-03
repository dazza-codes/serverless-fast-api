"""
Configure the invoke release task
"""

from invoke_release.tasks import *  # noqa: F403
from invoke_release.plugins import PatternReplaceVersionInFilesPlugin

configure_release_parameters(  # noqa: F405
    display_name="Serverless AWS FastAPI",
    module_name="example_app",
    plugins=[
        PatternReplaceVersionInFilesPlugin(
            "pyproject.toml",
            "README.md",
            "Makefile",
            "example_app/version.py",
            "terraform/variables.tf",
        )
    ],
)
