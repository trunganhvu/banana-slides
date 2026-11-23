"""Database models package"""
from flask_sqlalchemy import SQLAlchemy

# Engine options are configured dynamically per database URI via app.config
db = SQLAlchemy()

from .project import Project
from .user import User
from .page import Page
from .task import Task
from .user_template import UserTemplate
from .page_image_version import PageImageVersion
from .material import Material
from .reference_file import ReferenceFile
from .settings import Settings
from .user_style_template import UserStyleTemplate
from .project_template_asset import ProjectTemplateAsset

__all__ = ['db', 'User', 'Project', 'Page', 'Task', 'UserTemplate', 'PageImageVersion', 'Material', 'ReferenceFile', 'Settings', 'UserStyleTemplate', 'ProjectTemplateAsset']