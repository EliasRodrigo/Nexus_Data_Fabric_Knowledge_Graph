"""Nexus — Data Fabric Knowledge Graph Catalog — Flask app."""
from __future__ import annotations
import io, os, subprocess, sys, secrets
from pathlib import Path
from flask import (Flask, render_template, request, session,
                   redirect, url_for, jsonify, send_file, flash, abort)

from app.services.data_service import (
    summary, global_search, entity_detail, dashboard_payload,
    graph_payload, quality, data_dictionary, export_search, fraud_stats,
)
from app.services.auth_service import (
    authenticate, login_required, role_required, audit, recent_audit,
)

BASE_DIR = Path(__file__).resolve().parent.parent
app = Flask(__name__)
_key = os.environ.get("NEXUS_SECRET_KEY", "")
app.secret_key = _key if _key else secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=3600,
)

@app.context_processor
def inject_user():
    return {"current_user": session.get("user")}

# ── Auth ───────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = authenticate(request.form.get("username","").strip(), request.form.get("password",""))
        if user:
            session.permanent = True
            session["user"] = user
            audit(user["username"],"login",f"ip={request.remote_addr}")
            return redirect(url_for("home"))
        flash("Usuário ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    if u := session.get("user"):
        audit(u["username"],"logout","")
    session.clear()
    return redirect(url_for("login"))

# ── Catálogo ───────────────────────────────────────────────────────────
@app.route("/")
@login_required
def home():
    q=request.args.get("q",""); entity=request.args.get("entity","all")
    page=max(int(request.args.get("page",1)),1)
    rows,total = global_search(q,entity,page=page,per_page=20)
    pages=max(1,(total+19)//20)
    if q: audit(session["user"]["username"],"search",f"q={q};entity={entity}")
    return render_template("home.html",q=q,entity=entity,page=page,pages=pages,
                           total=total,rows=rows.to_dict(orient="records"),
                           columns=list(rows.columns),summary=summary())

@app.route("/dashboard")
@login_required
def dashboard():
    payload=dashboard_payload()
    audit(session["user"]["username"],"view","dashboard")
    return render_template("dashboard.html",payload=payload)

@app.route("/fraud")
@login_required
def fraud_page():
    q=request.args.get("q",""); page=max(int(request.args.get("page",1)),1)
    rows,total=global_search(q,"fraude",page=page,per_page=25)
    pages=max(1,(total+24)//25)
    audit(session["user"]["username"],"view","fraud")
    return render_template("fraud.html",rows=rows.to_dict(orient="records"),
                           total=total,page=page,pages=pages,q=q,stats=fraud_stats())

@app.route("/graph")
@login_required
def graph():
    ft=request.args.get("focus_type","cliente")
    raw=request.args.get("focus_id")
    fid=int(raw) if raw and raw.isdigit() else None
    payload=graph_payload(ft,fid)
    audit(session["user"]["username"],"view",f"graph:{ft}:{fid}")
    return render_template("graph.html",payload=payload,focus_type=ft,focus_id=fid)

@app.route("/governance")
@login_required
def governance():
    dd=data_dictionary()
    audit(session["user"]["username"],"view","governance")
    return render_template("governance.html",dict_rows=dd.to_dict(orient="records"))

@app.route("/quality")
@login_required
def quality_page():
    audit(session["user"]["username"],"view","quality")
    return render_template("quality.html",quality_data=quality())

@app.route("/sources")
@login_required
def sources():
    return render_template("sources.html")

@app.route("/entity/<entity_type>/<int:entity_id>")
@login_required
def detail(entity_type,entity_id):
    sub,label,metrics=entity_detail(entity_type,entity_id)
    if sub is None: abort(404)
    audit(session["user"]["username"],"view_entity",f"{entity_type}:{entity_id}")
    show=["id_transacao","transacao_data","transacao_tipo","transacao_valor","fraude","nome_agencia","produto_nome"]
    show=[c for c in show if c in sub.columns]
    return render_template("detail.html",entity_type=entity_type,label=label,metrics=metrics,
                           rows=sub[show].head(50).to_dict(orient="records"),
                           columns=show,entity_id=entity_id)

# ── Export ─────────────────────────────────────────────────────────────
@app.route("/export/search.csv")
@login_required
def export_csv():
    q=request.args.get("q",""); entity=request.args.get("entity","all")
    df=export_search(q,entity)
    audit(session["user"]["username"],"export_csv",f"q={q}")
    buf=io.BytesIO(df.to_csv(index=False).encode("utf-8-sig"))
    return send_file(buf,mimetype="text/csv",as_attachment=True,download_name="nexus_export.csv")

@app.route("/export/frauds.csv")
@login_required
def export_frauds():
    df=export_search("","fraude")
    audit(session["user"]["username"],"export_frauds","")
    buf=io.BytesIO(df.to_csv(index=False).encode("utf-8-sig"))
    return send_file(buf,mimetype="text/csv",as_attachment=True,download_name="nexus_fraudes.csv")

# ── API ─────────────────────────────────────────────────────────────────
@app.route("/api/v1/summary")
@login_required
def api_summary(): return jsonify(summary())

@app.route("/api/v1/quality")
@login_required
def api_quality(): return jsonify(quality())

@app.route("/api/v1/fraud-stats")
@login_required
def api_fraud(): return jsonify(fraud_stats())

@app.route("/api/v1/graph")
@login_required
def api_graph():
    ft=request.args.get("focus_type","cliente")
    fid=request.args.get("focus_id")
    fid=int(fid) if fid and fid.isdigit() else None
    return jsonify(graph_payload(ft,fid))

@app.route("/health")
def health(): return jsonify({"status":"ok","service":"nexus"})

# ── Admin ───────────────────────────────────────────────────────────────
@app.route("/admin/logs")
@role_required("admin")
def admin_logs():
    return render_template("admin_logs.html",rows=recent_audit(300))

@app.route("/admin/run-etl",methods=["POST"])
@role_required("admin")
def run_etl():
    etl=BASE_DIR/"src"/"etl"/"build_nexus.py"
    res=subprocess.run([sys.executable,str(etl)],cwd=str(BASE_DIR),capture_output=True,text=True)
    audit(session["user"]["username"],"run_etl",f"rc={res.returncode}")
    flash("ETL executado com sucesso ✅" if res.returncode==0 else "Erro no ETL — veja logs.")
    return redirect(url_for("admin_logs"))


@app.route("/about")
@login_required
def about():
    return render_template("about.html", summary=summary())

@app.errorhandler(404)
def not_found(e):
    return render_template("home.html",q="",entity="all",page=1,pages=1,
                           total=0,rows=[],columns=[],summary=summary()),404

if __name__=="__main__":
    debug=os.environ.get("NEXUS_DEBUG","0")=="1"
    app.run(debug=debug,host="127.0.0.1",port=5000)
