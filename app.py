# app.py
# Pousada Aurora — Investigação (Streamlit)
# Versão polida: capa, imagens por envelope, progresso, UX premium, decisão ritualizada, fechamento bloqueado.

import json
from pathlib import Path
from datetime import datetime

import streamlit as st

import io
from PIL import Image, UnidentifiedImageError


# ---------------------------
# Config
# ---------------------------
st.set_page_config(
    page_title="Pousada Aurora — Investigação",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent
CONTENT_PATH = ROOT / "content" / "envelopes_ptbr.json"
ASSETS = ROOT / "assets" / "images"

# Nomes esperados das imagens (coloque arquivos com esses nomes em assets/images/)
def pick_image(stem: str) -> Path | None:
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = ASSETS / f"{stem}.{ext}"
        if p.exists():
            return p
    return None

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


BRAND = {
    "studio": "Aurora Narrative Games",
    "tagline": "Experiência de investigação. Decida antes da verdade.",
}


# ---------------------------
# Helpers
# ---------------------------
def load_content() -> dict:
    if not CONTENT_PATH.exists():
        st.error(
            f"Arquivo de conteúdo não encontrado: {CONTENT_PATH}\n\n"
            "Crie content/envelopes_ptbr.json (use o JSON que você já montou)."
        )
        st.stop()
    with open(CONTENT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_image(path: Path, caption: str | None = None):
    """Renderiza imagem se existir e for válida. Se não, não quebra o app."""
    if not path:
        return
    if not path.exists():
        return

    try:
        data = path.read_bytes()
        img = Image.open(io.BytesIO(data))
        img.verify()  # valida estrutura

        # reabre após verify
        img = Image.open(io.BytesIO(data))
        st.image(img, use_container_width=True, caption=caption)

    except (UnidentifiedImageError, OSError, ValueError):
        # fallback visual, sem quebrar o app
        with st.container(border=True):
            st.caption("Imagem indisponível (arquivo inválido).")
            st.code(str(path))

    else:
        # Mantém o layout sem poluir demais
        st.caption("")


def badge(status: str) -> str:
    m = {
        "Neutro": "⚪",
        "Suspeito": "🟠",
        "Prioritário": "🔴",
        "Descartado": "🟢",
    }
    return m.get(status, "⚪")


def init_state():
    if "initialized" in st.session_state:
        return

    st.session_state.initialized = True
    st.session_state.started = False
    st.session_state.current_env = 1
    st.session_state.max_opened_envelope = 0

    st.session_state.notes = ""
    st.session_state.timeline = []  # list[{"at": iso, "event": str}]
    st.session_state.hypotheses = []  # list[{"at": iso, "text": str}]

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
        st.warning("Inicie o caso pelo menu lateral para acessar esta área.")
        st.stop()


# ---------------------------
# Content + State
# ---------------------------
content = load_content()
init_state()

# ---------------------------
# Minimal styling (Streamlit-safe)
# ---------------------------
st.markdown(
    """
<style>
/* Slightly tighten default spacing and improve typography rhythm */
.block-container { padding-top: 1.25rem; padding-bottom: 2rem; }
h1, h2, h3 { letter-spacing: -0.2px; }
[data-testid="stSidebar"] { padding-top: 1rem; }
.smallcaps { font-variant: small-caps; letter-spacing: 0.8px; }
.muted { opacity: 0.78; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.markdown("## 🕵️ Pousada Aurora")
    st.caption(BRAND["tagline"])

    st.divider()

    if not st.session_state.started:
        st.info("Clique para iniciar e liberar o Envelope 1.")
        if st.button("▶️ Iniciar caso", use_container_width=True):
            st.session_state.started = True
            st.session_state.max_opened_envelope = 1
            st.session_state.current_env = 1
            st.rerun()
    else:
        st.success("Caso em andamento")
        prog = st.session_state.max_opened_envelope / 6
        st.progress(prog, text=f"Progresso da investigação: {int(prog*100)}%")

        cols = st.columns(2)
        with cols[0]:
            st.metric("Envelopes", f"{st.session_state.max_opened_envelope}/6")
        with cols[1]:
            st.metric("Decisão", "✅" if st.session_state.decision_submitted else "—")

        if st.button("🔄 Reiniciar caso", use_container_width=True):
            reset_state()

    st.divider()

    st.markdown("### 📌 Suspeitos")
    for name, data in st.session_state.suspects.items():
        st.write(f"{badge(data['status'])} **{name}** — {data['status']}")

    st.divider()
    st.markdown("### 🧠 Regras rápidas")
    st.caption("1) Abra na ordem. 2) Anote hipóteses. 3) Decida antes do fechamento.")

    st.divider()
    st.caption(f"© {BRAND['studio']}")

# ---------------------------
# Main Layout
# ---------------------------
if not st.session_state.started:
    left, right = st.columns([0.58, 0.42], gap="large")
    with left:
        st.markdown("# O Incidente da Pousada Aurora")
        st.markdown(
            """
<div class="muted">
Uma investigação narrativa com informação fragmentada.
Você só verá o fechamento oficial depois de declarar sua conclusão.
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
### Como funciona
- Você recebe **envelopes** com contexto, depoimentos e provas.
- As informações são liberadas em **ordem controlada**.
- Você registra hipóteses, prioriza suspeitos e toma uma decisão final.
- O **fechamento oficial** fica bloqueado até você enviar sua conclusão.

⚠️ **Regra central**  
Sem atalhos: o valor do jogo está na disciplina analítica.
"""
        )

        st.info("Quando estiver pronto, clique em **Iniciar caso** na barra lateral.")
    with right:
        safe_image(IMG["cover"])
        with st.container(border=True):
            st.markdown("### Preparação")
            st.markdown(
                "- 60 a 90 minutos\n"
                "- Ambiente silencioso\n"
                "- Sem multitarefa\n"
                "- Você contra seus próprios vieses"
            )
    st.stop()

# Tabs
tabs = st.tabs(["📦 Envelopes", "🗒️ Caderno", "✅ Decisão", "🔒 Fechamento"])

# ---------------------------
# TAB 1 — Envelopes
# ---------------------------
with tabs[0]:
    require_started()

    top_left, top_right = st.columns([0.55, 0.45], gap="large")
    with top_left:
        st.markdown("## 📦 Envelopes")
        st.caption("Abra na ordem. Confirme leitura para liberar o próximo.")
    with top_right:
        prog = st.session_state.max_opened_envelope / 6
        st.progress(prog, text=f"Progresso: {int(prog*100)}%")

    left, right = st.columns([0.33, 0.67], gap="large")

    with left:
        st.markdown("### Ordem de abertura")

        for env in content["envelopes"]:
            env_id = env["id"]
            allowed = can_open(env_id)
            active = (st.session_state.current_env == env_id)

            if allowed:
                label = f"{'➡️ ' if active else ''}Envelope {env_id}"
                if st.button(f"📩 {label}", key=f"btn_env_{env_id}", use_container_width=True):
                    st.session_state.current_env = env_id
                    st.rerun()
            else:
                st.button(f"🔒 Envelope {env_id} (bloqueado)", disabled=True, use_container_width=True)

        st.divider()

        with st.container(border=True):
            st.markdown("### Dica operacional")
            st.markdown(
                "- Separe **fato** de **interpretação**\n"
                "- Priorize **prova física** sobre discurso\n"
                "- Reavalie hipóteses a cada envelope"
            )

    with right:
        env_id = st.session_state.current_env
        env = envelope_by_id(content, env_id)

        # Envelope header with image
        safe_image(IMG.get(env_id))
        st.markdown(f"## {env['title']}")
        st.markdown(env["body"])

        st.divider()
        with st.container(border=True):
            st.markdown("### O que observar neste envelope")
            prompts = {
                1: "- Isolamento e vulnerabilidades do ambiente\n- Quem tem acesso a quê\n- Lacunas na linha do tempo",
                2: "- O que é experiência subjetiva vs. evidência\n- Gatilhos emocionais\n- Onde pode haver ruído narrativo",
                3: "- Minimizações e exageros\n- Omissões úteis\n- Convergências entre versões",
                4: "- Vínculo físico\n- Janela temporal\n- Dinâmica (luta vs. golpe único)",
                5: "- Vetores alternativos (plausível ≠ provável)\n- Incentivos ocultos\n- Quem se beneficia do ruído",
                6: "- Rupturas temporais\n- Comportamento pós-evento\n- Coerência final da narrativa",
            }
            st.markdown(prompts.get(env_id, "-"))

        st.divider()
        c1, c2, c3 = st.columns([0.36, 0.36, 0.28])
        with c1:
            if st.button("✅ Confirmar leitura", use_container_width=True):
                # Libera próximo envelope se estiver no limite atual
                if st.session_state.max_opened_envelope == env_id and env_id < 6:
                    st.session_state.max_opened_envelope += 1
                st.toast("Leitura confirmada. Próximo envelope liberado (se aplicável).")
                st.rerun()
        with c2:
            if st.button("🗒️ Anotar hipótese rápida", use_container_width=True):
                st.session_state._show_quick_note = True
        with c3:
            st.caption("")

        if st.session_state.get("_show_quick_note", False):
            with st.container(border=True):
                st.markdown("### Hipótese rápida")
                txt = st.text_input("Digite uma hipótese/insight e pressione Enter", key="quick_hyp")
                if txt and txt.strip():
                    st.session_state.hypotheses.append({"at": datetime.now().isoformat(), "text": txt.strip()})
                    st.session_state._show_quick_note = False
                    st.toast("Hipótese registrada.")
                    st.rerun()
                st.caption("Dica: escreva curto e objetivo. Você vai revisitar isso no Caderno.")

# ---------------------------
# TAB 2 — Caderno
# ---------------------------
with tabs[1]:
    require_started()

    st.markdown("## 🗒️ Caderno do Investigador")
    st.caption("Registre hipóteses provisórias. Errar cedo é barato. Errar tarde é caro.")

    c1, c2 = st.columns([0.56, 0.44], gap="large")

    with c1:
        with st.container(border=True):
            st.markdown("### Hipóteses provisórias (podem mudar)")
            st.session_state.notes = st.text_area(
                "Use isso como sua sala de guerra: hipóteses, contradições, perguntas em aberto.",
                value=st.session_state.notes,
                height=220,
            )

        st.divider()

        with st.container(border=True):
            st.markdown("### 🧩 Hipóteses rápidas registradas")
            if not st.session_state.hypotheses:
                st.caption("Nenhuma hipótese rápida registrada ainda.")
            else:
                for item in reversed(st.session_state.hypotheses[-12:]):
                    st.markdown(f"- {item['text']}")

        st.divider()

        with st.container(border=True):
            st.markdown("### 🕒 Linha do tempo (operacional)")
            with st.form("timeline_form", clear_on_submit=True):
                t = st.text_input("Evento (ex: 00h05 — discussão na recepção)")
                submitted = st.form_submit_button("Adicionar evento")
                if submitted and t.strip():
                    st.session_state.timeline.append({"at": datetime.now().isoformat(), "event": t.strip()})
                    st.toast("Evento adicionado.")
                    st.rerun()

            if st.session_state.timeline:
                for i, item in enumerate(reversed(st.session_state.timeline[-12:]), start=1):
                    st.write(f"{i}. {item['event']}")
            else:
                st.caption("Sem eventos registrados ainda.")

    with c2:
        with st.container(border=True):
            st.markdown("### 🎯 Gestão de suspeitos")
            st.caption("Seja disciplinado: status sem nota é palpite.")

            for name, data in st.session_state.suspects.items():
                st.markdown(f"**{name}** {badge(data['status'])}")

                new_status = st.selectbox(
                    "Status",
                    ["Neutro", "Suspeito", "Prioritário", "Descartado"],
                    index=["Neutro", "Suspeito", "Prioritário", "Descartado"].index(data["status"]),
                    key=f"status_{name}",
                )
                st.session_state.suspects[name]["status"] = new_status

                new_notes = st.text_area(
                    "Notas (provas e lógica)",
                    value=data["notes"],
                    key=f"notes_{name}",
                    height=90,
                    placeholder="Ex: Digitais na arma + janela temporal + ruptura narrativa…",
                )
                st.session_state.suspects[name]["notes"] = new_notes
                st.divider()

        with st.container(border=True):
            st.markdown("### 🧭 Checklist de qualidade")
            st.markdown(
                "- Minha hipótese **explica as digitais**?\n"
                "- Minha hipótese **explica o horário**?\n"
                "- Minha hipótese exige **coincidências**?\n"
                "- Estou sendo seduzido pelo \"fenômeno\"?"
            )

# ---------------------------
# TAB 3 — Decisão
# ---------------------------
with tabs[2]:
    require_started()

    st.markdown("## ✅ Decisão final")
    st.caption("Você só desbloqueia o Fechamento Oficial depois de declarar sua conclusão.")

    if not all_unlocked():
        st.warning("Você ainda não liberou todos os envelopes. Confirme leitura até o Envelope 6 para decidir.")
        st.stop()

    # Ritual
    st.warning(
        "Este é o momento da decisão.\n\n"
        "Depois de enviada, sua conclusão ficará registrada e o fechamento oficial será liberado."
    )

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
                height=180,
                placeholder="Use evidência física, janela temporal, coerência narrativa. Evite achismo.",
            )

            ok = st.form_submit_button("📌 Enviar decisão e desbloquear fechamento")
            if ok:
                if not culprit or not method.strip() or not motive.strip() or not reasoning.strip():
                    st.error("Preencha todos os campos. Decisão incompleta não desbloqueia o fechamento.")
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
        with st.container(border=True):
            st.markdown("### 📄 Sua decisão registrada")
            d = st.session_state.decision
            st.write(f"**Culpado:** {d['culprit']}")
            st.write(f"**Método:** {d['method']}")
            st.write(f"**Motivo:** {d['motive']}")
            st.write("**Justificativa:**")
            st.write(d["reasoning"])

# ---------------------------
# TAB 4 — Fechamento
# ---------------------------
with tabs[3]:
    require_started()

    st.markdown("## 🔒 Fechamento Oficial do Caso")

    if not st.session_state.decision_submitted:
        st.info("Bloqueado até você enviar sua decisão final.")
        st.stop()

    safe_image(IMG.get("closing"))
    st.markdown("### A verdade não espera por consenso.")

    with st.container(border=True):
        st.markdown(f"## {content['closing']['title']}")
        st.markdown(content["closing"]["body"])

    st.divider()
    st.caption("Fim do caso. Reinicie para jogar novamente com outra hipótese.")
