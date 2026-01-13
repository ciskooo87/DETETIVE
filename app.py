# app.py — mobile-first + UX upgrades + MENU FUNCIONAL (popover)
import json
import io
import binascii
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image, UnidentifiedImageError

# ---------------------------
# Config
# ---------------------------
st.set_page_config(
    page_title="Pousada Aurora — Investigação",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="collapsed",  # sidebar fica recolhida e não é necessária
)

ROOT = Path(__file__).parent
CONTENT_PATH = ROOT / "content" / "envelopes_ptbr.json"
ASSETS = ROOT / "assets" / "images"

BRAND = {
    "studio": "Aurora Narrative Games",
    "tagline": "Experiência de investigação. Decida antes da verdade.",
}

# ---------------------------
# CSS — mobile UX
# ---------------------------
st.markdown(
    """
<style>
.block-container { padding-top: 1rem; padding-bottom: 1.5rem; }
.stButton button { padding: 0.65rem 0.95rem; border-radius: 12px; }
@media (max-width: 768px) {
  h1 { font-size: 1.6rem !important; }
  h2 { font-size: 1.25rem !important; }
  h3 { font-size: 1.05rem !important; }
  .block-container { padding-left: 0.9rem; padding-right: 0.9rem; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Helpers
# ---------------------------
def load_content() -> dict:
    if not CONTENT_PATH.exists():
        st.error(
            f"Arquivo de conteúdo não encontrado: {CONTENT_PATH}\n\n"
            "Crie content/envelopes_ptbr.json (use o JSON do caso)."
        )
        st.stop()
    with open(CONTENT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def pick_image(stem: str) -> Path | None:
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = ASSETS / f"{stem}.{ext}"
        if p.exists():
            return p
    return None

def safe_image(path: Path | None, caption: str | None = None):
    if not path or not path.exists():
        return
    try:
        data = path.read_bytes()
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data))
        st.image(img, use_container_width=True, caption=caption)
    except (UnidentifiedImageError, OSError, ValueError):
        with st.container(border=True):
            st.caption("Imagem indisponível (arquivo inválido).")
            st.code(str(path))

def badge(status: str) -> str:
    m = {"Neutro": "⚪", "Suspeito": "🟠", "Prioritário": "🔴", "Descartado": "🟢"}
    return m.get(status, "⚪")

def init_state():
    if "initialized" in st.session_state:
        return
    st.session_state.initialized = True

    st.session_state.started = False
    st.session_state.current_env = 1
    st.session_state.max_opened_envelope = 0

    st.session_state.notes = ""
    st.session_state.timeline = []
    st.session_state.hypotheses = []

    st.session_state.suspects = {
        "Daniel Moreira": {"status": "Neutro", "notes": ""},
        "Laura Moreira": {"status": "Neutro", "notes": ""},
        "Proprietário (Sr. Álvaro)": {"status": "Neutro", "notes": ""},
    }

    st.session_state.decision_submitted = False
    st.session_state.decision = {
        "culprit": "",
        "method": "",
        "motive": "",
        "reasoning": "",
        "submitted_at": None,
    }

    st.session_state.nav_page = "🏠 Início"

def reset_state():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

def envelope_by_id(content: dict, env_id: int) -> dict:
    return next(e for e in content["envelopes"] if e["id"] == env_id)

def can_open(env_id: int) -> bool:
    return env_id <= st.session_state.max_opened_envelope

def all_unlocked() -> bool:
    return st.session_state.max_opened_envelope >= 6

def require_started():
    if not st.session_state.started:
        st.warning("Inicie o caso para acessar esta área.")
        st.stop()

def go(page_name: str):
    st.session_state.nav_page = page_name
    st.rerun()

# ---------------------------
# Boot
# ---------------------------
content = load_content()
init_state()

IMG = {
    "cover": pick_image("cover"),
    1: pick_image("envelope1"),
    2: pick_image("envelope2"),
    3: pick_image("envelope3"),
    4: pick_image("envelope4"),
    5: pick_image("envelope5"),
    6: pick_image("envelope6"),
    "closing": pick_image("closing"),
}

# ---------------------------
# TOP BAR with REAL menu (popover)
# ---------------------------
top = st.container()
with top:
    colA, colB, colC = st.columns([0.5, 0.25, 0.25])
    with colA:
        st.caption(f"© {BRAND['studio']}")
    with colB:
        if st.session_state.started:
            prog = st.session_state.max_opened_envelope / 6
            st.progress(prog, text=f"{int(prog*100)}%")
        else:
            st.caption(BRAND["tagline"])
    with colC:
        with st.popover("☰ Menu", use_container_width=True):
            pages = ["🏠 Início", "📦 Envelopes", "🗒️ Caderno", "✅ Decisão", "🔒 Fechamento"]
            current = st.session_state.nav_page
            idx = pages.index(current) if current in pages else 0

            sel = st.radio("Ir para", pages, index=idx)
            if sel != st.session_state.nav_page:
                st.session_state.nav_page = sel
                st.rerun()

            st.divider()

            if not st.session_state.started:
                st.info("Comece pelo caso.")
                if st.button("▶️ Iniciar caso", use_container_width=True):
                    st.session_state.started = True
                    st.session_state.max_opened_envelope = 1
                    st.session_state.current_env = 1
                    st.session_state.nav_page = "📦 Envelopes"
                    st.rerun()
            else:
                if st.button("🗒️ Abrir Caderno", use_container_width=True):
                    go("🗒️ Caderno")
                if st.button("🔄 Reiniciar caso", use_container_width=True):
                    reset_state()

st.divider()

# ---------------------------
# Pages
# ---------------------------
def page_home():
    st.markdown("# O Incidente da Pousada Aurora")
    st.caption("Uma investigação narrativa com informação fragmentada.")
    safe_image(IMG.get("cover"))

    with st.container(border=True):
        st.markdown("### Como funciona")
        st.markdown(
            "- Você recebe **envelopes** com contexto, depoimentos e provas.\n"
            "- As informações são liberadas em **ordem controlada**.\n"
            "- Você registra hipóteses, prioriza suspeitos e toma uma decisão final.\n"
            "- O **fechamento oficial** fica bloqueado até você enviar sua conclusão."
        )
        st.warning("Regra central: você só vê o fechamento **depois de decidir**.")

    if not st.session_state.started:
        st.info("Abra o **☰ Menu** e clique em **Iniciar caso**.")
    else:
        st.success("Caso iniciado. Vá para **Envelopes**.")

def page_envelopes():
    require_started()
    st.markdown("## 📦 Envelopes")
    st.caption("Abra na ordem. Confirme leitura para liberar o próximo.")

    with st.container(border=True):
        st.markdown("### Ordem de abertura")
        for env in content["envelopes"]:
            env_id = env["id"]
            allowed = can_open(env_id)
            short = env["title"].split("—")[-1].strip()
            label = f"Envelope {env_id} — {short}"
            if allowed:
                if st.button(f"📩 Abrir {label}", key=f"open_{env_id}", use_container_width=True):
                    st.session_state.current_env = env_id
                    st.rerun()
            else:
                st.button(f"🔒 {label}", disabled=True, use_container_width=True)

    env_id = st.session_state.current_env
    env = envelope_by_id(content, env_id)

    st.divider()
    safe_image(IMG.get(env_id))
    st.markdown(f"### {env['title']}")
    st.markdown(env["body"])

    with st.container(border=True):
        st.markdown("#### O que observar neste envelope")
        prompts = {
            1: "- Isolamento e vulnerabilidades do ambiente\n- Quem tem acesso a quê\n- Lacunas na linha do tempo",
            2: "- Experiência subjetiva vs. evidência\n- Gatilhos emocionais\n- Ruído narrativo",
            3: "- Minimizações e exageros\n- Omissões\n- Convergências",
            4: "- Vínculo físico\n- Janela temporal\n- Dinâmica do crime",
            5: "- Vetores alternativos (plausível ≠ provável)\n- Incentivos ocultos\n- Quem se beneficia",
            6: "- Rupturas temporais\n- Coerência final\n- Pós-evento",
        }
        st.markdown(prompts.get(env_id, "-"))

    st.divider()

    # Confirm reading
    if st.button("✅ Confirmar leitura", use_container_width=True):
        if st.session_state.max_opened_envelope == env_id and env_id < 6:
            st.session_state.max_opened_envelope += 1
        st.toast("Leitura confirmada.")
        st.rerun()

    # Next envelope button (below confirmation)
    next_id = min(env_id + 1, 6)
    next_allowed = can_open(next_id)
    if env_id >= 6:
        st.button("➡️ Próximo envelope (fim)", disabled=True, use_container_width=True)
    else:
        if st.button(f"➡️ Próximo envelope (Envelope {next_id})", disabled=not next_allowed, use_container_width=True):
            st.session_state.current_env = next_id
            st.rerun()

    # Quick notebook access
    if st.button("🗒️ Abrir Caderno do Investigador", use_container_width=True):
        go("🗒️ Caderno")

    with st.popover("🧠 Hipótese rápida"):
        txt = st.text_input("Escreva curto e objetivo", key="hyp_fast")
        if st.button("Salvar hipótese", use_container_width=True) and txt.strip():
            st.session_state.hypotheses.append({"at": datetime.now().isoformat(), "text": txt.strip()})
            st.toast("Hipótese registrada.")
            st.rerun()

def page_notebook():
    require_started()
    st.markdown("## 🗒️ Caderno do Investigador")
    st.caption("Hipóteses provisórias. Mudança de opinião é maturidade analítica.")

    with st.container(border=True):
        st.markdown("### Notas gerais")
        st.session_state.notes = st.text_area(
            "Registre hipóteses, contradições, dúvidas e próximos passos.",
            value=st.session_state.notes,
            height=180,
        )

    st.divider()
    with st.container(border=True):
        st.markdown("### 🧩 Hipóteses rápidas")
        if not st.session_state.hypotheses:
            st.caption("Nenhuma hipótese registrada ainda.")
        else:
            for item in reversed(st.session_state.hypotheses[-15:]):
                st.markdown(f"- {item['text']}")

    st.divider()
    with st.container(border=True):
        st.markdown("### 🕒 Linha do tempo")
        with st.form("timeline_form", clear_on_submit=True):
            t = st.text_input("Evento (ex: 00h05 — discussão na recepção)")
            ok = st.form_submit_button("Adicionar")
            if ok and t.strip():
                st.session_state.timeline.append({"at": datetime.now().isoformat(), "event": t.strip()})
                st.toast("Evento adicionado.")
                st.rerun()

        if st.session_state.timeline:
            for i, item in enumerate(reversed(st.session_state.timeline[-12:]), start=1):
                st.write(f"{i}. {item['event']}")
        else:
            st.caption("Sem eventos ainda.")

    st.divider()
    with st.container(border=True):
        st.markdown("### 🎯 Suspeitos")
        for name, data in st.session_state.suspects.items():
            st.markdown(f"**{name}** {badge(data['status'])}")
            new_status = st.selectbox(
                "Status",
                ["Neutro", "Suspeito", "Prioritário", "Descartado"],
                index=["Neutro", "Suspeito", "Prioritário", "Descartado"].index(data["status"]),
                key=f"status_{name}",
            )
            st.session_state.suspects[name]["status"] = new_status
            st.session_state.suspects[name]["notes"] = st.text_area(
                "Notas (provas e lógica)",
                value=data["notes"],
                key=f"notes_{name}",
                height=80,
                placeholder="Ex: Digitais na arma + janela temporal + ruptura narrativa…",
            )
            st.divider()

def page_decision():
    require_started()
    st.markdown("## ✅ Decisão final")
    st.caption("O fechamento oficial só libera depois da sua conclusão.")

    if not all_unlocked():
        st.warning("Você ainda não liberou todos os envelopes. Termine o Envelope 6 para decidir.")
        return

    st.warning("Momento da decisão: preencha tudo. Sem campos vazios.")

    with st.container(border=True):
        with st.form("decision_form"):
            culprit = st.selectbox(
                "Quem é o culpado?",
                ["", "Daniel Moreira", "Laura Moreira", "Proprietário (Sr. Álvaro)", "Outro/Indeterminado"],
                index=0,
            )
            method = st.text_input("Como foi o crime? (método/objeto/dinâmica)")
            motive = st.text_input("Qual foi o motivo?")
            reasoning = st.text_area(
                "Justificativa (por que sua hipótese explica melhor as provas?)",
                height=160,
            )
            ok = st.form_submit_button("📌 Enviar decisão")
            if ok:
                if not culprit or not method.strip() or not motive.strip() or not reasoning.strip():
                    st.error("Preencha todos os campos.")
                else:
                    st.session_state.decision_submitted = True
                    st.session_state.decision = {
                        "culprit": culprit,
                        "method": method.strip(),
                        "motive": motive.strip(),
                        "reasoning": reasoning.strip(),
                        "submitted_at": datetime.now().isoformat(),
                    }
                    st.success("Decisão registrada. Fechamento desbloqueado.")
                    st.rerun()

    if st.session_state.decision_submitted:
        st.divider()
        d = st.session_state.decision
        with st.container(border=True):
            st.markdown("### 📄 Sua decisão registrada")
            st.write(f"**Culpado:** {d['culprit']}")
            st.write(f"**Método:** {d['method']}")
            st.write(f"**Motivo:** {d['motive']}")
            st.write("**Justificativa:**")
            st.write(d["reasoning"])

def page_closing():
    require_started()
    st.markdown("## 🔒 Fechamento Oficial do Caso")
    if not st.session_state.decision_submitted:
        st.info("Bloqueado até você enviar sua decisão.")
        return

    safe_image(IMG.get("closing"))
    st.markdown("### A verdade não espera por consenso.")

    with st.container(border=True):
        st.markdown(f"## {content['closing']['title']}")
        st.markdown(content["closing"]["body"])

    st.caption("Fim do caso. Reinicie para jogar novamente com outra hipótese.")

# ---------------------------
# Router
# ---------------------------
page = st.session_state.nav_page

if page == "🏠 Início":
    page_home()
elif page == "📦 Envelopes":
    page_envelopes()
elif page == "🗒️ Caderno":
    page_notebook()
elif page == "✅ Decisão":
    page_decision()
else:
    page_closing()
