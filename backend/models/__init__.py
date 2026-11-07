"""Database models package"""
from flask_sqlalchemy import SQLAlchemy

# Backend logic
db = SQLAlchemy(
    engine_options={
        'connect_args': {
            'check_same_thread': False,  # Backend logic
            'timeout': 30,  # Backend logic
        },
        'pool_pre_ping': True,  # Backend logic
        'pool_recycle': 3600,  # Backend logic
        'pool_size': 10,
        'max_overflow': 50,
        'pool_timeout': 30,  # Backend logic
    }
)

from .project import Project
from .page import Page
from .task import Task
from .user_template import UserTemplate
from .page_image_version import PageImageVersion
from .material import Material
from .reference_file import ReferenceFile
from .settings import Settings
from .user_style_template import UserStyleTemplate
from .project_template_asset import ProjectTemplateAsset

__all__ = ['db', 'Project', 'Page', 'Task', 'UserTemplate', 'PageImageVersion', 'Material', 'ReferenceFile', 'Settings', 'UserStyleTemplate', 'ProjectTemplateAsset']