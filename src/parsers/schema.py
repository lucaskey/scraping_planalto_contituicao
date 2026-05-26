from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypedDict


class ReferencialLegislativoDict(TypedDict):
    id_referencia: str
    numero_referencia: str
    tipo_de_referencia: Optional[str]
    texto_da_referencia: str
    status_da_referencia: Optional[str]


class ModificacaoHistoricaDict(TypedDict):
    tipo_de_modificacao: Optional[str]
    descricao_da_modificacao: str
    texto_antigo_descontinuado: str
    status_da_modificacao: Optional[str]


class AlineaDict(TypedDict):
    id_dispositivo_legislativo: str
    numero_alinea: str
    texto_da_alinea: str
    status_da_alinea: Optional[str]
    referenciais_legislativos: List[ReferencialLegislativoDict]
    modificacoes_historicas: List[ModificacaoHistoricaDict]


class IncisoDict(TypedDict):
    id_dispositivo_legislativo: str
    numero_inciso: str
    texto_do_inciso: str
    status_do_inciso: Optional[str]
    referenciais_legislativos: List[ReferencialLegislativoDict]
    modificacoes_historicas: List[ModificacaoHistoricaDict]
    alineas: List[AlineaDict]


class ParagrafoDict(TypedDict):
    id_dispositivo_legislativo: str
    numero_paragrafo: str
    texto_do_paragrafo: str
    status_do_paragrafo: Optional[str]
    referenciais_legislativos: List[ReferencialLegislativoDict]
    modificacoes_historicas: List[ModificacaoHistoricaDict]
    incisos: List[IncisoDict]


class ArtigoDict(TypedDict):
    id_dispositivo_legislativo: str
    numero_artigo: str
    caput: str
    status_do_artigo: Optional[str]
    referenciais_legislativos: List[ReferencialLegislativoDict]
    modificacoes_historicas: List[ModificacaoHistoricaDict]
    incisos_caput: List[IncisoDict]
    paragrafos: List[ParagrafoDict]


class SubsecaoDict(TypedDict):
    id_dispositivo_legislativo: str
    subsecao: str
    descricao_da_subsecao: str
    status_da_subsecao: Optional[str]
    referenciais_legislativos: List[ReferencialLegislativoDict]
    modificacoes_historicas: List[ModificacaoHistoricaDict]
    artigos: List[ArtigoDict]


class SecaoDict(TypedDict):
    id_dispositivo_legislativo: str
    secao: str
    descricao_da_secao: str
    status_da_secao: Optional[str]
    referenciais_legislativos: List[ReferencialLegislativoDict]
    modificacoes_historicas: List[ModificacaoHistoricaDict]
    subsecoes: List[SubsecaoDict]
    artigos: List[ArtigoDict]


class CapituloDict(TypedDict):
    id_dispositivo_legislativo: str
    capitulo: str
    descricao_do_capitulo: str
    status_do_capitulo: Optional[str]
    referenciais_legislativos: List[ReferencialLegislativoDict]
    modificacoes_historicas: List[ModificacaoHistoricaDict]
    secoes: List[SecaoDict]
    artigos: List[ArtigoDict]


class TituloDict(TypedDict):
    id_dispositivo_legislativo: str
    titulo: str
    descricao_do_titulo: str
    status_do_titulo: Optional[str]
    referenciais_legislativos: List[ReferencialLegislativoDict]
    modificacoes_historicas: List[ModificacaoHistoricaDict]
    capitulos: List[CapituloDict]
    artigos: List[ArtigoDict]


STATUS_VIGENTE = "VIGENTE"
STATUS_REVOGADO = "REVOGADO"

TIPO_INCLUSAO = "INCLUSAO"
TIPO_ALTERACAO = "ALTERACAO"
TIPO_REVOGACAO = "REVOGACAO"

TIPO_REF_LEI = "LEI"
TIPO_REF_DECRETO = "DECRETO"
TIPO_REF_DECRETO_LEI = "DECRETO-LEI"
TIPO_REF_EMENDA = "EMENDA"
TIPO_REF_MPV = "MPV"
TIPO_REF_ADI = "ADI"
TIPO_REF_ADIN = "ADIN"
TIPO_REF_ADPF = "ADPF"
TIPO_REF_OUTRO = "OUTRO"


def gerar_id(*partes: object) -> str:
    base = "|".join(str(p).strip().upper() for p in partes if p is not None)
    return hashlib.blake2b(base.encode("utf-8"), digest_size=16).hexdigest()


@dataclass(slots=True)
class ReferencialLegislativo:
    numero_referencia: str = ""
    tipo_de_referencia: Optional[str] = None
    texto_da_referencia: str = ""
    status_da_referencia: Optional[str] = None

    def to_dict(self) -> ReferencialLegislativoDict:
        return {
            "id_referencia": gerar_id(self.numero_referencia, self.tipo_de_referencia, self.texto_da_referencia),
            "numero_referencia": self.numero_referencia,
            "tipo_de_referencia": self.tipo_de_referencia,
            "texto_da_referencia": self.texto_da_referencia,
            "status_da_referencia": self.status_da_referencia,
        }


@dataclass(slots=True)
class ModificacaoHistorica:
    tipo_de_modificacao: Optional[str] = None
    descricao_da_modificacao: str = ""
    texto_antigo_descontinuado: str = ""
    status_da_modificacao: Optional[str] = None

    def to_dict(self) -> ModificacaoHistoricaDict:
        return {
            "tipo_de_modificacao": self.tipo_de_modificacao,
            "descricao_da_modificacao": self.descricao_da_modificacao,
            "texto_antigo_descontinuado": self.texto_antigo_descontinuado,
            "status_da_modificacao": self.status_da_modificacao,
        }


@dataclass(slots=True)
class Alinea:
    numero_alinea: str = ""
    texto_da_alinea: str = ""
    status_da_alinea: Optional[str] = None
    referenciais_legislativos: List[ReferencialLegislativoDict] = field(default_factory=list)
    modificacoes_historicas: List[ModificacaoHistoricaDict] = field(default_factory=list)

    def to_dict(self) -> AlineaDict:
        return {
            "id_dispositivo_legislativo": gerar_id("ALINEA", self.numero_alinea, self.texto_da_alinea),
            "numero_alinea": self.numero_alinea,
            "texto_da_alinea": self.texto_da_alinea,
            "status_da_alinea": self.status_da_alinea,
            "referenciais_legislativos": self.referenciais_legislativos,
            "modificacoes_historicas": self.modificacoes_historicas,
        }


@dataclass(slots=True)
class Inciso:
    numero_inciso: str = ""
    texto_do_inciso: str = ""
    status_do_inciso: Optional[str] = None
    referenciais_legislativos: List[ReferencialLegislativoDict] = field(default_factory=list)
    modificacoes_historicas: List[ModificacaoHistoricaDict] = field(default_factory=list)
    alineas: List[AlineaDict] = field(default_factory=list)

    def to_dict(self) -> IncisoDict:
        return {
            "id_dispositivo_legislativo": gerar_id("INCISO", self.numero_inciso, self.texto_do_inciso),
            "numero_inciso": self.numero_inciso,
            "texto_do_inciso": self.texto_do_inciso,
            "status_do_inciso": self.status_do_inciso,
            "referenciais_legislativos": self.referenciais_legislativos,
            "modificacoes_historicas": self.modificacoes_historicas,
            "alineas": self.alineas,
        }


@dataclass(slots=True)
class Paragrafo:
    numero_paragrafo: str = ""
    texto_do_paragrafo: str = ""
    status_do_paragrafo: Optional[str] = None
    referenciais_legislativos: List[ReferencialLegislativoDict] = field(default_factory=list)
    modificacoes_historicas: List[ModificacaoHistoricaDict] = field(default_factory=list)
    incisos: List[IncisoDict] = field(default_factory=list)

    def to_dict(self) -> ParagrafoDict:
        return {
            "id_dispositivo_legislativo": gerar_id("PARAGRAFO", self.numero_paragrafo, self.texto_do_paragrafo),
            "numero_paragrafo": self.numero_paragrafo,
            "texto_do_paragrafo": self.texto_do_paragrafo,
            "status_do_paragrafo": self.status_do_paragrafo,
            "referenciais_legislativos": self.referenciais_legislativos,
            "modificacoes_historicas": self.modificacoes_historicas,
            "incisos": self.incisos,
        }


@dataclass(slots=True)
class Artigo:
    numero_artigo: str = ""
    caput: str = ""
    status_do_artigo: Optional[str] = None
    referenciais_legislativos: List[ReferencialLegislativoDict] = field(default_factory=list)
    modificacoes_historicas: List[ModificacaoHistoricaDict] = field(default_factory=list)
    incisos_caput: List[IncisoDict] = field(default_factory=list)
    paragrafos: List[ParagrafoDict] = field(default_factory=list)

    def to_dict(self) -> ArtigoDict:
        return {
            "id_dispositivo_legislativo": gerar_id("ARTIGO", self.numero_artigo, self.caput),
            "numero_artigo": self.numero_artigo,
            "caput": self.caput,
            "status_do_artigo": self.status_do_artigo,
            "referenciais_legislativos": self.referenciais_legislativos,
            "modificacoes_historicas": self.modificacoes_historicas,
            "incisos_caput": self.incisos_caput,
            "paragrafos": self.paragrafos,
        }


@dataclass(slots=True)
class Subsecao:
    subsecao: str = ""
    descricao_da_subsecao: str = ""
    status_da_subsecao: Optional[str] = None
    referenciais_legislativos: List[ReferencialLegislativoDict] = field(default_factory=list)
    modificacoes_historicas: List[ModificacaoHistoricaDict] = field(default_factory=list)
    artigos: List[ArtigoDict] = field(default_factory=list)

    def to_dict(self) -> SubsecaoDict:
        return {
            "id_dispositivo_legislativo": gerar_id("SUBSECAO", self.subsecao, self.descricao_da_subsecao),
            "subsecao": self.subsecao,
            "descricao_da_subsecao": self.descricao_da_subsecao.upper(),
            "status_da_subsecao": self.status_da_subsecao,
            "referenciais_legislativos": self.referenciais_legislativos,
            "modificacoes_historicas": self.modificacoes_historicas,
            "artigos": self.artigos,
        }


@dataclass(slots=True)
class Secao:
    secao: str = ""
    descricao_da_secao: str = ""
    status_da_secao: Optional[str] = None
    referenciais_legislativos: List[ReferencialLegislativoDict] = field(default_factory=list)
    modificacoes_historicas: List[ModificacaoHistoricaDict] = field(default_factory=list)
    subsecoes: List[SubsecaoDict] = field(default_factory=list)
    artigos: List[ArtigoDict] = field(default_factory=list)

    def to_dict(self) -> SecaoDict:
        return {
            "id_dispositivo_legislativo": gerar_id("SECAO", self.secao, self.descricao_da_secao),
            "secao": self.secao,
            "descricao_da_secao": self.descricao_da_secao.upper(),
            "status_da_secao": self.status_da_secao,
            "referenciais_legislativos": self.referenciais_legislativos,
            "modificacoes_historicas": self.modificacoes_historicas,
            "subsecoes": self.subsecoes,
            "artigos": self.artigos,
        }


@dataclass(slots=True)
class Capitulo:
    capitulo: str = ""
    descricao_do_capitulo: str = ""
    status_do_capitulo: Optional[str] = None
    referenciais_legislativos: List[ReferencialLegislativoDict] = field(default_factory=list)
    modificacoes_historicas: List[ModificacaoHistoricaDict] = field(default_factory=list)
    secoes: List[SecaoDict] = field(default_factory=list)
    artigos: List[ArtigoDict] = field(default_factory=list)

    def to_dict(self) -> CapituloDict:
        return {
            "id_dispositivo_legislativo": gerar_id("CAPITULO", self.capitulo, self.descricao_do_capitulo),
            "capitulo": self.capitulo,
            "descricao_do_capitulo": self.descricao_do_capitulo.upper(),
            "status_do_capitulo": self.status_do_capitulo,
            "referenciais_legislativos": self.referenciais_legislativos,
            "modificacoes_historicas": self.modificacoes_historicas,
            "secoes": self.secoes,
            "artigos": self.artigos,
        }


@dataclass(slots=True)
class Titulo:
    titulo: str = ""
    descricao_do_titulo: str = ""
    status_do_titulo: Optional[str] = None
    referenciais_legislativos: List[ReferencialLegislativoDict] = field(default_factory=list)
    modificacoes_historicas: List[ModificacaoHistoricaDict] = field(default_factory=list)
    capitulos: List[CapituloDict] = field(default_factory=list)
    artigos: List[ArtigoDict] = field(default_factory=list)

    def to_dict(self) -> TituloDict:
        return {
            "id_dispositivo_legislativo": gerar_id("TITULO", self.titulo, self.descricao_do_titulo),
            "titulo": self.titulo,
            "descricao_do_titulo": self.descricao_do_titulo.upper(),
            "status_do_titulo": self.status_do_titulo,
            "referenciais_legislativos": self.referenciais_legislativos,
            "modificacoes_historicas": self.modificacoes_historicas,
            "capitulos": self.capitulos,
            "artigos": self.artigos,
        }


def make_modificacoes_historicas(
    tipo: Optional[str] = None,
    descricao: str = "",
    texto_antigo: str = "",
    status: Optional[str] = None,
) -> ModificacaoHistoricaDict:
    return ModificacaoHistorica(
        tipo_de_modificacao=tipo,
        descricao_da_modificacao=descricao,
        texto_antigo_descontinuado=texto_antigo,
        status_da_modificacao=status,
    ).to_dict()


def make_referencial_legislativo(
    numero: str = "",
    tipo: Optional[str] = None,
    texto: str = "",
    status: Optional[str] = None,
) -> ReferencialLegislativoDict:
    return ReferencialLegislativo(
        numero_referencia=numero,
        tipo_de_referencia=tipo,
        texto_da_referencia=texto,
        status_da_referencia=status,
    ).to_dict()


def make_titulo(titulo: str = "", descricao: str = "", status: Optional[str] = None) -> TituloDict:
    return Titulo(titulo=titulo, descricao_do_titulo=descricao, status_do_titulo=status).to_dict()


def make_capitulo(capitulo: str = "", descricao: str = "", status: Optional[str] = None) -> CapituloDict:
    return Capitulo(capitulo=capitulo, descricao_do_capitulo=descricao, status_do_capitulo=status).to_dict()


def make_secao(secao: str = "", descricao: str = "", status: Optional[str] = None) -> SecaoDict:
    return Secao(secao=secao, descricao_da_secao=descricao, status_da_secao=status).to_dict()


def make_subsecao(subsecao: str = "", descricao: str = "", status: Optional[str] = None) -> SubsecaoDict:
    return Subsecao(subsecao=subsecao, descricao_da_subsecao=descricao, status_da_subsecao=status).to_dict()


def make_artigo(numero: str = "", caput: str = "", status: Optional[str] = None) -> ArtigoDict:
    return Artigo(numero_artigo=numero, caput=caput, status_do_artigo=status).to_dict()


def make_paragrafo(numero: str = "", texto: str = "", status: Optional[str] = None) -> ParagrafoDict:
    return Paragrafo(numero_paragrafo=numero, texto_do_paragrafo=texto, status_do_paragrafo=status).to_dict()


def make_inciso(numero: str = "", texto: str = "", status: Optional[str] = None) -> IncisoDict:
    return Inciso(numero_inciso=numero, texto_do_inciso=texto, status_do_inciso=status).to_dict()


def make_alinea(numero: str = "", texto: str = "", status: Optional[str] = None) -> AlineaDict:
    return Alinea(numero_alinea=numero, texto_da_alinea=texto, status_da_alinea=status).to_dict()


class EstadoParser:
    def __init__(self) -> None:
        self.titulo_dict: Optional[Dict[str, Any]] = None
        self.capitulo_dict: Optional[Dict[str, Any]] = None
        self.secao_dict: Optional[Dict[str, Any]] = None
        self.subsecao_dict: Optional[Dict[str, Any]] = None
        self.artigo_dict: Optional[Dict[str, Any]] = None
        self.paragrafo_dict: Optional[Dict[str, Any]] = None
        self.inciso_dict: Optional[Dict[str, Any]] = None
        self._desc_antiga_pendente_transfer: Optional[str] = None

    def abrir_titulo(self, titulo: Dict[str, Any]) -> None:
        self.fechar_titulo()
        self.titulo_dict = titulo

    def fechar_titulo(self) -> Optional[Dict[str, Any]]:
        self.fechar_capitulo()
        titulo = self.titulo_dict
        if titulo:
            titulo.pop("_direto", None)
        self.titulo_dict = None
        return titulo

    def abrir_capitulo(self, capitulo: Dict[str, Any]) -> None:
        self.fechar_capitulo()
        if self._desc_antiga_pendente_transfer:
            capitulo["_desc_antiga_pendente"] = self._desc_antiga_pendente_transfer
            self._desc_antiga_pendente_transfer = None
        self.capitulo_dict = capitulo

    def fechar_capitulo(self) -> None:
        self.fechar_secao()
        self.secao_dict = None
        self.subsecao_dict = None
        if self.capitulo_dict is not None and self.titulo_dict is not None:
            self.capitulo_dict.pop("_direto", None)
            desc_antiga = self.capitulo_dict.pop("_desc_antiga_pendente", None)
            if desc_antiga:
                found = False
                for mod in self.capitulo_dict.get("modificacoes_historicas", []):
                    if not mod.get("texto_antigo_descontinuado"):
                        mod["texto_antigo_descontinuado"] = desc_antiga
                        found = True
                if not found:
                    self._desc_antiga_pendente_transfer = desc_antiga
            self.titulo_dict["capitulos"].append(self.capitulo_dict)
        self.capitulo_dict = None

    def abrir_secao(self, secao: Dict[str, Any]) -> None:
        self.fechar_secao()
        if self._desc_antiga_pendente_transfer:
            secao["_desc_antiga_pendente"] = self._desc_antiga_pendente_transfer
            self._desc_antiga_pendente_transfer = None
        self.secao_dict = secao

    def fechar_secao(self) -> None:
        self.fechar_subsecao()
        if self.secao_dict is not None and self.capitulo_dict is not None:
            self.secao_dict.pop("_direto", None)
            desc_antiga = self.secao_dict.pop("_desc_antiga_pendente", None)
            if desc_antiga:
                found = False
                for mod in self.secao_dict.get("modificacoes_historicas", []):
                    if not mod.get("texto_antigo_descontinuado"):
                        mod["texto_antigo_descontinuado"] = desc_antiga
                        found = True
                if not found:
                    self._desc_antiga_pendente_transfer = desc_antiga
            self.capitulo_dict["secoes"].append(self.secao_dict)
        self.secao_dict = None

    def abrir_subsecao(self, subsecao: Dict[str, Any]) -> None:
        self.fechar_subsecao()
        self.subsecao_dict = subsecao

    def fechar_subsecao(self) -> None:
        self.fechar_artigo()
        if self.subsecao_dict is not None and self.secao_dict is not None:
            self.subsecao_dict.pop("_direto", None)
            self.secao_dict["subsecoes"].append(self.subsecao_dict)
        self.subsecao_dict = None

    def abrir_artigo(self, artigo: Dict[str, Any]) -> None:
        self.fechar_artigo()
        self.artigo_dict = artigo

    def fechar_artigo(self) -> None:
        self.fechar_paragrafo()
        if self.artigo_dict is None:
            return
        destino = self.subsecao_dict or self.secao_dict or self.capitulo_dict or self.titulo_dict
        if destino is not None:
            destino["artigos"].append(self.artigo_dict)
        self.artigo_dict = None

    def abrir_paragrafo(self, paragrafo: Dict[str, Any]) -> None:
        self.fechar_paragrafo()
        self.paragrafo_dict = paragrafo

    def fechar_paragrafo(self) -> None:
        self.fechar_inciso()
        if self.paragrafo_dict is not None and self.artigo_dict is not None:
            self.artigo_dict["paragrafos"].append(self.paragrafo_dict)
        self.paragrafo_dict = None

    def abrir_inciso(self, inciso: Dict[str, Any]) -> None:
        self.fechar_inciso()
        self.inciso_dict = inciso

    def fechar_inciso(self) -> None:
        if self.inciso_dict is None:
            return
        if self.paragrafo_dict is not None:
            self.paragrafo_dict["incisos"].append(self.inciso_dict)
        elif self.artigo_dict is not None:
            if "incisos_caput" not in self.artigo_dict:
                self.artigo_dict["incisos_caput"] = []
            self.artigo_dict["incisos_caput"].append(self.inciso_dict)
        self.inciso_dict = None
