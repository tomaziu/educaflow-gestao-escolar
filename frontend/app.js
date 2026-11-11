/* =========================================================================
   EducaFlow — front-end
   Consome a API REST do back-end (Express + PostgreSQL) mantendo o
   layout e o design system originais.
   ========================================================================= */

const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];

function esc(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}
function iniciais(nome) {
  return String(nome || "").trim().split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase();
}
function vazio(valor) {
  return valor === null || valor === undefined || valor === "—" ? "" : valor;
}
function numeroBR(valor) {
  return new Intl.NumberFormat("pt-BR").format(Number(valor) || 0);
}
function primeiroNome(nome) {
  return String(nome || "").trim().split(/\s+/)[0] || "";
}

const UFS = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"];
const TITULOS = {
  dashboard: "Dashboard", alunos: "Alunos", responsaveis: "Responsáveis",
  turmas: "Turmas", matriculas: "Matrículas", relatorios: "Relatórios",
  visualizacao: "Visualização de relatório",
};

const estado = {
  usuario: null,
  csrf: null,
  pagina: "dashboard",
  dashboardMeses: 6,
  listas: {
    alunos: { page: 1, q: "", filtros: {} },
    responsaveis: { page: 1, q: "", filtros: {} },
    turmas: { page: 1, q: "", filtros: {} },
    matriculas: { page: 1, q: "", filtros: {} },
  },
  relatorio: { tipo: "alunos", filtros: {}, dados: null },
};

/* =============================== API =============================== */

class ErroApi extends Error {
  constructor(mensagem, { status = 0, code = null, field = null } = {}) {
    super(mensagem);
    this.status = status;
    this.code = code;
    this.field = field;
  }
}

async function api(metodo, caminho, corpo) {
  const opcoes = { method: metodo, headers: {}, credentials: "same-origin" };
  if (corpo !== undefined) {
    opcoes.headers["Content-Type"] = "application/json";
    opcoes.body = JSON.stringify(corpo);
  }
  if (estado.csrf && metodo !== "GET") opcoes.headers["X-CSRF-Token"] = estado.csrf;

  let resposta;
  try {
    resposta = await fetch(caminho, opcoes);
  } catch (e) {
    throw new ErroApi("Não foi possível conectar ao servidor. Verifique sua conexão.");
  }

  const contentType = resposta.headers.get("content-type") || "";
  const dados = contentType.includes("application/json")
    ? await resposta.json().catch(() => null)
    : null;

  if (resposta.status === 401 && !caminho.endsWith("/auth/login")) {
    encerrarSessao();
    throw new ErroApi("Sessão expirada. Entre novamente.", { status: 401 });
  }
  if (!resposta.ok) {
    const erro = (dados && dados.error) || {};
    throw new ErroApi(erro.message || `Erro ${resposta.status} ao processar a solicitação.`, {
      status: resposta.status,
      code: erro.code,
      field: erro.field,
    });
  }
  return dados ? dados.data : null;
}

async function baixarArquivo(caminho, nomePadrao) {
  let resposta;
  try {
    resposta = await fetch(caminho, { credentials: "same-origin" });
  } catch (e) {
    toast("Falha ao baixar o arquivo.", true);
    return;
  }
  if (!resposta.ok) {
    let mensagem = "Falha ao gerar o arquivo.";
    try {
      const j = await resposta.json();
      mensagem = (j.error && j.error.message) || mensagem;
    } catch (e) { /* ignora */ }
    toast(mensagem, true);
    return;
  }
  const blob = await resposta.blob();
  const disposicao = resposta.headers.get("content-disposition") || "";
  const encontrado = /filename="?([^";]+)"?/i.exec(disposicao);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = encontrado ? encontrado[1] : nomePadrao;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
  toast("Arquivo gerado com sucesso.");
}

/* ============================ Carregando ============================ */

let carregamentosAtivos = 0;
function mostrarCarregando(texto = "Carregando…") {
  carregamentosAtivos += 1;
  if (carregamentosAtivos === 1) {
    const el = document.createElement("div");
    el.className = "loading-overlay";
    el.id = "loadingOverlay";
    el.innerHTML = `<div class="loading-box"><div class="spinner"></div>${esc(texto)}</div>`;
    document.body.appendChild(el);
  }
}
function esconderCarregando() {
  carregamentosAtivos = Math.max(carregamentosAtivos - 1, 0);
  if (carregamentosAtivos === 0) {
    const el = $("#loadingOverlay");
    if (el) el.remove();
  }
}
async function carregar(texto, funcao) {
  mostrarCarregando(texto);
  try {
    return await funcao();
  } finally {
    esconderCarregando();
  }
}

/* =============================== UI =============================== */

function toast(mensagem, erro = false) {
  const el = document.createElement("div");
  el.className = "toast" + (erro ? " error" : "");
  el.textContent = mensagem;
  $("#toastRoot").appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

function statusTag(rotulo) {
  const texto = String(rotulo || "—");
  const chave = texto.toLowerCase();
  const classe =
    ["ativo", "ativa"].includes(chave) ? "active"
    : ["pendente"].includes(chave) ? "pending"
    : ["inativo", "inativa", "cancelada"].includes(chave) ? "inactive"
    : "";
  return `<span class="status status-${classe}">${esc(texto)}</span>`;
}

function person(nome, ini, sub = "") {
  return `<div class="person-cell"><div class="person-avatar">${esc(ini || iniciais(nome))}</div><div><strong>${esc(nome)}</strong>${sub ? `<small>${esc(sub)}</small>` : ""}</div></div>`;
}

function heading(titulo, desc, acoes = "") {
  return `<div class="page-heading"><div><h1>${esc(titulo)}</h1><p>${esc(desc)}</p></div><div class="heading-actions">${acoes}</div></div>`;
}

function btn(rotulo, acao, primario = false) {
  return `<button class="btn ${primario ? "btn-primary" : "btn-light"}" data-action="${acao}">${esc(rotulo)}</button>`;
}

const ICONES_ACAO = {
  view: ["Visualizar", "⌕", ""],
  edit: ["Editar", "✎", ""],
  toggle: ["Ativar ou desativar", "◐", ""],
  delete: ["Excluir", "✕", "danger"],
  cancel: ["Cancelar matrícula", "⊘", "danger"],
};

function acoes(tipo, id, permitidas) {
  const admin = estado.usuario && estado.usuario.tipo === "administrador";
  const lista = permitidas.filter((a) => a !== "delete" || admin);
  return `<div class="row-actions">${lista
    .map((a) => {
      const [titulo, icone, classe] = ICONES_ACAO[a];
      return `<button type="button" title="${titulo}" aria-label="${titulo}" class="${classe}" data-action="${a === "cancel" ? "cancel-matricula" : a}" data-tipo="${tipo}" data-id="${id}">${icone}</button>`;
    })
    .join("")}</div>`;
}

/* =============================== Modal =============================== */

let resolveConfirmacao = null;

function abrirModal({ titulo, corpo, aoEnviar, rotuloAcao = "Salvar" }) {
  $("#modalRoot").innerHTML = `
    <div class="modal-backdrop">
      <div class="modal" role="dialog" aria-modal="true" aria-label="${esc(titulo)}">
        <div class="modal-head"><h2>${esc(titulo)}</h2>
          <button type="button" class="modal-close" data-action="close-modal" aria-label="Fechar">×</button></div>
        <form id="modalForm" novalidate>
          <div class="modal-body"><div id="modalError"></div>${corpo}</div>
          <div class="modal-actions">
            <button type="button" class="btn btn-light" data-action="close-modal">Cancelar</button>
            <button type="submit" class="btn btn-primary">${esc(rotuloAcao)}</button>
          </div>
        </form>
      </div>
    </div>`;
  $("#modalForm").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    if (!validarCamposData(evento.target)) {
      const primeiroErro = $(".datepicker-text.input-error", evento.target);
      if (primeiroErro) primeiroErro.focus();
      return;
    }
    const botao = $('#modalForm button[type="submit"]');
    if (botao) botao.classList.add("loading");
    try {
      await aoEnviar(evento.target);
    } catch (erro) {
      exibirErroFormulario(erro);
    } finally {
      if (botao) botao.classList.remove("loading");
    }
  });
  iniciarSeletoresData($("#modalForm"));
  const primeiro = $("#modalForm input, #modalForm select");
  if (primeiro) primeiro.focus();
}

function fecharModal() {
  if (resolveConfirmacao) {
    const resolver = resolveConfirmacao;
    resolveConfirmacao = null;
    resolver(false);
  }
  $("#modalRoot").innerHTML = "";
}

function exibirErroFormulario(erro) {
  const caixa = $("#modalError");
  const mensagem = (erro && erro.message) || "Não foi possível concluir a operação.";
  if (caixa) {
    caixa.className = "form-error";
    caixa.textContent = mensagem;
  } else {
    toast(mensagem, true);
  }
  $$("#modalForm .input-error").forEach((el) => el.classList.remove("input-error"));
  if (erro && erro.field) {
    const campo = $(`#modalForm [name="${erro.field}"]`);
    if (campo) {
      campo.classList.add("input-error");
      campo.focus();
    }
  }
}

function confirmar(titulo, mensagem) {
  return new Promise((resolver) => {
    resolveConfirmacao = resolver;
    abrirModal({
      titulo,
      rotuloAcao: "Confirmar",
      corpo: `<p style="margin:0;font-size:14px;line-height:1.6;color:var(--muted)">${esc(mensagem)}</p>`,
      aoEnviar: async () => {
        resolveConfirmacao = null;
        fecharModalSilencioso();
        resolver(true);
      },
    });
  });
}

function fecharModalSilencioso() {
  $("#modalRoot").innerHTML = "";
}

/* =========================== Campos de form =========================== */

function campoHtml(campo) {
  const classe = campo.full ? "full" : "";
  const obrigatorio = campo.obrigatorio ? "required" : "";
  const valor = esc(campo.valor ?? "");
  if (campo.tipo === "date-br") {
    const iso = campo.valor ? String(campo.valor).slice(0, 10) : "";
    const data = dataDeISO(iso);
    const idCampo = `dp-${campo.name}-${Math.random().toString(36).slice(2, 8)}`;
    return `
      <div class="form-field ${classe}" data-datepicker data-obrigatorio="${campo.obrigatorio ? "1" : "0"}">
        <label class="form-label" for="${idCampo}">${esc(campo.label)}</label>
        <div class="datepicker-control">
          <input id="${idCampo}" class="datepicker-text" type="text" placeholder="dd/mm/aaaa"
                 inputmode="numeric" autocomplete="off" spellcheck="false"
                 value="${data ? dataParaBR(data) : ""}"
                 aria-haspopup="dialog" aria-expanded="false" ${campo.obrigatorio ? 'aria-required="true"' : ""}>
          <button type="button" class="datepicker-button" aria-label="Escolher data no calendário" title="Escolher data no calendário">▦</button>
        </div>
        <input type="hidden" name="${campo.name}" value="${esc(iso)}">
        <div class="datepicker-popup" role="dialog" aria-label="Calendário" hidden></div>
        <small class="field-error" hidden></small>
      </div>`;
  }
  let controle;
  if (campo.tipo === "select") {
    const opcoes = (campo.opcoes || [])
      .map((o) => `<option value="${esc(o.v)}" ${String(o.v) === String(campo.valor ?? "") ? "selected" : ""}>${esc(o.t)}</option>`)
      .join("");
    controle = `<select name="${campo.name}" ${obrigatorio}>${`<option value="">${esc(campo.rotuloVazio || "Selecione")}</option>`}${opcoes}</select>`;
  } else if (campo.tipo === "textarea") {
    controle = `<textarea name="${campo.name}" rows="3" placeholder="${esc(campo.placeholder || "")}">${valor}</textarea>`;
  } else {
    controle = `<input name="${campo.name}" type="${campo.tipo || "text"}" value="${valor}" placeholder="${esc(campo.placeholder || "")}" ${obrigatorio} ${campo.maxlength ? `maxlength="${campo.maxlength}"` : ""}>`;
  }
  return `<label class="${classe}">${esc(campo.label)}${controle}</label>`;
}

function corpoFormulario(campos) {
  return `<div class="form-grid">${campos.map(campoHtml).join("")}</div>`;
}

function lerFormulario(form) {
  const dados = Object.fromEntries(new FormData(form).entries());
  Object.keys(dados).forEach((chave) => {
    if (typeof dados[chave] === "string") dados[chave] = dados[chave].trim();
  });
  return dados;
}

/* ======================= Seletor de data (calendário) ======================= */

const MESES_CALENDARIO = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
const DIAS_CALENDARIO = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const seletoresData = [];

function dataParaISO(data) {
  return `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, "0")}-${String(data.getDate()).padStart(2, "0")}`;
}

function dataDeISO(iso) {
  if (!iso) return null;
  const partes = String(iso).slice(0, 10).split("-").map(Number);
  if (partes.length !== 3 || partes.some((n) => !Number.isFinite(n))) return null;
  const data = new Date(partes[0], partes[1] - 1, partes[2]);
  if (data.getFullYear() !== partes[0] || data.getMonth() !== partes[1] - 1 || data.getDate() !== partes[2]) return null;
  return data;
}

function dataParaBR(data) {
  return `${String(data.getDate()).padStart(2, "0")}/${String(data.getMonth() + 1).padStart(2, "0")}/${data.getFullYear()}`;
}

function dataDeHoje() {
  const agora = new Date();
  return new Date(agora.getFullYear(), agora.getMonth(), agora.getDate());
}

function montarData(ano, mes, dia) {
  const data = new Date(ano, mes - 1, dia);
  if (data.getFullYear() !== ano || data.getMonth() !== mes - 1 || data.getDate() !== dia) return { invalido: true };
  return { data };
}

function interpretarDataDigitada(texto) {
  const limpo = String(texto || "").trim();
  if (!limpo) return { vazio: true };
  let partes = limpo.match(/^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})$/);
  if (partes) return montarData(Number(partes[3]), Number(partes[2]), Number(partes[1]));
  partes = limpo.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (partes) return montarData(Number(partes[1]), Number(partes[2]), Number(partes[3]));
  partes = limpo.match(/^(\d{2})(\d{2})(\d{4})$/);
  if (partes) return montarData(Number(partes[3]), Number(partes[2]), Number(partes[1]));
  return { invalido: true };
}

function fecharSeletoresData(exceto) {
  seletoresData.forEach((seletor) => {
    if (seletor !== exceto) seletor.fechar();
  });
}

function criarSeletorData(raiz) {
  const texto = $(".datepicker-text", raiz);
  const oculto = $("input[type=hidden]", raiz);
  const botao = $(".datepicker-button", raiz);
  const popup = $(".datepicker-popup", raiz);
  const aviso = $(".field-error", raiz);
  const obrigatorio = raiz.dataset.obrigatorio === "1";

  let selecionada = dataDeISO(oculto.value);
  let referencia = selecionada ? new Date(selecionada.getFullYear(), selecionada.getMonth(), 1) : dataDeHoje();
  let foco = selecionada ? new Date(selecionada) : dataDeHoje();
  let aberto = false;
  let modo = "dias";

  function mesDoTitulo() {
    return `${MESES_CALENDARIO[referencia.getMonth()]} de ${referencia.getFullYear()}`;
  }

  function cabecalho() {
    return `
      <div class="datepicker-head">
        <button type="button" class="datepicker-nav" data-nav="mes-anterior" aria-label="Mês anterior">‹</button>
        <button type="button" class="datepicker-title" data-nav="trocar-modo" aria-label="Escolher mês e ano">${mesDoTitulo()}</button>
        <button type="button" class="datepicker-nav" data-nav="mes-seguinte" aria-label="Próximo mês">›</button>
      </div>`;
  }

  function painelMeses() {
    const botoes = MESES_CALENDARIO.map((nome, indice) => `
      <button type="button" class="datepicker-month ${indice === referencia.getMonth() ? "ativo" : ""}" data-mes="${indice}">${nome.slice(0, 3)}</button>
    `).join("");
    return `
      ${cabecalho()}
      <div class="datepicker-anos">
        <button type="button" class="datepicker-nav" data-nav="ano-anterior" aria-label="Ano anterior">‹</button>
        <strong>${referencia.getFullYear()}</strong>
        <button type="button" class="datepicker-nav" data-nav="ano-seguinte" aria-label="Próximo ano">›</button>
      </div>
      <div class="datepicker-meses">${botoes}</div>`;
  }

  function painelDias() {
    const ano = referencia.getFullYear();
    const mes = referencia.getMonth();
    const primeiro = new Date(ano, mes, 1).getDay();
    const total = new Date(ano, mes + 1, 0).getDate();
    const anterior = new Date(ano, mes, 0).getDate();
    const celulas = Math.ceil((primeiro + total) / 7) * 7;
    const hoje = dataDeHoje();
    let dias = "";
    for (let i = 0; i < celulas; i += 1) {
      const posicao = i - primeiro + 1;
      let data;
      if (posicao < 1) data = new Date(ano, mes - 1, anterior + posicao);
      else if (posicao > total) data = new Date(ano, mes + 1, posicao - total);
      else data = new Date(ano, mes, posicao);
      const classes = ["datepicker-day"];
      if (posicao < 1 || posicao > total) classes.push("fora");
      if (data.getTime() === hoje.getTime()) classes.push("hoje");
      if (selecionada && data.getTime() === selecionada.getTime()) classes.push("selecionada");
      if (data.getTime() === foco.getTime()) classes.push("foco");
      dias += `<button type="button" class="${classes.join(" ")}" data-dia="${dataParaISO(data)}" tabindex="-1" aria-label="${data.getDate()} de ${MESES_CALENDARIO[data.getMonth()]} de ${data.getFullYear()}">${data.getDate()}</button>`;
    }
    const semana = DIAS_CALENDARIO.map((dia) => `<span>${dia}</span>`).join("");
    return `
      ${cabecalho()}
      <div class="datepicker-semana">${semana}</div>
      <div class="datepicker-dias">${dias}</div>
      <div class="datepicker-pe">
        <button type="button" class="datepicker-acao" data-nav="hoje">Hoje</button>
        <button type="button" class="datepicker-acao" data-nav="limpar">Limpar</button>
      </div>`;
  }

  function desenhar(foco) {
    popup.innerHTML = modo === "dias" ? painelDias() : painelMeses();
    let alvo = null;
    if (foco) alvo = $(`[data-nav="${foco}"]`, popup);
    if (!alvo) {
      alvo = modo === "dias"
        ? $(".datepicker-day.foco", popup) || $(".datepicker-day", popup)
        : $(".datepicker-month.ativo", popup) || $(".datepicker-month", popup);
    }
    if (alvo) {
      alvo.tabIndex = 0;
      if (foco !== undefined) alvo.focus();
    }
  }

  function posicionar() {
    const controle = $(".datepicker-control", raiz).getBoundingClientRect();
    const largura = popup.offsetWidth;
    const esquerda = Math.max(8, Math.min(controle.left, window.innerWidth - largura - 8));
    popup.style.left = `${esquerda}px`;
    const abaixo = controle.bottom + 6;
    if (abaixo + popup.offsetHeight > window.innerHeight - 8) {
      popup.style.top = `${Math.max(8, controle.top - popup.offsetHeight - 6)}px`;
    } else {
      popup.style.top = `${abaixo}px`;
    }
  }

  function abrir() {
    if (aberto) return;
    aberto = true;
    seletor.popupAberto = true;
    fecharSeletoresData(seletor);
    popup.hidden = false;
    texto.setAttribute("aria-expanded", "true");
    desenhar();
    posicionar();
    const diaFoco = $(".datepicker-day.foco", popup) || $(".datepicker-day", popup);
    if (diaFoco) diaFoco.focus();
  }

  function fechar() {
    if (!aberto) return;
    aberto = false;
    seletor.popupAberto = false;
    popup.hidden = true;
    modo = "dias";
    texto.setAttribute("aria-expanded", "false");
  }

  function aplicar(data) {
    selecionada = data;
    oculto.value = data ? dataParaISO(data) : "";
    texto.value = data ? dataParaBR(data) : "";
    texto.classList.remove("input-error");
    if (aviso) {
      aviso.hidden = true;
      aviso.textContent = "";
    }
    if (data) {
      referencia = new Date(data.getFullYear(), data.getMonth(), 1);
      foco = new Date(data);
    }
    fechar();
    texto.focus();
  }

  function mostrarErro(mensagem) {
    texto.classList.add("input-error");
    if (aviso) {
      aviso.textContent = mensagem;
      aviso.hidden = false;
    }
  }

  function validar() {
    const bruto = texto.value.trim();
    if (!bruto) {
      if (obrigatorio) {
        mostrarErro("Informe a data.");
        return "Informe a data.";
      }
      oculto.value = "";
      selecionada = null;
      return null;
    }
    const resultado = interpretarDataDigitada(bruto);
    if (resultado.invalido) {
      mostrarErro("Data inválida. Use o formato dd/mm/aaaa.");
      return "Data inválida. Use o formato dd/mm/aaaa.";
    }
    selecionada = resultado.data;
    oculto.value = dataParaISO(resultado.data);
    texto.value = dataParaBR(resultado.data);
    texto.classList.remove("input-error");
    if (aviso) {
      aviso.hidden = true;
      aviso.textContent = "";
    }
    return null;
  }

  function moverFoco(dias) {
    const alvo = new Date(foco.getFullYear(), foco.getMonth(), foco.getDate() + dias);
    foco = alvo;
    if (alvo.getMonth() !== referencia.getMonth() || alvo.getFullYear() !== referencia.getFullYear()) {
      referencia = new Date(alvo.getFullYear(), alvo.getMonth(), 1);
      desenhar();
    } else {
      $$(".datepicker-day", popup).forEach((botao) => {
        botao.classList.toggle("foco", botao.dataset.dia === dataParaISO(alvo));
      });
    }
    const botao = $(".datepicker-day.foco", popup);
    if (botao) botao.focus();
  }

  botao.addEventListener("click", (evento) => {
    evento.preventDefault();
    if (aberto) fechar();
    else abrir();
  });

  texto.addEventListener("focus", () => {
    if (!aberto && texto.value.trim() === "") {
      const hoje = dataDeHoje();
      referencia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
      foco = hoje;
    }
  });

  texto.addEventListener("keydown", (evento) => {
    if (evento.key === "ArrowDown") {
      evento.preventDefault();
      abrir();
    } else if (evento.key === "Enter") {
      evento.preventDefault();
      if (aberto) {
        const dia = $(".datepicker-day.foco", popup) || $(".datepicker-day", popup);
        if (dia) aplicar(dataDeISO(dia.dataset.dia));
      } else {
        validar();
      }
    } else if (evento.key === "Escape") {
      fechar();
    }
  });

  texto.addEventListener("blur", () => {
    setTimeout(() => {
      if (document.activeElement && document.activeElement.closest && document.activeElement.closest("[data-datepicker]")) return;
      if (texto.value.trim() !== "") validar();
      fechar();
    }, 120);
  });

  popup.addEventListener("mousedown", (evento) => {
    if (evento.target.closest("button")) evento.preventDefault();
  });

  popup.addEventListener("click", (evento) => {
    evento.stopPropagation();
    const botao = evento.target.closest("[data-nav], [data-dia], [data-mes]");
    if (!botao) return;
    if (botao.dataset.dia) {
      aplicar(dataDeISO(botao.dataset.dia));
      return;
    }
    if (botao.dataset.mes !== undefined) {
      referencia = new Date(referencia.getFullYear(), Number(botao.dataset.mes), 1);
      modo = "dias";
      desenhar("grade");
      return;
    }
    switch (botao.dataset.nav) {
      case "mes-anterior":
        referencia = new Date(referencia.getFullYear(), referencia.getMonth() - 1, 1);
        desenhar("mes-anterior");
        break;
      case "mes-seguinte":
        referencia = new Date(referencia.getFullYear(), referencia.getMonth() + 1, 1);
        desenhar("mes-seguinte");
        break;
      case "ano-anterior":
        referencia = new Date(referencia.getFullYear() - 1, referencia.getMonth(), 1);
        desenhar("ano-anterior");
        break;
      case "ano-seguinte":
        referencia = new Date(referencia.getFullYear() + 1, referencia.getMonth(), 1);
        desenhar("ano-seguinte");
        break;
      case "trocar-modo":
        modo = modo === "dias" ? "meses" : "dias";
        desenhar("trocar-modo");
        break;
      case "hoje": {
        const hoje = dataDeHoje();
        referencia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        foco = hoje;
        aplicar(hoje);
        break;
      }
      case "limpar":
        aplicar(null);
        break;
      default:
        break;
    }
  });

  popup.addEventListener("keydown", (evento) => {
    const passo = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[evento.key];
    if (passo !== undefined) {
      evento.preventDefault();
      moverFoco(passo);
      return;
    }
    if (evento.key === "PageUp" || evento.key === "PageDown") {
      evento.preventDefault();
      const sinal = evento.key === "PageUp" ? -1 : 1;
      referencia = new Date(referencia.getFullYear(), referencia.getMonth() + sinal, 1);
      desenhar();
      return;
    }
    if (evento.key === "Escape") {
      evento.preventDefault();
      fechar();
      texto.focus();
    }
  });

  const seletor = { abrir, fechar, aplicar, validar, mostrarErro, reposicionar: posicionar };
  seletoresData.push(seletor);
  return seletor;
}

function iniciarSeletoresData(raiz) {
  $$("[data-datepicker]", raiz || document).forEach((elemento) => {
    if (!elemento._seletor) elemento._seletor = criarSeletorData(elemento);
  });
}

function validarCamposData(form) {
  let valido = true;
  $$("[data-datepicker]", form).forEach((elemento) => {
    const seletor = elemento._seletor;
    if (!seletor) return;
    const erro = seletor.validar();
    if (erro) valido = false;
  });
  return valido;
}

document.addEventListener("click", (evento) => {
  if (!evento.target.closest("[data-datepicker]")) fecharSeletoresData(null);
});

document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape") fecharSeletoresData(null);
});

window.addEventListener("resize", () => {
  seletoresData.forEach((seletor) => {
    if (seletor.popupAberto) seletor.reposicionar();
  });
});

window.addEventListener("scroll", () => {
  seletoresData.forEach((seletor) => {
    if (seletor.popupAberto) seletor.reposicionar();
  });
}, true);


/* ========================== Login / sessão ========================== */

function mostrarApp() {
  $("#loginScreen").classList.add("hidden");
  $("#app").classList.remove("hidden");
}

function mostrarLogin() {
  $("#app").classList.add("hidden");
  $("#loginScreen").classList.remove("hidden");
}

function exibirErroLogin(mensagem) {
  const caixa = $("#loginError");
  if (!caixa) return;
  caixa.hidden = false;
  caixa.textContent = mensagem;
}

function limparErroLogin() {
  const caixa = $("#loginError");
  if (caixa) {
    caixa.hidden = true;
    caixa.textContent = "";
  }
}

function preencherUsuario() {
  const u = estado.usuario;
  if (!u) return;
  const perfil = u.perfil_label || (u.tipo === "administrador" ? "Administrador" : "Secretária escolar");
  const curto = u.tipo === "administrador" ? "Administrador" : "Secretária";
  const ini = iniciais(u.nome);
  $("#sidebarUserName").textContent = u.nome;
  $("#sidebarUserProfile").textContent = perfil;
  $("#sidebarUserInitials").textContent = ini;
  $("#topUserName").textContent = u.nome;
  $("#topUserProfile").textContent = curto;
  $("#topUserInitials").textContent = ini;
}

function encerrarSessao() {
  estado.usuario = null;
  estado.csrf = null;
  fecharModalSilencioso();
  resolveConfirmacao = null;
  mostrarLogin();
}

async function entrar(identificador, senha) {
  const dados = await api("POST", "/api/auth/login", { identificador, senha });
  estado.csrf = dados.csrfToken;
  estado.usuario = dados.usuario;
  preencherUsuario();
  limparErroLogin();
  mostrarApp();
  await render("dashboard");
}

async function sair() {
  try {
    await api("POST", "/api/auth/logout");
  } catch (e) { /* sessão já encerrada */ }
  encerrarSessao();
  toast("Sessão encerrada com sucesso.");
}

/* ============================= Dashboard ============================= */

const CORES_ETAPAS = ["#4263eb", "#25b58a", "#f2b35f", "#e8ebf2"];

function statCard(indicador) {
  const variacao = indicador.variacao;
  const texto = variacao === null || variacao === undefined
    ? esc(indicador.nota)
    : `<span class="${variacao >= 0 ? "positive" : ""}">${variacao >= 0 ? "↑" : "↓"} ${Math.abs(variacao).toLocaleString("pt-BR")}%</span> ${esc(indicador.nota)}`;
  const icones = { alunos: ["♙", "ic-blue"], responsaveis: ["♧", "ic-green"], turmas: ["▤", "ic-orange"], matriculas: ["▣", "ic-purple"] };
  const [icone, classe] = icones[indicador.chave] || ["•", "ic-blue"];
  return `<div class="stat-card"><div class="stat-top">${esc(indicador.rotulo)} <span class="stat-icon ${classe}">${icone}</span></div>
    <div class="stat-value">${numeroBR(indicador.valor)}</div>
    <div class="stat-foot">${texto}</div></div>`;
}

async function conteudoDashboard() {
  const d = await api("GET", `/api/dashboard?meses=${estado.dashboardMeses}`);
  if (d.totais) $("#navAlunosCount").textContent = numeroBR(d.totais.alunos);

  const serie = d.serie_matriculas || [];
  const maximo = Math.max(1, ...serie.map((s) => Math.max(s.novas || 0, s.rematriculas || 0)));
  const barras = serie.map((s) => `
    <div class="bar-group">
      <div class="bar" style="height:${Math.max(4, Math.round(((s.rematriculas || 0) / maximo) * 100))}%"></div>
      <div class="bar alt" style="height:${Math.max(4, Math.round(((s.novas || 0) / maximo) * 100))}%"></div>
      <span class="bar-label">${esc(s.rotulo)}</span>
    </div>`).join("");

  const etapas = d.etapas || [];
  const doDonut = etapas.map((e, i) => `<i style="flex:${Math.max(e.quantidade, 1)};background:${CORES_ETAPAS[i % CORES_ETAPAS.length]}"></i>`).join("");
  const legenda = etapas.map((e, i) => `
    <div class="legend-row"><i style="background:${CORES_ETAPAS[i % CORES_ETAPAS.length]}"></i>${esc(e.rotulo)} <strong>${e.percentual}%</strong></div>`).join("");

  const atividades = (d.atividades || []).map((a) => {
    const icones = { criar: "＋", editar: "✎", excluir: "✕", login: "↪", desativar: "−", reativar: "+" };
    return `
      <div class="activity">
        <div class="activity-bullet">${icones[a.acao] || "•"}</div>
        <div class="activity-text"><strong>${esc(a.descricao)}</strong>
          <small>${esc(a.quando)}${a.usuario ? ` · ${esc(a.usuario)}` : ""}</small></div>
      </div>`;
  }).join("") || `<div class="empty-state">Nenhuma movimentação recente.</div>`;

  const totais = d.totais;
  return `
    ${heading(`Olá, ${primeiroNome(estado.usuario.nome)} 👋`, "Aqui está o resumo da sua instituição hoje.", btn("+ Novo aluno", "new-student", true))}
    <div class="stats-grid">${(d.indicadores || []).map(statCard).join("")}</div>
    <div class="dashboard-grid">
      <section class="panel">
        <div class="panel-head"><div><h3>Visão geral de matrículas</h3><p>Acompanhe a evolução ao longo do ano</p></div>
          <select class="select-small" id="dashboardMeses">
            <option value="6" ${estado.dashboardMeses === 6 ? "selected" : ""}>Últimos 6 meses</option>
            <option value="12" ${estado.dashboardMeses === 12 ? "selected" : ""}>Últimos 12 meses</option>
          </select></div>
        <div class="chart">${barras || `<div class="empty-state">Sem dados no período.</div>`}</div>
        <div class="chart-legend"><span><i class="legend-dot"></i> Matrículas novas</span><span><i class="legend-dot light"></i> Rematrículas</span></div>
      </section>
      <section class="panel">
        <div class="panel-head"><div><h3>Alunos por etapa</h3><p>Distribuição de estudantes</p></div></div>
        <div class="donut-wrap">
          <div class="donut">${doDonut || `<i style="flex:1;background:var(--line)"></i>`}</div>
          <div class="legend-list">${legenda || `<div class="empty-state">Sem dados.</div>`}</div>
        </div>
      </section>
    </div>
    <div class="dashboard-grid">
      <section class="panel">
        <div class="panel-head"><div><h3>Atividades recentes</h3><p>Últimas movimentações no sistema</p></div>
          <a href="#" class="text-link" data-page-link="alunos">Ver todos</a></div>
        <div class="activity-list">${atividades}</div>
      </section>
      <section class="panel">
        <div class="panel-head"><div><h3>Acesso rápido</h3><p>Atalhos para tarefas frequentes</p></div></div>
        <div class="quick-grid">
          <button class="quick-action" data-action="new-student"><span>＋</span>Cadastrar aluno</button>
          <button class="quick-action" data-action="new-guardian"><span>♧</span>Novo responsável</button>
          <button class="quick-action" data-action="new-class"><span>▤</span>Criar turma</button>
        </div>
        <div class="section-grid" style="margin-top:18px">
          <div class="mini-card"><small>Vagas disponíveis</small><strong>${numeroBR(totais.vagas_disponiveis)}</strong><span>● Capacidade total ${numeroBR(totais.capacidade_total)}</span></div>
          <div class="mini-card"><small>Ocupação</small><strong>${totais.ocupacao_percentual}%</strong><span>● Matrículas do ano letivo</span></div>
        </div>
      </section>
    </div>`;
}

/* =============================== Listas =============================== */

const LISTAS = {
  alunos: {
    titulo: "Alunos",
    desc: "Gerencie os estudantes cadastrados na instituição.",
    add: "+ Novo aluno",
    acaoNovo: "new-student",
    rota: "/api/alunos",
    placeholder: "Buscar por nome, CPF...",
    headers: ["Aluno", "Nascimento", "CPF", "Turma", "Responsável", "Situação", "Ações"],
    linha: (r) => [
      person(r.nome_completo, iniciais(r.nome_completo), r.email && r.email !== "—" ? r.email : ""),
      r.nascimento_br || "—",
      r.cpf || "—",
      r.turma || "—",
      r.responsavel || "—",
      statusTag(r.situacao === "ativo" ? "Ativo" : "Inativo"),
      acoes("alunos", r.id, ["view", "edit", "toggle", "delete"]),
    ],
    filtros: [
      {
        campo: "turma_id",
        rotulo: "Todas as turmas",
        carregar: async () => (await api("GET", "/api/turmas?per_page=200&todas=1")).items
          .map((t) => ({ v: String(t.id), t: `${t.nome} (${t.ano_letivo})` })),
      },
      { campo: "situacao", rotulo: "Todas as situações", opcoes: [{ v: "ativo", t: "Ativo" }, { v: "inativo", t: "Inativo" }] },
    ],
    exportar: "alunos",
  },
  responsaveis: {
    titulo: "Responsáveis",
    desc: "Consulte e gerencie os pais e responsáveis dos alunos.",
    add: "+ Novo responsável",
    acaoNovo: "new-guardian",
    rota: "/api/responsaveis",
    placeholder: "Buscar responsável...",
    headers: ["Responsável", "CPF", "Telefone", "E-mail", "Aluno vinculado", "Ações"],
    linha: (r) => [
      person(r.nome_completo, iniciais(r.nome_completo)),
      r.cpf || "—",
      r.telefone || "—",
      r.email || "—",
      r.alunos && r.alunos !== "—" ? esc(r.alunos) : "—",
      acoes("responsaveis", r.id, ["view", "edit", "delete"]),
    ],
    filtros: [],
    exportar: "responsaveis",
  },
  turmas: {
    titulo: "Turmas",
    desc: "Organize as turmas, turnos e capacidade da instituição.",
    add: "+ Nova turma",
    acaoNovo: "new-class",
    rota: "/api/turmas",
    placeholder: "Buscar turma...",
    headers: ["Turma", "Turno", "Ano letivo", "Capacidade", "Alunos", "Sala", "Situação", "Ações"],
    linha: (r) => [
      esc(r.nome),
      esc(r.turno),
      esc(r.ano_letivo),
      numeroBR(r.capacidade_maxima),
      numeroBR(r.matriculados),
      esc(r.sala || "—"),
      statusTag(r.situacao === "ativa" ? "Ativa" : "Inativa"),
      acoes("turmas", r.id, ["view", "edit", "toggle", "delete"]),
    ],
    filtros: [
      { campo: "ano", rotulo: "Todos os anos", opcoes: [{ v: "2026", t: "2026" }, { v: "2025", t: "2025" }, { v: "2024", t: "2024" }] },
      { campo: "situacao", rotulo: "Todas as situações", opcoes: [{ v: "ativa", t: "Ativa" }, { v: "inativa", t: "Inativa" }] },
      { campo: "turno", rotulo: "Todos os turnos", opcoes: [{ v: "Matutino", t: "Matutino" }, { v: "Vespertino", t: "Vespertino" }, { v: "Integral", t: "Integral" }] },
    ],
    exportar: "alunos-por-turma",
    resumo: async () => {
      const r = await api("GET", "/api/turmas/resumo");
      const nomes = Array.isArray(r.turnos_nomes)
        ? r.turnos_nomes
        : String(r.turnos_nomes || "").split(",").map((s) => s.trim()).filter(Boolean);
      const turnosQtd = nomes.length || r.turnos || 0;
      const turnosTxt = nomes.join(", ") || "Matutino, vespertino e integral";
      return `
        <div class="section-grid">
          <div class="mini-card"><small>Total de turmas</small><strong>${numeroBR(r.total_ativas)}</strong><span>● Em funcionamento</span></div>
          <div class="mini-card"><small>Vagas disponíveis</small><strong>${numeroBR(r.vagas_disponiveis)}</strong><span>● Capacidade restante</span></div>
          <div class="mini-card"><small>Turnos atendidos</small><strong>${numeroBR(turnosQtd)}</strong><span>● ${esc(turnosTxt)}</span></div>
        </div>`;
    },
  },
  matriculas: {
    titulo: "Matrículas",
    desc: "Acompanhe as matrículas e a situação dos estudantes.",
    add: "+ Nova matrícula",
    acaoNovo: "new-enrollment",
    rota: "/api/matriculas",
    placeholder: "Buscar aluno...",
    headers: ["Aluno", "Turma", "Ano letivo", "Data", "Situação", "Ações"],
    linha: (r) => [
      person(r.aluno, iniciais(r.aluno), r.responsaveis || ""),
      `${esc(r.turma)}${r.turno ? ` <small style="color:var(--muted)">(${esc(r.turno)})</small>` : ""}`,
      esc(r.ano_letivo),
      esc(r.data_matricula_br || "—"),
      statusTag(r.situacao === "ativa" ? "Ativa" : r.situacao === "pendente" ? "Pendente" : "Cancelada"),
      acoes("matriculas", r.id, r.situacao === "cancelada" ? ["view", "edit"] : ["view", "edit", "cancel"]),
    ],
    filtros: [
      { campo: "ano", rotulo: "Todos os anos", opcoes: [{ v: "2026", t: "2026" }, { v: "2025", t: "2025" }] },
      {
        campo: "turma_id",
        rotulo: "Todas as turmas",
        carregar: async () => (await api("GET", "/api/turmas?per_page=200&todas=1")).items
          .map((t) => ({ v: String(t.id), t: `${t.nome} (${t.ano_letivo})` })),
      },
      {
        campo: "situacao",
        rotulo: "Todas as situações",
        opcoes: [{ v: "ativa", t: "Ativa" }, { v: "pendente", t: "Pendente" }, { v: "cancelada", t: "Cancelada" }],
      },
    ],
    exportar: "matriculas",
    resumo: async () => {
      const r = await api("GET", "/api/matriculas/resumo");
      const total = r.total ?? 0;
      const percentual = r.percentual_confirmadas ?? 0;
      const ano = (r.anos && r.anos[0]) || new Date().getFullYear();
      return `
        <div class="section-grid">
          <div class="mini-card"><small>Total de matrículas</small><strong>${numeroBR(total)}</strong><span>● Ano letivo ${esc(ano)}</span></div>
          <div class="mini-card"><small>Confirmadas</small><strong>${numeroBR(r.ativas || 0)}</strong><span>● ${percentual}% do total</span></div>
          <div class="mini-card"><small>Pendentes</small><strong>${numeroBR(r.pendentes || 0)}</strong><span>● Aguardando confirmação</span></div>
        </div>`;
    },
  },
};

async function conteudoLista(tipo) {
  const cfg = LISTAS[tipo];
  const est = estado.listas[tipo];
  const filtroOpcoes = await Promise.all(
    cfg.filtros.map(async (f) => ({
      ...f,
      opcoes: f.opcoes || (f.carregar ? await f.carregar() : []),
    }))
  );
  const selects = filtroOpcoes
    .map((f) => `<select class="filter-select" data-lista="${tipo}" data-filtro="${f.campo}">
        <option value="">${esc(f.rotulo)}</option>
        ${f.opcoes.map((o) => `<option value="${esc(o.v)}" ${String(est.filtros[f.campo]) === String(o.v) ? "selected" : ""}>${esc(o.t)}</option>`).join("")}
      </select>`)
    .join("");

  const painelResumo = cfg.resumo ? await cfg.resumo() : "";

  return `
    ${heading(cfg.titulo, cfg.desc, btn(cfg.add, cfg.acaoNovo, true))}
    ${painelResumo}
    <div class="table-card">
      <div class="table-toolbar">
        <div class="toolbar-left">
          <div class="search-box"><span>⌕</span>
            <input class="table-search" data-lista="${tipo}" placeholder="${esc(cfg.placeholder)}" value="${esc(est.q)}">
          </div>
        </div>
        <div class="toolbar-right">
          ${selects}
          <button class="btn btn-light btn-sm" data-action="exportar-lista" data-lista="${tipo}">⇩ Exportar</button>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>${cfg.headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
          <tbody id="tableBody"><tr><td colspan="${cfg.headers.length}"><div class="table-loading">Carregando registros…</div></td></tr></tbody>
        </table>
      </div>
      <div class="table-footer" id="tableFooter"></div>
    </div>`;
}

function paginasVisiveis(pagina, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const conjunto = new Set([1, total, pagina, pagina - 1, pagina + 1]);
  const ordenadas = [...conjunto].filter((n) => n >= 1 && n <= total).sort((a, b) => a - b);
  const saida = [];
  ordenadas.forEach((n, i) => {
    if (i > 0 && n - ordenadas[i - 1] > 1) saida.push("…");
    saida.push(n);
  });
  return saida;
}

function rodapeLista(dados, tipo) {
  const inicio = dados.total === 0 ? 0 : (dados.page - 1) * dados.per_page + 1;
  const fim = Math.min(dados.page * dados.per_page, dados.total);
  const botoes = [
    `<button type="button" ${dados.page <= 1 ? "disabled" : ""} data-action="page-num" data-lista="${tipo}" data-num="${dados.page - 1}">‹</button>`,
    ...paginasVisiveis(dados.page, dados.total_pages).map((n) =>
      n === "…"
        ? `<button type="button" disabled>…</button>`
        : `<button type="button" class="${n === dados.page ? "active" : ""}" data-action="page-num" data-lista="${tipo}" data-num="${n}">${n}</button>`
    ),
    `<button type="button" ${dados.page >= dados.total_pages ? "disabled" : ""} data-action="page-num" data-lista="${tipo}" data-num="${dados.page + 1}">›</button>`,
  ].join("");
  return `<span>Mostrando ${inicio}–${fim} de ${numeroBR(dados.total)} registro(s)</span><div class="pagination">${botoes}</div>`;
}

async function recarregarTabela(tipo) {
  const cfg = LISTAS[tipo];
  const est = estado.listas[tipo];
  const params = new URLSearchParams({ page: String(est.page), per_page: "10" });
  if (est.q) params.set("q", est.q);
  Object.entries(est.filtros).forEach(([chave, valor]) => {
    if (valor) params.set(chave, valor);
  });

  const corpo = $("#tableBody");
  const rodape = $("#tableFooter");
  if (corpo) {
    corpo.innerHTML = `<tr><td colspan="${cfg.headers.length}"><div class="table-loading">Carregando registros…</div></td></tr>`;
  }

  try {
    const dados = await api("GET", `${cfg.rota}?${params.toString()}`);
    if (!$("#tableBody")) return;
    if (tipo === "alunos" && $("#navAlunosCount")) $("#navAlunosCount").textContent = numeroBR(dados.total);
    $("#tableBody").innerHTML = dados.items.length
      ? dados.items.map((r) => `<tr>${cfg.linha(r).map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")
      : `<tr><td colspan="${cfg.headers.length}"><div class="empty-state">Nenhum registro encontrado.</div></td></tr>`;
    if ($("#tableFooter")) $("#tableFooter").innerHTML = rodapeLista(dados, tipo);
  } catch (erro) {
    if ($("#tableBody")) {
      $("#tableBody").innerHTML = `<tr><td colspan="${cfg.headers.length}"><div class="empty-state">${esc(erro.message)}</div></td></tr>`;
    }
    toast(erro.message, true);
  }
}

/* ============================== Detalhes ============================== */

const ROTAS_DETALHE = {
  alunos: "/api/alunos",
  responsaveis: "/api/responsaveis",
  turmas: "/api/turmas",
  matriculas: "/api/matriculas",
};

function itemDetalhe(rotulo, valor, cheio = false) {
  const texto = vazio(valor);
  return `<div class="detail-item ${cheio ? "full" : ""}"><small>${esc(rotulo)}</small>
    <strong class="${texto ? "" : "muted-value"}">${esc(texto || "Não informado")}</strong></div>`;
}

async function abrirDetalhe(tipo, id) {
  const titulo = { alunos: "Aluno", responsaveis: "Responsável", turmas: "Turma", matriculas: "Matrícula" }[tipo];
  await carregar("Carregando…", async () => {
    const r = await api("GET", `${ROTAS_DETALHE[tipo]}/${id}`);
    let corpo = "";

    if (tipo === "alunos") {
      corpo = `
        <div class="detail-grid">
          ${itemDetalhe("Nome completo", r.nome_completo, true)}
          ${itemDetalhe("Data de nascimento", r.nascimento_br)}
          ${itemDetalhe("CPF", r.cpf)}
          ${itemDetalhe("RG", r.rg)}
          ${itemDetalhe("Telefone", r.telefone)}
          ${itemDetalhe("E-mail", r.email)}
          ${itemDetalhe("Endereço", [r.endereco, r.numero].filter(Boolean).join(", "), true)}
          ${itemDetalhe("Bairro", r.bairro)}
          ${itemDetalhe("Cidade", [r.cidade, r.estado].filter(Boolean).join(" - "))}
          ${itemDetalhe("CEP", r.cep)}
          ${itemDetalhe("Situação", r.situacao === "ativo" ? "Ativo" : "Inativo")}
          <div class="detail-subtitle">Responsáveis vinculados</div>
          <div class="detail-item full"><div class="detail-list-chips">${
            (r.responsaveis || []).length
              ? r.responsaveis.map((resp) => `<span>${esc(resp.nome)}${resp.principal ? " · principal" : ""}</span>`).join("")
              : "<span>Nenhum responsável vinculado</span>"
          }</div></div>
          <div class="detail-subtitle">Matrículas</div>
          <div class="detail-item full"><div class="detail-list-chips">${
            (r.matriculas || []).length
              ? r.matriculas.map((m) => `<span>${m.ano_letivo} · ${esc(m.turma)} · ${esc(m.situacao)}</span>`).join("")
              : "<span>Nenhuma matrícula registrada</span>"
          }</div></div>
        </div>`;
    } else if (tipo === "responsaveis") {
      corpo = `
        <div class="detail-grid">
          ${itemDetalhe("Nome completo", r.nome_completo, true)}
          ${itemDetalhe("CPF", r.cpf)}
          ${itemDetalhe("Telefone", r.telefone)}
          ${itemDetalhe("E-mail", r.email, true)}
          ${itemDetalhe("Endereço", [r.endereco, r.numero].filter(Boolean).join(", "), true)}
          ${itemDetalhe("Bairro", r.bairro)}
          ${itemDetalhe("Cidade", [r.cidade, r.estado].filter(Boolean).join(" - "))}
          ${itemDetalhe("CEP", r.cep)}
          ${itemDetalhe("Total de alunos", r.total_alunos)}
          <div class="detail-subtitle">Alunos vinculados</div>
          <div class="detail-item full"><div class="detail-list-chips">${
            r.alunos && r.alunos !== "—"
              ? String(r.alunos).split(",").map((a) => `<span>${esc(a.trim())}</span>`).join("")
              : "<span>Nenhum aluno vinculado</span>"
          }</div></div>
        </div>`;
    } else if (tipo === "turmas") {
      corpo = `
        <div class="detail-grid">
          ${itemDetalhe("Turma", r.nome, true)}
          ${itemDetalhe("Turno", r.turno)}
          ${itemDetalhe("Ano letivo", r.ano_letivo)}
          ${itemDetalhe("Capacidade máxima", r.capacidade_maxima)}
          ${itemDetalhe("Alunos matriculados", r.matriculados)}
          ${itemDetalhe("Vagas disponíveis", r.vagas_disponiveis)}
          ${itemDetalhe("Sala", r.sala)}
          ${itemDetalhe("Situação", r.situacao === "ativa" ? "Ativa" : "Inativa")}
          ${itemDetalhe("Descrição", r.descricao, true)}
        </div>`;
    } else {
      corpo = `
        <div class="detail-grid">
          ${itemDetalhe("Aluno", r.aluno, true)}
          ${itemDetalhe("CPF do aluno", r.aluno_cpf)}
          ${itemDetalhe("Turma", r.turma)}
          ${itemDetalhe("Turno", r.turno)}
          ${itemDetalhe("Ano letivo", r.ano_letivo)}
          ${itemDetalhe("Data da matrícula", r.data_matricula_br)}
          ${itemDetalhe("Situação", r.situacao)}
          ${itemDetalhe("Responsáveis", r.responsaveis)}
        </div>`;
    }

    abrirModal({
      titulo: `Detalhes — ${titulo}`,
      corpo,
      rotuloAcao: "Fechar",
      aoEnviar: async () => fecharModalSilencioso(),
    });
    const botao = $('#modalForm button[type="submit"]');
    if (botao) {
      botao.classList.remove("btn-primary");
      botao.classList.add("btn-light");
    }
  });
}

/* ============================= Formulários ============================= */

async function opcoesAlunos(somenteAtivos = true) {
  const params = new URLSearchParams({ per_page: "200" });
  if (somenteAtivos) params.set("situacao", "ativo");
  const dados = await api("GET", `/api/alunos?${params.toString()}`);
  return dados.items.map((a) => ({ v: String(a.id), t: a.nome_completo }));
}

async function opcoesResponsaveis() {
  const dados = await api("GET", "/api/responsaveis?per_page=200");
  return dados.items.map((r) => ({ v: String(r.id), t: r.nome_completo }));
}

async function opcoesTurmas(filtroAno = null) {
  const params = new URLSearchParams({ per_page: "200", todas: "1" });
  const dados = await api("GET", `/api/turmas?${params.toString()}`);
  return dados.items
    .filter((t) => !filtroAno || Number(t.ano_letivo) === Number(filtroAno))
    .map((t) => ({ v: String(t.id), t: `${t.nome} (${t.ano_letivo}) · ${t.matriculados}/${t.capacidade_maxima}` }));
}

function campoData(valor) {
  if (!valor) return "";
  return String(valor).slice(0, 10);
}

async function abrirFormulario(tipo, id = null) {
  const edicao = Boolean(id);
  let registro = null;
  if (edicao) {
    registro = await carregar("Carregando…", () => api("GET", `${ROTAS_DETALHE[tipo]}/${id}`));
  }

  let titulo = "";
  let campos = [];
  let enviar = null;

  if (tipo === "alunos") {
    titulo = edicao ? "Editar aluno" : "Cadastrar aluno";
    campos = [
      { name: "nome_completo", label: "Nome completo", obrigatorio: true, full: true, valor: registro?.nome_completo, placeholder: "Informe o nome completo" },
      { name: "data_nascimento", label: "Data de nascimento", tipo: "date-br", obrigatorio: true, valor: campoData(registro?.data_nascimento) },
      { name: "cpf", label: "CPF", obrigatorio: true, valor: registro?.cpf, placeholder: "000.000.000-00" },
      { name: "rg", label: "RG", valor: registro?.rg },
      { name: "telefone", label: "Telefone", valor: registro?.telefone, placeholder: "(00) 00000-0000" },
      { name: "email", label: "E-mail", type: "email", valor: registro?.email },
      { name: "endereco", label: "Endereço", valor: registro?.endereco, full: true },
      { name: "numero", label: "Número", valor: registro?.numero },
      { name: "bairro", label: "Bairro", valor: registro?.bairro },
      { name: "cidade", label: "Cidade", valor: registro?.cidade },
      { name: "estado", label: "Estado", tipo: "select", opcoes: UFS.map((u) => ({ v: u, t: u })), valor: registro?.estado, rotuloVazio: "UF" },
      { name: "cep", label: "CEP", valor: registro?.cep, placeholder: "00000-000" },
    ];
    let resp = [], turmas = [];
    try {
      [resp, turmas] = await Promise.all([opcoesResponsaveis(), opcoesTurmas(new Date().getFullYear())]);
    } catch (e) {
      toast("Não foi possível carregar opções de responsável/turma.", true);
    }
    const responsavelAtual = (registro?.responsaveis || []).find((r) => r.principal) || (registro?.responsaveis || [])[0];
    campos.push(
      { name: "responsavel_id", label: "Responsável", tipo: "select", opcoes: resp, valor: responsavelAtual ? String(responsavelAtual.id) : "", rotuloVazio: "Sem vínculo" },
      { name: "turma_id", label: edicao ? "Turma (matrícula)" : "Turma (matrícula imediata)", tipo: "select", opcoes: turmas, valor: "", rotuloVazio: "Sem matrícula agora", full: true }
    );
    enviar = async (form) => {
      const dados = lerFormulario(form);
      await carregar("Salvando…", () =>
        api(edicao ? "PUT" : "POST", edicao ? `/api/alunos/${id}` : "/api/alunos", dados)
      );
      toast(edicao ? "Aluno atualizado com sucesso." : "Aluno cadastrado com sucesso.");
      fecharModalSilencioso();
      await render(estado.pagina);
    };
  }

  if (tipo === "responsaveis") {
    titulo = edicao ? "Editar responsável" : "Cadastrar responsável";
    campos = [
      { name: "nome_completo", label: "Nome completo", obrigatorio: true, full: true, valor: registro?.nome_completo },
      { name: "cpf", label: "CPF", obrigatorio: true, valor: registro?.cpf, placeholder: "000.000.000-00" },
      { name: "telefone", label: "Telefone", valor: registro?.telefone, placeholder: "(00) 00000-0000" },
      { name: "email", label: "E-mail", type: "email", valor: registro?.email },
      { name: "endereco", label: "Endereço", valor: registro?.endereco, full: true },
      { name: "numero", label: "Número", valor: registro?.numero },
      { name: "bairro", label: "Bairro", valor: registro?.bairro },
      { name: "cidade", label: "Cidade", valor: registro?.cidade },
      { name: "estado", label: "Estado", tipo: "select", opcoes: UFS.map((u) => ({ v: u, t: u })), valor: registro?.estado, rotuloVazio: "UF" },
      { name: "cep", label: "CEP", valor: registro?.cep, placeholder: "00000-000" },
    ];
    if (!edicao) {
      let alunos = [];
      try {
        alunos = await opcoesAlunos();
      } catch (e) {
        toast("Não foi possível carregar opções de alunos.", true);
      }
      campos.push({ name: "aluno_id", label: "Aluno vinculado", tipo: "select", opcoes: alunos, valor: "", rotuloVazio: "Vincular depois", full: true });
    }
    enviar = async (form) => {
      const dados = lerFormulario(form);
      await carregar("Salvando…", () =>
        api(edicao ? "PUT" : "POST", edicao ? `/api/responsaveis/${id}` : "/api/responsaveis", dados)
      );
      toast(edicao ? "Responsável atualizado com sucesso." : "Responsável cadastrado com sucesso.");
      fecharModalSilencioso();
      await render(estado.pagina);
    };
  }

  if (tipo === "turmas") {
    titulo = edicao ? "Editar turma" : "Cadastrar turma";
    const anoAtual = new Date().getFullYear();
    campos = [
      { name: "nome", label: "Nome da turma", obrigatorio: true, valor: registro?.nome, placeholder: "Ex.: 7º Ano A" },
      { name: "turno", label: "Turno", tipo: "select", obrigatorio: true, valor: registro?.turno, opcoes: ["Matutino", "Vespertino", "Integral"].map((t) => ({ v: t, t })) },
      { name: "ano_letivo", label: "Ano letivo", tipo: "select", obrigatorio: true, valor: registro?.ano_letivo || anoAtual, opcoes: [anoAtual + 1, anoAtual, anoAtual - 1].map((a) => ({ v: String(a), t: String(a) })) },
      { name: "capacidade_maxima", label: "Capacidade máxima", tipo: "number", obrigatorio: true, valor: registro?.capacidade_maxima ?? 30 },
      { name: "sala", label: "Sala", valor: registro?.sala },
      { name: "descricao", label: "Descrição", tipo: "textarea", valor: registro?.descricao, full: true, placeholder: "Adicione uma descrição" },
    ];
    enviar = async (form) => {
      const dados = lerFormulario(form);
      await carregar("Salvando…", () =>
        api(edicao ? "PUT" : "POST", edicao ? `/api/turmas/${id}` : "/api/turmas", dados)
      );
      toast(edicao ? "Turma atualizada com sucesso." : "Turma cadastrada com sucesso.");
      fecharModalSilencioso();
      await render(estado.pagina);
    };
  }

  if (tipo === "matriculas") {
    titulo = edicao ? "Editar matrícula" : "Nova matrícula";
    const anoAtual = new Date().getFullYear();
    if (edicao) {
      const turmas = await opcoesTurmas(registro.ano_letivo);
      campos = [
        { name: "aluno_id", label: "Aluno", valor: registro.aluno_id, tipo: "select", opcoes: [{ v: String(registro.aluno_id), t: registro.aluno }], rotuloVazio: "—" },
        { name: "ano_letivo", label: "Ano letivo", valor: registro.ano_letivo, tipo: "select", opcoes: [{ v: String(registro.ano_letivo), t: String(registro.ano_letivo) }] },
        { name: "turma_id", label: "Turma", tipo: "select", obrigatorio: true, valor: registro.turma_id, opcoes: turmas },
        { name: "data_matricula", label: "Data da matrícula", tipo: "date-br", valor: campoData(registro.data_matricula) },
        { name: "situacao", label: "Situação", tipo: "select", valor: registro.situacao, opcoes: [
          { v: "ativa", t: "Ativa" }, { v: "pendente", t: "Pendente" }, { v: "cancelada", t: "Cancelada" },
        ] },
      ];
    } else {
      let alunos = [], turmas = [];
      try {
        [alunos, turmas] = await Promise.all([opcoesAlunos(), opcoesTurmas(anoAtual)]);
      } catch (e) {
        toast("Não foi possível carregar opções de alunos/turmas.", true);
      }
      campos = [
        { name: "aluno_id", label: "Aluno", tipo: "select", obrigatorio: true, opcoes: alunos },
        { name: "turma_id", label: "Turma", tipo: "select", obrigatorio: true, opcoes: turmas },
        { name: "ano_letivo", label: "Ano letivo", tipo: "select", obrigatorio: true, valor: anoAtual, opcoes: [anoAtual, anoAtual - 1].map((a) => ({ v: String(a), t: String(a) })) },
        { name: "data_matricula", label: "Data da matrícula", tipo: "date-br", valor: new Date().toISOString().slice(0, 10) },
        { name: "situacao", label: "Situação", tipo: "select", valor: "ativa", opcoes: [{ v: "ativa", t: "Ativa" }, { v: "pendente", t: "Pendente" }] },
      ];
    }
    enviar = async (form) => {
      const dados = lerFormulario(form);
      await carregar("Salvando…", () =>
        api(edicao ? "PUT" : "POST", edicao ? `/api/matriculas/${id}` : "/api/matriculas", dados)
      );
      toast(edicao ? "Matrícula atualizada com sucesso." : "Matrícula realizada com sucesso.");
      fecharModalSilencioso();
      await render(estado.pagina);
    };
  }

  abrirModal({ titulo, corpo: corpoFormulario(campos), aoEnviar: enviar });
}

/* ============================== Ações ============================== */

async function alternarSituacao(tipo, id) {
  const cfg = { alunos: { rota: "/api/alunos", atual: null }, turmas: { rota: "/api/turmas", atual: null } }[tipo];
  if (!cfg) return;
  try {
    const registro = await api("GET", `${cfg.rota}/${id}`);
    const novo = tipo === "alunos"
      ? (registro.situacao === "ativo" ? "inativo" : "ativo")
      : (registro.situacao === "ativa" ? "inativa" : "ativa");
    await carregar("Atualizando…", () => api("PATCH", `${cfg.rota}/${id}/situacao`, { situacao: novo }));
    toast(`Situação alterada para ${novo === "ativo" || novo === "ativa" ? "ativo(a)" : "inativo(a)"}.`);
    await render(estado.pagina);
  } catch (erro) {
    toast(erro.message, true);
  }
}

async function excluirRegistro(tipo, id) {
  const nomes = { alunos: "aluno", responsaveis: "responsável", turmas: "turma" };
  const confirmado = await confirmar(
    "Confirmar exclusão",
    `Deseja realmente excluir este ${nomes[tipo]}? Esta ação não pode ser desfeita.`
  );
  if (!confirmado) return;
  try {
    await carregar("Excluindo…", () => api("DELETE", `${ROTAS_DETALHE[tipo]}/${id}`));
    toast("Registro excluído com sucesso.");
    await render(estado.pagina);
  } catch (erro) {
    toast(erro.message, true);
  }
}

async function cancelarMatricula(id) {
  const confirmado = await confirmar(
    "Cancelar matrícula",
    "A matrícula será marcada como cancelada. O histórico será preservado e uma nova matrícula poderá ser criada em seguida."
  );
  if (!confirmado) return;
  try {
    await carregar("Cancelando…", () => api("POST", `/api/matriculas/${id}/cancelar`, { motivo: "Cancelada pelo usuário" }));
    toast("Matrícula cancelada.");
    await render(estado.pagina);
  } catch (erro) {
    toast(erro.message, true);
  }
}

/* ============================= Relatórios ============================= */

const RELATORIOS = [
  { tipo: "alunos", icone: "♙", nome: "Alunos cadastrados", desc: "Lista completa com informações pessoais e escolares." },
  { tipo: "alunos-por-turma", icone: "▤", nome: "Alunos por turma", desc: "Visualize a distribuição de estudantes em cada turma." },
  { tipo: "situacao-matriculas", icone: "◉", nome: "Situação das matrículas", desc: "Acompanhe matrículas ativas, pendentes e canceladas." },
  { tipo: "responsaveis", icone: "♧", nome: "Responsáveis", desc: "Relação de responsáveis e alunos vinculados." },
  { tipo: "matriculas", icone: "▣", nome: "Matriculas realizadas", desc: "Histórico de matrículas por ano letivo." },
  { tipo: "historico-matriculas", icone: "≡", nome: "Histórico de matrículas", desc: "Eventos de criação, transferência e cancelamento." },
];

function nomeRelatorio(tipo) {
  const r = RELATORIOS.find((x) => x.tipo === tipo);
  return r ? r.nome : tipo;
}

async function conteudoRelatorios() {
  return `
    ${heading("Relatórios", "Acesse informações organizadas para acompanhar a rotina escolar.")}
    <div class="report-grid">
      ${RELATORIOS.map((r) => `
        <div class="report-card">
          <div class="report-icon">${r.icone}</div>
          <h3>${esc(r.nome)}</h3>
          <p>${esc(r.desc)}</p>
          <button class="btn btn-light btn-sm" data-action="abrir-relatorio" data-tipo="${r.tipo}">Visualizar relatório →</button>
        </div>`).join("")}
    </div>`;
}

function paramsRelatorio(filtros) {
  const params = new URLSearchParams({ format: "json" });
  Object.entries(filtros).forEach(([chave, valor]) => {
    if (valor) params.set(chave, valor);
  });
  return params;
}

async function carregarRelatorio() {
  const est = estado.relatorio;
  const alvo = $("#reportPreview");
  if (!alvo) return;
  alvo.innerHTML = `<div class="table-loading">Gerando relatório…</div>`;
  try {
    const dados = await api("GET", `/api/relatorios/${est.tipo}?${paramsRelatorio(est.filtros).toString()}`);
    est.dados = dados;
    if (!$("#reportPreview")) return;
    $("#reportPreview").innerHTML = `
      <div class="report-paper-head">
        <strong>INSTITUTO CENTRAL</strong>
        <p>${esc(dados.titulo)} · ${esc(dados.subtitulo)}</p>
        <p>Gerado em ${new Date(dados.gerado_em).toLocaleString("pt-BR")}${dados.filtros_aplicados ? ` · ${esc(dados.filtros_aplicados)}` : ""}</p>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>${dados.colunas.map((c) => `<th>${esc(c.label)}</th>`).join("")}</tr></thead>
          <tbody>
            ${dados.linhas.length
              ? dados.linhas.map((linha) => `<tr>${dados.colunas.map((c) => `<td>${esc(linha[c.key] ?? "—")}</td>`).join("")}</tr>`).join("")
              : `<tr><td colspan="${dados.colunas.length}"><div class="empty-state">Nenhum registro para os filtros selecionados.</div></td></tr>`}
          </tbody>
        </table>
      </div>
      <p class="muted" style="text-align:right;margin:18px 0 0;font-size:11px">
        Total de registros: ${numeroBR(dados.total)}${dados.truncado ? " (lista truncada em 5.000 registros)" : ""}
      </p>`;
  } catch (erro) {
    if ($("#reportPreview")) {
      $("#reportPreview").innerHTML = `<div class="empty-state">${esc(erro.message)}</div>`;
    }
    toast(erro.message, true);
  }
}

async function conteudoRelatorioVista() {
  const est = estado.relatorio;
  const opcoes = await api("GET", "/api/relatorios/opcoes");
  const f = est.filtros;

  const situacoes = est.tipo === "alunos"
    ? [{ v: "ativo", t: "Ativo" }, { v: "inativo", t: "Inativo" }]
    : opcoes.situacoes.map((s) => ({ v: s, t: s.charAt(0).toUpperCase() + s.slice(1) }));
  const mostraSituacao = est.tipo !== "responsaveis";

  return `
    ${heading("Visualização de relatório", `Relatório de ${nomeRelatorio(est.tipo).toLowerCase()}`,
      `${btn("← Voltar", "voltar-relatorios")} ${btn("⇩ Exportar PDF", "exportar-pdf", true)} ${btn("⇩ Exportar Excel", "exportar-excel")} ${btn("Imprimir", "imprimir")}`)}
    <div class="filter-panel">
      <div class="filter-field"><label>Tipo de relatório</label>
        <select id="reportTipo">${RELATORIOS.map((r) => `<option value="${r.tipo}" ${r.tipo === est.tipo ? "selected" : ""}>${esc(r.nome)}</option>`).join("")}</select></div>
      <div class="filter-field"><label>Ano letivo</label>
        <select id="reportAno"><option value="">Todos</option>${opcoes.anos.map((a) => `<option value="${a}" ${String(f.ano) === String(a) ? "selected" : ""}>${a}</option>`).join("")}</select></div>
      <div class="filter-field"><label>Turma</label>
        <select id="reportTurma"><option value="">Todas</option>${opcoes.turmas.map((t) => `<option value="${t.id}" ${String(f.turma_id) === String(t.id) ? "selected" : ""}>${esc(t.nome)}</option>`).join("")}</select></div>
      ${mostraSituacao ? `<div class="filter-field"><label>Situação</label>
        <select id="reportSituacao"><option value="">Todas</option>${situacoes.map((s) => `<option value="${s.v}" ${f.situacao === s.v ? "selected" : ""}>${esc(s.t)}</option>`).join("")}</select></div>` : ""}
      <div class="filter-field"><label>Nome</label>
        <input id="reportNome" type="text" placeholder="Filtrar por nome" value="${esc(f.nome || "")}"></div>
      <button class="btn btn-primary" data-action="aplicar-relatorio">Aplicar filtros</button>
    </div>
    <div class="report-preview" id="reportPreview"><div class="table-loading">Gerando relatório…</div></div>`;
}

function lerFiltrosRelatorio() {
  return {
    ano: $("#reportAno") ? $("#reportAno").value : "",
    turma_id: $("#reportTurma") ? $("#reportTurma").value : "",
    situacao: $("#reportSituacao") ? $("#reportSituacao").value : "",
    nome: $("#reportNome") ? $("#reportNome").value.trim() : "",
  };
}

function exportarRelatorio(formato) {
  const est = estado.relatorio;
  const params = paramsRelatorio(est.filtros);
  params.set("format", formato);
  baixarArquivo(
    `/api/relatorios/${est.tipo}?${params.toString()}`,
    `educaflow-${est.tipo}.${formato === "pdf" ? "pdf" : "xlsx"}`
  );
}

/* ============================== Render ============================== */

async function render(pagina) {
  estado.pagina = pagina;
  $("#breadcrumbCurrent").textContent = TITULOS[pagina] || "Dashboard";
  $$(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.page === pagina));
  window.scrollTo(0, 0);

  const alvo = $("#pageContent");
  alvo.innerHTML = `<div class="table-loading">Carregando…</div>`;

  try {
    if (pagina === "dashboard") {
      alvo.innerHTML = await carregar("Carregando dashboard…", conteudoDashboard);
    } else if (LISTAS[pagina]) {
      const html = await carregar(`Carregando ${LISTAS[pagina].titulo.toLowerCase()}…`, () => conteudoLista(pagina));
      alvo.innerHTML = html;
      await recarregarTabela(pagina);
    } else if (pagina === "relatorios") {
      alvo.innerHTML = await carregar("Carregando relatórios…", conteudoRelatorios);
    } else if (pagina === "visualizacao") {
      alvo.innerHTML = await carregar("Carregando relatório…", conteudoRelatorioVista);
      await carregarRelatorio();
    }
  } catch (erro) {
    alvo.innerHTML = `
      ${heading(TITULOS[pagina] || "Página", "Não foi possível carregar os dados.")}
      <div class="table-card"><div class="empty-state">${esc(erro.message)}<br><br>
        <button class="btn btn-light btn-sm" data-action="recarregar">Tentar novamente</button></div></div>`;
    toast(erro.message, true);
  }
}

/* ============================== Eventos ============================== */

const ACAO_NOVO = {
  "new-student": "alunos",
  "new-guardian": "responsaveis",
  "new-class": "turmas",
  "new-enrollment": "matriculas",
};

document.addEventListener("click", async (evento) => {
  const nav = evento.target.closest("[data-page]");
  if (nav) {
    render(nav.dataset.page);
    fecharSidebar();
    return;
  }

  const link = evento.target.closest("[data-page-link]");
  if (link) {
    evento.preventDefault();
    render(link.dataset.pageLink);
    return;
  }

  if (evento.target.classList && evento.target.classList.contains("modal-backdrop")) {
    fecharModal();
    return;
  }

  const alvo = evento.target.closest("[data-action]");
  if (!alvo) return;
  const acao = alvo.dataset.action;

  if (ACAO_NOVO[acao]) {
    try {
      await abrirFormulario(ACAO_NOVO[acao]);
    } catch (erro) {
      toast(erro.message, true);
    }
    return;
  }

  switch (acao) {
    case "close-modal":
      fecharModal();
      break;
    case "logout":
      await sair();
      break;
    case "view":
      try {
        await abrirDetalhe(alvo.dataset.tipo, alvo.dataset.id);
      } catch (erro) {
        toast(erro.message, true);
      }
      break;
    case "edit":
      try {
        await abrirFormulario(alvo.dataset.tipo, alvo.dataset.id);
      } catch (erro) {
        toast(erro.message, true);
      }
      break;
    case "toggle":
      await alternarSituacao(alvo.dataset.tipo, alvo.dataset.id);
      break;
    case "delete":
      await excluirRegistro(alvo.dataset.tipo, alvo.dataset.id);
      break;
    case "cancel-matricula":
      await cancelarMatricula(alvo.dataset.id);
      break;
    case "page-num": {
      const tipo = alvo.dataset.lista;
      const pagina = Number(alvo.dataset.num);
      if (tipo && pagina >= 1) {
        estado.listas[tipo].page = pagina;
        await recarregarTabela(tipo);
      }
      break;
    }
    case "exportar-lista": {
      const tipo = alvo.dataset.lista;
      const cfg = LISTAS[tipo];
      const est = estado.listas[tipo];
      const params = new URLSearchParams({ format: "excel" });
      if (est.q) params.set("nome", est.q);
      if (est.filtros.ano) params.set("ano", est.filtros.ano);
      if (est.filtros.turma_id) params.set("turma_id", est.filtros.turma_id);
      if (est.filtros.situacao) params.set("situacao", est.filtros.situacao);
      await baixarArquivo(`/api/relatorios/${cfg.exportar}?${params.toString()}`, `educaflow-${tipo}.xlsx`);
      break;
    }
    case "abrir-relatorio":
      estado.relatorio = { tipo: alvo.dataset.tipo, filtros: {}, dados: null };
      render("visualizacao");
      break;
    case "voltar-relatorios":
      render("relatorios");
      break;
    case "aplicar-relatorio": {
      const tipo = $("#reportTipo") ? $("#reportTipo").value : estado.relatorio.tipo;
      estado.relatorio.tipo = tipo;
      estado.relatorio.filtros = lerFiltrosRelatorio();
      await carregarRelatorio();
      toast("Filtros aplicados.");
      break;
    }
    case "exportar-pdf":
      exportarRelatorio("pdf");
      break;
    case "exportar-excel":
      exportarRelatorio("excel");
      break;
    case "imprimir":
      window.print();
      break;
    case "recarregar":
      render(estado.pagina);
      break;
    default:
      break;
  }
});

let temporizadorBusca = null;
document.addEventListener("input", (evento) => {
  if (!evento.target.classList.contains("table-search")) return;
  const tipo = evento.target.dataset.lista;
  clearTimeout(temporizadorBusca);
  temporizadorBusca = setTimeout(() => {
    estado.listas[tipo].q = evento.target.value.trim();
    estado.listas[tipo].page = 1;
    recarregarTabela(tipo);
  }, 350);
});

document.addEventListener("change", async (evento) => {
  const filtro = evento.target.closest("[data-filtro]");
  if (filtro) {
    const tipo = filtro.dataset.lista;
    estado.listas[tipo].filtros[filtro.dataset.filtro] = filtro.value;
    estado.listas[tipo].page = 1;
    await recarregarTabela(tipo);
    return;
  }
  if (evento.target.id === "dashboardMeses") {
    estado.dashboardMeses = Number(evento.target.value);
    await render("dashboard");
  }
});

/* ---------- Login ---------- */
$("#loginForm").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  limparErroLogin();
  const botao = $("#loginSubmit");
  const identificador = $("#username").value.trim();
  const senha = $("#password").value;
  if (!identificador || !senha) {
    exibirErroLogin("Informe usuário e senha.");
    return;
  }
  if (botao) botao.classList.add("loading");
  try {
    await entrar(identificador, senha);
  } catch (erro) {
    exibirErroLogin(erro.message);
  } finally {
    if (botao) botao.classList.remove("loading");
  }
});

$("#togglePassword").addEventListener("click", () => {
  const campo = $("#password");
  campo.type = campo.type === "password" ? "text" : "password";
});

$("#forgotLink").addEventListener("click", (evento) => {
  evento.preventDefault();
  toast("Recuperação de senha: solicite ao administrador do sistema.");
});

/* ---------- Sidebar ---------- */
function fecharSidebar() {
  $("#sidebar").classList.remove("open");
  $("#sidebarOverlay").classList.remove("show");
}
$("#menuToggle").addEventListener("click", () => {
  $("#sidebar").classList.add("open");
  $("#sidebarOverlay").classList.add("show");
});
$("#closeSidebar").addEventListener("click", fecharSidebar);
$("#sidebarOverlay").addEventListener("click", fecharSidebar);

$("#helpLink").addEventListener("click", (evento) => {
  evento.preventDefault();
  toast("Central de suporte: fale com a coordenação da unidade.");
});

/* ---------- Tema claro / escuro ---------- */
const THEME_KEY = "educaflow-theme";
function lerTema() {
  try {
    return localStorage.getItem(THEME_KEY);
  } catch (e) {
    return null;
  }
}
function salvarTema(tema) {
  try {
    localStorage.setItem(THEME_KEY, tema);
  } catch (e) { /* ignora */ }
}
function aplicarTema(tema) {
  const escuro = tema === "dark";
  if (escuro) document.documentElement.setAttribute("data-theme", "dark");
  else document.documentElement.removeAttribute("data-theme");
  $("#themeToggle").textContent = escuro ? "☀" : "☾";
  $("#themeToggle").title = escuro ? "Usar tema claro" : "Usar tema escuro";
}
aplicarTema(lerTema() || "light");
$("#themeToggle").addEventListener("click", () => {
  const proximo = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  aplicarTema(proximo);
  salvarTema(proximo);
});

/* ---------- Data de hoje ---------- */
const rotuloData = new Intl.DateTimeFormat("pt-BR", { weekday: "short", day: "2-digit", month: "short", year: "numeric" }).format(new Date());
$("#todayLabel").textContent = rotuloData.charAt(0).toUpperCase() + rotuloData.slice(1);

/* ---------- Inicialização ---------- */
async function iniciar() {
  try {
    const sessao = await api("GET", "/api/auth/me");
    estado.csrf = sessao.csrfToken;
    estado.usuario = sessao;
    preencherUsuario();
    mostrarApp();
    await render("dashboard");
  } catch (e) {
    mostrarLogin();
  }
}

iniciar();
