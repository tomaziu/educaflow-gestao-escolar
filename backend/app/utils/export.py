from __future__ import annotations

import io
import zipfile
from typing import Optional, Sequence


def _texto(valor) -> str:
    if valor is None:
        return "—"
    texto = str(valor).strip()
    return texto if texto else "—"


def _valores(colunas: Sequence[dict], linha: dict) -> list[str]:
    return [_texto(linha.get(coluna["key"])) for coluna in colunas]


def gerar_csv(colunas: Sequence[dict], linhas: Sequence[dict]) -> bytes:
    import csv

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow([coluna["label"] for coluna in colunas])
    for linha in linhas:
        writer.writerow(_valores(colunas, linha))
    return ("﻿" + buffer.getvalue()).encode("utf-8")

def _escapar_xml(texto: str) -> str:
    substituido = str(texto)
    substituido = substituido.replace("&", chr(38) + "amp;")
    substituido = substituido.replace("<", chr(38) + "lt;")
    substituido = substituido.replace(">", chr(38) + "gt;")
    substituido = substituido.replace('"', chr(38) + "quot;")
    return substituido


def _coluna_excel(indice: int) -> str:
    letras = ""
    n = indice + 1
    while n:
        n, resto = divmod(n - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def gerar_xlsx(titulo: str, colunas: Sequence[dict], linhas: Sequence[dict]) -> bytes:
    cabecalhos = "".join(
        f'<c r="{_coluna_excel(i)}1" t="inlineStr" s="1"><is><t>{_escapar_xml(coluna["label"])}</t></is></c>'
        for i, coluna in enumerate(colunas)
    )
    linhas_xml = [f'<row r="1">{cabecalhos}</row>']
    for indice, linha in enumerate(linhas, start=2):
        celulas = "".join(
            f'<c r="{_coluna_excel(i)}{indice}" t="inlineStr"><is><t>{_escapar_xml(valor)}</t></is></c>'
            for i, valor in enumerate(_valores(colunas, linha))
        )
        linhas_xml.append(f'<row r="{indice}">{celulas}</row>')

    larguras = "".join(
        f'<col min="{i + 1}" max="{i + 1}" width="24" customWidth="1"/>'
        for i in range(len(colunas))
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{_escapar_xml(titulo[:31] or "Relatorio")}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        "</Relationships>"
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
        "</styleSheet>"
    )
    planilha = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<cols>{larguras}</cols>"
        f'<sheetData>{"".join(linhas_xml)}</sheetData>'
        "</worksheet>"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as pacote:
        pacote.writestr("[Content_Types].xml", content_types)
        pacote.writestr("_rels/.rels", rels)
        pacote.writestr("xl/workbook.xml", workbook)
        pacote.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        pacote.writestr("xl/styles.xml", styles)
        pacote.writestr("xl/worksheets/sheet1.xml", planilha)
    return buffer.getvalue()


def _escapar_pdf(texto: str) -> str:
    substituido = str(texto)
    substituido = substituido.replace("\\", "\\\\")
    substituido = substituido.replace("(", "\\(")
    substituido = substituido.replace(")", "\\)")
    substituido = substituido.replace("\r", " ")
    substituido = substituido.replace("\n", " ")
    return substituido.encode("cp1252", "replace").decode("cp1252")


def _cortar(texto: str, limite: int) -> str:
    if len(texto) <= limite:
        return texto
    return texto[: max(0, limite - 1)] + "..."


def gerar_pdf(
    titulo: str,
    subtitulo: str,
    colunas: Sequence[dict],
    linhas: Sequence[dict],
    observacoes: Optional[str] = None,
) -> bytes:
    largura, altura = 842.0, 595.0
    margem = 36.0
    largura_util = largura - margem * 2
    total_colunas = max(1, len(colunas))
    larguras = [largura_util / total_colunas] * total_colunas
    linhas_por_pagina = 30

    paginas = [list(linhas[i : i + linhas_por_pagina]) for i in range(0, len(linhas), linhas_por_pagina)]
    if not paginas:
        paginas = [[]]

    conteudos: list[bytes] = []
    for numero, pagina in enumerate(paginas, start=1):
        ops: list[str] = []

        def texto(valor: str, x: float, y: float, fonte: str = "F2", tamanho: float = 9.0) -> None:
            ops.append(
                f"BT /{fonte} {tamanho} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({_escapar_pdf(valor)}) Tj ET"
            )

        y = altura - margem - 18
        texto(titulo, margem, y, "F1", 16)
        y -= 16
        texto(subtitulo, margem, y, "F2", 9)
        y -= 12
        if observacoes:
            texto(observacoes, margem, y, "F2", 8)
            y -= 12
        y -= 4
        ops.append(f"0.6 w {margem:.2f} {y:.2f} m {largura - margem:.2f} {y:.2f} l S")
        y -= 14

        x = margem
        for indice, coluna in enumerate(colunas):
            limite = max(4, int(larguras[indice] / 4.4))
            texto(_cortar(str(coluna["label"]), limite), x, y, "F1", 8)
            x += larguras[indice]
        y -= 6
        ops.append(f"0.3 w {margem:.2f} {y:.2f} m {largura - margem:.2f} {y:.2f} l S")
        y -= 14

        for linha in pagina:
            x = margem
            for indice, valor in enumerate(_valores(colunas, linha)):
                limite = max(4, int(larguras[indice] / 4.4))
                texto(_cortar(valor, limite), x, y, "F2", 8)
                x += larguras[indice]
            y -= 13

        texto(
            f"EducaFlow - Pagina {numero} de {len(paginas)} - {len(linhas)} registro(s)",
            margem,
            margem,
            "F2",
            8,
        )
        conteudos.append("\n".join(ops).encode("cp1252", "replace"))

    objetos: list[bytes] = []
    objetos.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{5 + i * 2} 0 R" for i in range(len(conteudos)))
    objetos.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(conteudos)} >>".encode("latin-1"))
    objetos.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    )
    objetos.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )

    for indice, conteudo in enumerate(conteudos):
        id_pagina = 5 + indice * 2
        objetos.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {largura:.0f} {altura:.0f}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                f"/Contents {id_pagina + 1} 0 R >>"
            ).encode("latin-1")
        )
        objetos.append(
            f"<< /Length {len(conteudo)} >>\nstream\n".encode("latin-1") + conteudo + b"\nendstream"
        )

    saida = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for indice, objeto in enumerate(objetos, start=1):
        offsets.append(len(saida))
        saida += f"{indice} 0 obj\n".encode("latin-1")
        saida += objeto
        saida += b"\nendobj\n"

    inicio_xref = len(saida)
    saida += f"xref\n0 {len(objetos) + 1}\n".encode("latin-1")
    saida += b"0000000000 65535 f \n"
    for offset in offsets:
        saida += f"{offset:010d} 00000 n \n".encode("latin-1")
    saida += (
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n"
    ).encode("latin-1")
    return bytes(saida)
