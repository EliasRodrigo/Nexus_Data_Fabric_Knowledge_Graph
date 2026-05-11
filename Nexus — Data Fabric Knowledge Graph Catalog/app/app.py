
from __future__ import annotations
import io
import os
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_file, flash
import pandas as pd

from app.services.data_service import (
    summary, global_search, entity_detail, dashboard_payload, graph_payload,
    quality, data_dictionary, export_search
)
from app.services.auth_service import (
    authenticate, login_required, role_required, audit, recent_audit
)

BASE_DIR = Path(__file__).resolve().parent.parent
app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET", "tcc-enterprise-secret")

@app.context_processor
def inject_user():
    return {"current_user": session.get("user")}

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = authenticate(username, password)
        if user:
            session["user"] = user
            audit(user["username"], "login", "Login realizado com sucesso")
            return redirect(url_for("home"))
        flash("Usuário ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    user = session.get("user")
    if user:
        audit(user["username"], "logout", "Logout")
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    q = request.args.get("q", "")
    entity = request.args.get("entity", "all")
    page = max(int(request.args.get("page", 1)), 1)
    per_page = 20
    results, total = global_search(q, entity, page=page, per_page=per_page)
    audit(session["user"]["username"], "search", f"entity={entity};q={q};page={page}")
    pages = max(1, (total + per_page - 1) // per_page)
    return render_template(
        "home.html",
        summary=summary(),
        q=q,
        entity=entity,
        page=page,
        pages=pages,
        total=total,
        rows=results.to_dict(orient="records"),
        columns=list(results.columns)
    )

@app.route("/dashboard")
@login_required
def dashboard():
    payload = dashboard_payload()
    audit(session["user"]["username"], "view_dashboard", "Acessou dashboard")
    return render_template("dashboard.html", payload=payload, summary=summary())

@app.route("/governance")
@login_required
def governance():
    dd = data_dictionary()
    audit(session["user"]["username"], "view_governance", "Acessou governança")
    return render_template("governance.html", rows=dd.to_dict(orient="records"), columns=list(dd.columns))

@app.route("/quality")
@login_required
def quality_page():
    q = quality()
    audit(session["user"]["username"], "view_quality", "Acessou qualidade")
    return render_template("quality.html", quality=q)

@app.route("/entity/<entity_type>/<int:entity_id>")
@login_required
def detail(entity_type, entity_id):
    sub, label, metrics = entity_detail(entity_type, entity_id)
    if sub is None:
        flash("Entidade não encontrada.")
        return redirect(url_for("home"))
    audit(session["user"]["username"], "view_detail", f"{entity_type}:{entity_id}")
    cols = [c for c in ["id_transacao","transacao_data","transacao_tipo","transacao_valor","id_contrato","contrato_valor","cliente_nome","cpf","nome_agencia","produto_nome","produto_tipo"] if c in sub.columns]
    sample = sub[cols].head(50)
    return render_template("detail.html", entity_type=entity_type, label=label, metrics=metrics, rows=sample.to_dict(orient="records"), columns=list(sample.columns), entity_id=entity_id)

@app.route("/graph")
@login_required
def graph():
    focus_type = request.args.get("focus_type", "cliente")
    focus_id = request.args.get("focus_id")
    focus_id = int(focus_id) if focus_id and str(focus_id).isdigit() else None
    payload = graph_payload(focus_type, focus_id)
    audit(session["user"]["username"], "view_graph", f"{focus_type}:{focus_id}")
    return render_template("graph.html", payload=payload, focus_type=focus_type, focus_id=focus_id)

@app.route("/export/search.csv")
@login_required
def export_csv():
    q = request.args.get("q", "")
    entity = request.args.get("entity", "all")
    df = export_search(q, entity)
    audit(session["user"]["username"], "export_csv", f"entity={entity};q={q}")
    bio = io.StringIO()
    df.to_csv(bio, index=False)
    mem = io.BytesIO(bio.getvalue().encode("utf-8-sig"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="resultado_busca.csv")

@app.route("/api/summary")
@login_required
def api_summary():
    return jsonify(summary())

@app.route("/api/quality")
@login_required
def api_quality():
    return jsonify(quality())

@app.route("/api/search")
@login_required
def api_search():
    q = request.args.get("q", "")
    entity = request.args.get("entity", "all")
    page = max(int(request.args.get("page", 1)), 1)
    rows, total = global_search(q, entity, page=page, per_page=20)
    return jsonify({"total": total, "page": page, "rows": rows.to_dict(orient="records")})

@app.route("/api/graph")
@login_required
def api_graph():
    focus_type = request.args.get("focus_type", "cliente")
    focus_id = request.args.get("focus_id")
    focus_id = int(focus_id) if focus_id and str(focus_id).isdigit() else None
    return jsonify(graph_payload(focus_type, focus_id))

@app.route("/admin/logs")
@role_required("admin")
def admin_logs():
    rows = recent_audit(200)
    return render_template("admin_logs.html", rows=rows)

@app.route("/admin/run-etl", methods=["POST"])
@role_required("admin")
def run_etl():
    etl_script = BASE_DIR / "src" / "etl" / "build_base.py"
    result = subprocess.run(["python", str(etl_script)], cwd=str(BASE_DIR), capture_output=True, text=True)
    audit(session["user"]["username"], "run_etl", f"returncode={result.returncode}")
    flash("ETL executado com sucesso." if result.returncode == 0 else "ETL executado com erro. Veja os logs.")
    return redirect(url_for("admin_logs"))

@app.route("/about")
@login_required
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
