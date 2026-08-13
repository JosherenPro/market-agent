import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# url
URL = "https://www.marches-publics-togo.com/consultations"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def extract_metadata(soup_detail: BeautifulSoup) -> dict:
    """Extrait les paires clé/valeur des cartes latérales."""
    metadata = {}
    for card in soup_detail.select("div.sidebar-card"):
        for info in card.select("div.sidebar-info__row"):
            key = info.select_one("span")
            value = info.select_one("strong")
            if key:
                metadata[key.get_text(strip=True)] = (
                    value.get_text(strip=True) if value else None
                )
    return metadata


def scrape_detail(url_detail: str, index: int):
    try:
        response_detail = requests.get(url_detail, headers=HEADERS, timeout=10)
        response_detail.raise_for_status()
    except requests.RequestException as e:
        print(f"[{index}]. Erreur de chargement du lien: {url_detail} ({e})")
        return None

    soup_detail = BeautifulSoup(response_detail.text, "html.parser")
    detail_card = soup_detail.select_one("div.detail-card")

    titre_elem = detail_card.select_one("h1.detail-card__title") if detail_card else None
    type_elem = detail_card.select_one("span.badge.badge-outline") if detail_card else None
    paragraphes = detail_card.find_all("p") if detail_card else []

    return {
        "url": url_detail,
        "type": type_elem.get_text(strip=True) if type_elem else None,
        "title": titre_elem.get_text(strip=True) if titre_elem else None,
        "descriptions": " ".join(p.text for p in paragraphes),
        "metadata": extract_metadata(soup_detail),
    }


def search_scraper(url: str):
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

    carte_offres = soup.select("article.item-card")

    print(f"Nombre d'offres détecté: {len(carte_offres)}")

    offres = []
    for index, carte in enumerate(carte_offres, start=1):
        lien_tag = carte if carte.name == "a" else carte.select_one("a[href]")

        if not lien_tag or "href" not in lien_tag.attrs:
            print(f"[{index}]. Pas de lien d'offre trouvé sur cette carte")
            continue

        url_detail = urljoin(URL, lien_tag["href"])
        print(f"[{index}] Visite de la page détail: {url_detail}")

        offre_data = scrape_detail(url_detail, index)
        if offre_data:
            offres.append(offre_data)
            print(f"[{index}], Succes")

        time.sleep(1)

    print(f"\n{len(offres)} offres collectées au total")
    return offres


# test de la fonction
if __name__ == "__main__":
    results = search_scraper(URL)
    print(results[0]["metadata"])
