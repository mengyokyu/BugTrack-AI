from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __table_args__ = (db.CheckConstraint("role IN ('user', 'admin')", name="ck_user_role"),)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user", server_default="user")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    bugs = db.relationship("Bug", foreign_keys="Bug.created_by", backref="creator", lazy=True)
    assigned_bugs = db.relationship("Bug", foreign_keys="Bug.assigned_to", backref="assignee", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)
    projects = db.relationship("Project", backref="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    key = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False, default="")
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    bugs = db.relationship("Bug", backref="project", lazy=True)
    members = db.relationship("ProjectMember", backref="project", lazy=True, cascade="all, delete-orphan")


class ProjectMember(db.Model):
    __table_args__ = (db.UniqueConstraint("project_id", "user_id", name="uq_project_member"),)
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="member", server_default="member")


class Bug(db.Model):
    __table_args__ = (
        db.CheckConstraint("severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name="ck_bug_severity"),
        db.CheckConstraint("status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')", name="ck_bug_status"),
        db.Index("ix_bug_status_severity", "status", "severity"),
        db.Index("ix_bug_project_created", "project_id", "created_at"),
    )
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reproduction_steps = db.Column(db.Text, nullable=False, default="")
    expected_behavior = db.Column(db.Text, nullable=False, default="")
    actual_behavior = db.Column(db.Text, nullable=False, default="")
    severity = db.Column(db.String(20), default="MEDIUM", nullable=False)
    priority = db.Column(db.String(20), default="P2", nullable=False)
    status = db.Column(db.String(20), default="OPEN", nullable=False)
    environment = db.Column(db.String(120), default="development", nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    comments = db.relationship("Comment", backref="bug", lazy=True, cascade="all, delete-orphan")
    analyses = db.relationship("AIAnalysis", backref="bug", lazy=True, cascade="all, delete-orphan")
    activities = db.relationship("Activity", backref="bug", lazy=True, cascade="all, delete-orphan")


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bug_id = db.Column(db.Integer, db.ForeignKey("bug.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bug_id = db.Column(db.Integer, db.ForeignKey("bug.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.String(255), nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class AIAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bug_id = db.Column(db.Integer, db.ForeignKey("bug.id"), nullable=False, index=True)
    summary = db.Column(db.Text, nullable=False)
    possible_cause = db.Column(db.Text, nullable=False)
    suggested_fix = db.Column(db.Text, nullable=False)
    suggested_severity = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
