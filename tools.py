"""Outils de l'agent: recherche web (Tavily), scraping, indexation et recherche RAG."""

import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

import rag
from scrapper import HEADERS, search_scraper

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY manquante dans .env")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

MARCHES_URL = "https://www.marches-publics-togo.com/consultations"


@tool
def web_search(query: str) -> str:
    """Recherche sur le web pour trouver des informations sur les marchés publics, fournisseurs, réglementations, etc.

    Args:
        query: la requête de recherche (soyez précis: ex "marchés publics BTP Togo 2026").
    """
    results = tavily_client.search(query=query, max_results=5, include_answer=True)
    lines = [f"Résumé: {results.get('answer') or 'aucun'}", ""]
    for i, r in enumerate(results.get("results", []), 1):
        content = r.get("content", "")[:800]
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"    URL: {r['url']}")
        lines.append(f"    {content}")
        lines.append("")
    return "\n".join(lines) if len(lines) > 2 else "Aucun résultat trouvé."


@tool
def scrape_web(url: str) -> str:
    """Récupère le contenu textuel d'une page web à partir de son URL.

    Args:
        url: l'URL complète de la page à scraper.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Erreur de chargement de {url}: {e}"

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else url
    text = " ".join(soup.get_text(separator=" ", strip=True).split())
    return f"Titre: {title}\n\n{text[:6000]}"


@tool
def indexer_marches() -> str:
    """Scrape le portail marches-publics-togo.com et indexe les offres dans la base
    vectorielle pour les recherches RAG. À lancer une première fois ou quand de nouvelles
    offres sont publiées."""
    offres = search_scraper(MARCHES_URL)
    if not offres:
        return "Aucune offre collectée."
    nb_chunks = rag.index_offres(offres)
    return f"{len(offres)} offres indexées ({nb_chunks} fragments) dans la base RAG."


@tool
def rag_search(query: str, secteur: str = "", k: int = 4) -> str:
    """Recherche dans la base vectorielle (RAG) des offres de marchés publics indexées.

    Args:
        query: la question ou mots-clés à rechercher.
        secteur: filtrer par secteur (BTP, Fournitures, Informatique, Services) — optionnel.
        k: nombre de résultats à retourner (défaut 4).
    """
    docs = rag.search_index(query, k=k, secteur=secteur if secteur else None)
    if not docs:
        msg = "Aucun résultat dans la base RAG."
        if secteur:
            msg += f" Aucune offre trouvée pour le secteur «{secteur}»."
        msg += " Lancer indexer_marches() pour rafraîchir les données."
        return msg
    header = f"Résultats pour «{query}»"
    if secteur:
        header += f" (secteur: {secteur})"
    header += " :\n"
    return header + "\n\n".join(
        f"[{i}] {d.page_content}\nSource: {d.metadata.get('url', 'inconnue')}"
        for i, d in enumerate(docs, start=1)
    )


@tool
def trouver_par_secteur(secteur: str, k: int = 5) -> str:
    """Liste les appels d'offres indexés appartenant à un secteur donné.

    Args:
        secteur: le secteur visé — l'un de: BTP, Fournitures, Informatique, Services, Autre.
        k: nombre maximal d'offres à retourner (défaut 5).
    """
    docs = rag.search_index("", k=k, secteur=secteur)
    if not docs:
        return f"Aucune offre indexée pour le secteur «{secteur}». Lancez indexer_marches() pour alimenter la base."
    lignes = [f"Offres du secteur «{secteur}» :\n"]
    for i, d in enumerate(docs, 1):
        titre = d.metadata.get("title") or "(sans titre)"
        url = d.metadata.get("url", "inconnue")
        lignes.append(f"[{i}] {titre}\n    {url}")
    return "\n".join(lignes)


@tool
def offres_recentes(k: int = 5) -> str:
    """Retourne les dernières offres indexées dans la base RAG (sans filtre de requête).

    Args:
        k: nombre d'offres à retourner (défaut 5).
    """
    docs = rag.get_vectorstore().get(limit=k, include=["metadatas", "documents"])
    items = docs.get("documents") or []
    metas = docs.get("metadatas") or []
    if not items:
        return "La base RAG est vide. Lancez indexer_marches() pour récupérer les offres."
    lignes = ["Dernières offres indexées :\n"]
    for i, (doc, meta) in enumerate(zip(items, metas), 1):
        titre = (meta or {}).get("title") or "(sans titre)"
        url = (meta or {}).get("url") or "inconnue"
        lignes.append(f"[{i}] {titre}\n    {url}")
    return "\n".join(lignes)


AGENT_TOOLS = [web_search, scrape_web, rag_search, indexer_marches,
               trouver_par_secteur, offres_recentes]
