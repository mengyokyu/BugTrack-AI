from functools import wraps
import re

from flask import Blueprint, current_app, jsonify, render_template, redirect, request, session, url_for
from sqlalchemy import or_

from .ai import analyze_bug
from .extensions import db, limiter
from .metrics import BUG_EVENTS, DATABASE, metrics_response
from .models import Activity, AIAnalysis, Bug, Comment, Project, ProjectMember, User

bp = Blueprint("main", __name__)
SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}
PRIORITIES = {"P0", "P1", "P2", "P3"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def current_user():
    return db.session.get(User, session.get("user_id")) if session.get("user_id") else None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify(error="authentication_required"), 401
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user().role != "admin":
            return jsonify(error="admin_required"), 403
        return fn(*args, **kwargs)
    return wrapper


def can_access_bug(bug):
    user = current_user()
    return user and (user.role == "admin" or bug.created_by == user.id or bug.assigned_to == user.id or (bug.project and (bug.project.owner_id == user.id or any(member.user_id == user.id for member in bug.project.members))))


def accessible_bug(bug_id):
    bug = db.session.get(Bug, bug_id)
    if not bug:
        return None, (jsonify(error="not_found"), 404)
    if not can_access_bug(bug):
        return None, (jsonify(error="forbidden"), 403)
    return bug, None


def bug_json(bug):
    return {
        "id": bug.id, "title": bug.title, "description": bug.description,
        "reproduction_steps": bug.reproduction_steps, "expected_behavior": bug.expected_behavior,
        "actual_behavior": bug.actual_behavior, "severity": bug.severity, "priority": bug.priority,
        "status": bug.status, "environment": bug.environment, "created_by": bug.created_by,
        "assigned_to": bug.assigned_to, "project_id": bug.project_id,
        "created_at": bug.created_at.isoformat(), "updated_at": bug.updated_at.isoformat(),
    }


def add_activity(bug, action, details=""):
    db.session.add(Activity(bug_id=bug.id, user_id=current_user().id, action=action, details=details[:255]))


@bp.get("/")
def index():
    return redirect(url_for("main.dashboard"))


@bp.get("/login")
def login_page(): return render_template("login.html")


@bp.get("/register")
def register_page(): return render_template("register.html")


@bp.get("/dashboard")
@login_required
def dashboard(): return render_template("dashboard.html")


@bp.get("/bugs")
@login_required
def bugs_page(): return render_template("bugs.html")


@bp.get("/bugs/create")
@login_required
def create_page(): return render_template("bug-form.html")


@bp.get("/bugs/<int:bug_id>")
@login_required
def detail_page(bug_id): return render_template("bug-detail.html", bug_id=bug_id)


@bp.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not name or len(name) > 120 or not EMAIL_RE.match(email) or len(password) < 8 or len(password) > 128:
        return jsonify(error="valid name, email, and an 8-128 character password are required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error="email already registered"), 409
    role = "admin" if email == current_app.config.get("ADMIN_EMAIL", "") else "user"
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    session.clear()
    session["user_id"] = user.id
    return jsonify(id=user.id, name=user.name, email=user.email, role=user.role), 201


@bp.post("/api/auth/login")
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(str(data.get("password", ""))):
        return jsonify(error="invalid credentials"), 401
    session.clear()
    session["user_id"] = user.id
    return jsonify(id=user.id, name=user.name, email=user.email, role=user.role)


@bp.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify(message="logged out")


@bp.get("/api/auth/csrf")
def csrf():
    session.setdefault("csrf_token", __import__("secrets").token_urlsafe(32))
    return jsonify(csrf_token=session["csrf_token"])


@bp.get("/api/auth/me")
def me():
    user = current_user()
    if not user:
        return jsonify(error="authentication_required"), 401
    return jsonify(id=user.id, name=user.name, email=user.email, role=user.role)


@bp.get("/health/live")
def health_live(): return jsonify(status="ok")


@bp.get("/health/ready")
def health_ready():
    try:
        db.session.execute(db.text("SELECT 1"))
        DATABASE.set(1)
        return jsonify(status="ready", database="ok")
    except Exception:
        DATABASE.set(0)
        return jsonify(status="not_ready", database="unavailable"), 503


@bp.get("/health")
def health(): return health_ready()


@bp.get("/metrics")
def metrics(): return metrics_response()


@bp.get("/api/projects")
@login_required
def list_projects():
    user = current_user()
    query = Project.query if user.role == "admin" else Project.query.outerjoin(ProjectMember).filter(or_(Project.owner_id == user.id, ProjectMember.user_id == user.id)).distinct()
    return jsonify([{"id": p.id, "name": p.name, "key": p.key, "description": p.description, "owner_id": p.owner_id} for p in query.order_by(Project.name).all()])


@bp.post("/api/projects")
@login_required
def create_project():
    data = request.get_json(silent=True) or {}
    name, key = str(data.get("name", "")).strip(), str(data.get("key", "")).strip().upper()
    if not name or not re.match(r"^[A-Z][A-Z0-9_-]{1,19}$", key):
        return jsonify(error="name and a valid project key are required"), 400
    if Project.query.filter_by(key=key).first(): return jsonify(error="project key already exists"), 409
    project = Project(name=name, key=key, description=str(data.get("description", "")).strip()[:2000], owner_id=current_user().id)
    db.session.add(project); db.session.flush()
    db.session.add(ProjectMember(project_id=project.id, user_id=current_user().id, role="owner"))
    db.session.commit()
    return jsonify(id=project.id, name=project.name, key=project.key), 201


@bp.post("/api/projects/<int:project_id>/members")
@login_required
def add_project_member(project_id):
    project = db.session.get(Project, project_id)
    if not project: return jsonify(error="not_found"), 404
    user = current_user()
    if user.role != "admin" and project.owner_id != user.id: return jsonify(error="forbidden"), 403
    data = request.get_json(silent=True) or {}
    member = db.session.get(User, data.get("user_id"))
    if not member: return jsonify(error="user_not_found"), 404
    if ProjectMember.query.filter_by(project_id=project.id, user_id=member.id).first(): return jsonify(error="already_member"), 409
    role = str(data.get("role", "member"))
    if role not in {"member", "viewer"}: return jsonify(error="invalid_member_role"), 400
    db.session.add(ProjectMember(project_id=project.id, user_id=member.id, role=role)); db.session.commit()
    return jsonify(project_id=project.id, user_id=member.id, role=role), 201


@bp.get("/api/bugs")
@login_required
def list_bugs():
    user = current_user()
    query = Bug.query if user.role == "admin" else Bug.query.outerjoin(Project, Bug.project_id == Project.id).outerjoin(ProjectMember, Project.id == ProjectMember.project_id).filter(or_(Bug.created_by == user.id, Bug.assigned_to == user.id, Project.owner_id == user.id, ProjectMember.user_id == user.id)).distinct()
    search = str(request.args.get("q", "")).strip()
    if search: query = query.filter(or_(Bug.title.ilike(f"%{search}%"), Bug.description.ilike(f"%{search}%")))
    for field, values in (("status", STATUSES), ("severity", SEVERITIES), ("priority", PRIORITIES)):
        value = request.args.get(field)
        if value in values: query = query.filter(getattr(Bug, field) == value)
    if request.args.get("project_id", "").isdigit(): query = query.filter_by(project_id=int(request.args["project_id"]))
    sort = request.args.get("sort", "newest")
    query = query.order_by(Bug.title.asc() if sort == "title" else Bug.created_at.asc() if sort == "oldest" else Bug.created_at.desc())
    page = max(int(request.args.get("page", 1) or 1), 1)
    per_page = min(max(int(request.args.get("per_page", 20) or 20), 1), 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(items=[bug_json(b) for b in pagination.items], page=page, per_page=per_page, total=pagination.total, pages=pagination.pages)


@bp.post("/api/bugs")
@login_required
def create_bug():
    data = request.get_json(silent=True) or {}
    title, description = str(data.get("title", "")).strip(), str(data.get("description", "")).strip()
    if not title or not description or len(title) > 200: return jsonify(error="title and description are required"), 400
    severity, status, priority = data.get("severity", "MEDIUM"), data.get("status", "OPEN"), data.get("priority", "P2")
    if severity not in SEVERITIES or status not in STATUSES or priority not in PRIORITIES: return jsonify(error="invalid severity, status, or priority"), 400
    project_id = data.get("project_id")
    if project_id is not None:
        project = db.session.get(Project, project_id)
        if not project or (current_user().role != "admin" and project.owner_id != current_user().id and not any(member.user_id == current_user().id and member.role == "member" for member in project.members)): return jsonify(error="project_forbidden"), 403
    bug = Bug(title=title, description=description, severity=severity, status=status, priority=priority,
              environment=str(data.get("environment", "development")).strip()[:120],
              reproduction_steps=str(data.get("reproduction_steps", "")).strip(),
              expected_behavior=str(data.get("expected_behavior", "")).strip(),
              actual_behavior=str(data.get("actual_behavior", "")).strip(), project_id=project_id,
              created_by=current_user().id)
    db.session.add(bug); db.session.flush(); add_activity(bug, "created"); db.session.commit(); BUG_EVENTS.labels("created").inc()
    return jsonify(bug_json(bug)), 201


@bp.get("/api/bugs/<int:bug_id>")
@login_required
def get_bug(bug_id):
    bug, error = accessible_bug(bug_id)
    if error: return error
    output = bug_json(bug)
    output["comments"] = [{"id": c.id, "content": c.content, "author": c.author.name, "created_at": c.created_at.isoformat()} for c in bug.comments]
    output["activities"] = [{"action": a.action, "details": a.details, "created_at": a.created_at.isoformat()} for a in bug.activities]
    output["analysis"] = None if not bug.analyses else {k: getattr(bug.analyses[-1], k) for k in ("summary", "possible_cause", "suggested_fix", "suggested_severity")}
    return jsonify(output)


@bp.put("/api/bugs/<int:bug_id>")
@login_required
def update_bug(bug_id):
    bug, error = accessible_bug(bug_id)
    if error: return error
    data = request.get_json(silent=True) or {}
    allowed = ("title", "description", "environment", "reproduction_steps", "expected_behavior", "actual_behavior")
    for field in allowed:
        if field in data: setattr(bug, field, str(data[field]).strip())
    for field, values in (("severity", SEVERITIES), ("status", STATUSES), ("priority", PRIORITIES)):
        if field in data:
            if data[field] not in values: return jsonify(error=f"invalid {field}"), 400
            setattr(bug, field, data[field])
    if "assigned_to" in data:
        assignee = db.session.get(User, data["assigned_to"]) if data["assigned_to"] else None
        if data["assigned_to"] and not assignee: return jsonify(error="assignee_not_found"), 400
        bug.assigned_to = assignee.id if assignee else None
    add_activity(bug, "updated", "bug fields changed"); db.session.commit()
    if bug.status == "RESOLVED": BUG_EVENTS.labels("resolved").inc()
    return jsonify(bug_json(bug))


@bp.delete("/api/bugs/<int:bug_id>")
@login_required
def delete_bug(bug_id):
    bug, error = accessible_bug(bug_id)
    if error: return error
    db.session.delete(bug); db.session.commit(); BUG_EVENTS.labels("deleted").inc()
    return jsonify(message="deleted")


@bp.post("/api/bugs/<int:bug_id>/comments")
@login_required
def add_comment(bug_id):
    bug, error = accessible_bug(bug_id)
    if error: return error
    content = str((request.get_json(silent=True) or {}).get("content", "")).strip()
    if not content or len(content) > 4000: return jsonify(error="content is required and must be under 4000 characters"), 400
    db.session.add(Comment(bug_id=bug.id, user_id=current_user().id, content=content)); add_activity(bug, "commented"); db.session.commit()
    return jsonify(message="comment added"), 201


@bp.post("/api/bugs/<int:bug_id>/analyze")
@login_required
@limiter.limit("10 per minute")
def ai_analyze(bug_id):
    bug, error = accessible_bug(bug_id)
    if error: return error
    try: data = analyze_bug(bug.title, bug.description)
    except Exception: return jsonify(error="AI analysis unavailable"), 503
    analysis = AIAnalysis(bug_id=bug.id, **data); db.session.add(analysis); add_activity(bug, "ai_analysis"); db.session.commit()
    return jsonify({k: getattr(analysis, k) for k in ("summary", "possible_cause", "suggested_fix", "suggested_severity")})
