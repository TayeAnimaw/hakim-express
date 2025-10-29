"""add profile_picture column to users table

Revision ID: add_profile_picture_to_users
Revises: 
Create Date: 2024-05-10

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('profile_picture', sa.String(length=255), nullable=True))

def downgrade():
    op.drop_column('users', 'profile_picture')
