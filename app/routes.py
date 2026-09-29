from functools import wraps
from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for
from .extensions import db
from .models import User, Bug, Comment, AIAnalysis
from .ai import analyze_bug
from .metrics import metrics_response
bp = Blueprint("main", __name__)
SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}; STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}
def current_user(): return db.session.get(User, session.get("user_id")) if session.get("user_id") else None
def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not current_user(): return jsonify(error="authentication_required"), 401
        return fn(*a, **kw)
    return wrapper
def bug_json(b): return {"id":b.id,"title":b.title,"description":b.description,"severity":b.severity,"status":b.status,"environment":b.environment,"created_by":b.created_by,"created_at":b.created_at.isoformat(),"updated_at":b.updated_at.isoformat()}
@bp.get("/")
def index(): return redirect(url_for("main.dashboard"))
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
    d = request.get_json(silent=True) or {}
    if not d.get("name") or not d.get("email") or len(d.get("password", "")) < 8: return jsonify(error="name, email and an 8-character password are required"), 400
    email = d["email"].strip().lower()
    if User.query.filter_by(email=email).first(): return jsonify(error="email already registered"), 409
    u = User(name=d["name"].strip(), email=email); u.set_password(d["password"]); db.session.add(u); db.session.commit(); session["user_id"] = u.id
    return jsonify(id=u.id, name=u.name, email=u.email), 201
@bp.post("/api/auth/login")
def login():
    d = request.get_json(silent=True) or {}; u = User.query.filter_by(email=d.get("email", "").lower()).first()
    if not u or not u.check_password(d.get("password", "")): return jsonify(error="invalid credentials"), 401
    session["user_id"] = u.id; return jsonify(id=u.id, name=u.name, email=u.email)
@bp.post("/api/auth/logout")
def logout(): session.clear(); return jsonify(message="logged out")
@bp.get("/api/auth/me")
def me():
    u = current_user(); return jsonify(id=u.id, name=u.name, email=u.email) if u else (jsonify(error="authentication_required"), 401)
@bp.get("/health")
def health():
    try: db.session.execute(db.text("SELECT 1")); return jsonify(status="ok", database="ok")
    except Exception: return jsonify(status="degraded", database="unavailable"), 503
@bp.get("/metrics")
def metrics(): return metrics_response()
@bp.get("/api/bugs")
@login_required
def list_bugs(): return jsonify([bug_json(b) for b in Bug.query.order_by(Bug.created_at.desc()).all()])
@bp.post("/api/bugs")
@login_required
def create_bug():
    d = request.get_json(silent=True) or {}
    if not d.get("title") or not d.get("description"): return jsonify(error="title and description are required"), 400
    if d.get("severity", "MEDIUM") not in SEVERITIES: return jsonify(error="invalid severity"), 400
    b = Bug(title=d["title"].strip(), description=d["description"].strip(), severity=d.get("severity", "MEDIUM"), environment=d.get("environment", "development"), created_by=current_user().id)
    db.session.add(b); db.session.commit(); return jsonify(bug_json(b)), 201
@bp.get("/api/bugs/<int:bug_id>")
@login_required
def get_bug(bug_id):
    b = db.get_or_404(Bug, bug_id); out = bug_json(b)
    out["comments"] = [{"id":c.id,"content":c.content,"author":c.author.name,"created_at":c.created_at.isoformat()} for c in b.comments]
    if b.analyses:
        a = b.analyses[-1]; out["analysis"] = {k:getattr(a,k) for k in ("summary","possible_cause","suggested_fix","suggested_severity")}
    else: out["analysis"] = None
    return jsonify(out)
@bp.put("/api/bugs/<int:bug_id>")
@login_required
def update_bug(bug_id):
    b = db.get_or_404(Bug, bug_id); d = request.get_json(silent=True) or {}
    for field in ("title", "description", "environment"):
        if d.get(field): setattr(b, field, d[field])
    if "severity" in d:
        if d["severity"] not in SEVERITIES: return jsonify(error="invalid severity"), 400
        b.severity = d["severity"]
    if "status" in d:
        if d["status"] not in STATUSES: return jsonify(error="invalid status"), 400
        b.status = d["status"]
    db.session.commit(); return jsonify(bug_json(b))
@bp.delete("/api/bugs/<int:bug_id>")
@login_required
def delete_bug(bug_id): db.session.delete(db.get_or_404(Bug, bug_id)); db.session.commit(); return jsonify(message="deleted")
@bp.post("/api/bugs/<int:bug_id>/comments")
@login_required
def add_comment(bug_id):
    b = db.get_or_404(Bug, bug_id); d = request.get_json(silent=True) or {}
    if not d.get("content"): return jsonify(error="content is required"), 400
    c = Comment(bug_id=b.id, user_id=current_user().id, content=d["content"].strip()); db.session.add(c); db.session.commit(); return jsonify(id=c.id, content=c.content), 201
@bp.post("/api/bugs/<int:bug_id>/analyze")
@login_required
def ai_analyze(bug_id):
    b = db.get_or_404(Bug, bug_id)
    try: data = analyze_bug(b.title, b.description)
    except Exception: return jsonify(error="AI analysis unavailable"), 503
    a = AIAnalysis(bug_id=b.id, **data); db.session.add(a); db.session.commit(); return jsonify({k:getattr(a,k) for k in ("summary","possible_cause","suggested_fix","suggested_severity")})
