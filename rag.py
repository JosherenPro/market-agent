"""RAG: indexation et recherche vectorielle sur ChromaDB + Ollama embeddings."""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

EMBED_MODEL = "nomic-embed-text"
COLLECTION = "marches_publics"
PERSIST_DIR = "./chroma_db"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

SECTOR_KEYWORDS: dict[str, list[str]] = {
    "BTP": [
        "travaux", "construction", "bâtiment", "batiment", "barrage", "forage",
        "assainissement", "aménagement", "amenagement", "route", "pont",
        "génie civil", "genie civil", "maçonnerie", "maconnerie",
        "infrastructure", "réseaux", "reseaux", "irrigation", "voirie",
        "réalisation", "realisation",
    ],
    "Fournitures": [
        "fourniture", "équipement", "equipement", "matériel", "materiel",
        "mobilier", "livraison", "station", "ordinateur", "véhicule",
        "vehicule", "intégration", "integration",
    ],
    "Informatique": [
        "logiciel", "commutateur", "réseau informatique", "reseau informatique",
        "système d'information", "systeme d'information", "géolocalisation",
        "geolocalisation", "identification", "digital", "plateforme",
    ],
    "Services": [
        "consultance", "consultant", "recrutement", "audit", "étude", "etude",
        "communication", "formation", "prestation", "pré-collecte", "pre-collecte",
        "stratégie", "strategie",
    ],
}


def detect_secteur(offre: dict) -> str:
    """Classe une offre dans un secteur."""
    texte = " ".join(
        str(offre.get(k, "")) for k in ("title", "type", "descriptions")
    ).lower()
    for secteur, mots in SECTOR_KEYWORDS.items():
        if any(mot in texte for mot in mots):
            return secteur
    return "Autre"


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=EMBED_MODEL)


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=PERSIST_DIR,
    )


def offre_to_document(offre: dict) -> Document:
    """Convertit une offre scrapée en document indexable."""
    secteur = detect_secteur(offre)
    text = "\n".join(
        [
            f"Titre: {offre['title'] or 'N/A'}",
            f"Type: {offre['type'] or 'N/A'}",
            f"Secteur: {secteur}",
            f"Description: {offre['descriptions'] or 'N/A'}",
            f"Métadonnées: {offre.get('metadata') or {}}",
            f"URL: {offre['url']}",
        ]
    )
    return Document(
        page_content=text,
        metadata={
            "url": offre["url"],
            "title": offre["title"] or "",
            "type": offre["type"] or "",
            "secteur": secteur,
        },
    )


def index_offres(offres: list[dict]) -> int:
    """Scinde puis indexe une liste d'offres dans ChromaDB. Retourne le nombre de chunks."""
    docs = [offre_to_document(o) for o in offres]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    if chunks:
        get_vectorstore().add_documents(chunks)
    return len(chunks)


def search_index(query: str, k: int = 4, secteur: str | None = None) -> list[Document]:
    """Recherche les k documents les plus similaires à la requête, avec filtrage optionnel par secteur."""
    store = get_vectorstore()
    search_kwargs: dict = {"k": k * 2}
    if secteur:
        search_kwargs["filter"] = {"secteur": secteur}
    docs_with_scores = store.similarity_search_with_score(query, **search_kwargs)
    seen_urls: set[str] = set()
    results: list[Document] = []
    for doc, _score in docs_with_scores:
        url = doc.metadata.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        results.append(doc)
        if len(results) >= k:
            break
    return results


def clear_index() -> int:
    """Vide la collection. Retourne le nombre de documents supprimés."""
    store = get_vectorstore()
    ids = store.get()["ids"]
    if ids:
        store.delete(ids=ids)
    return len(ids)
