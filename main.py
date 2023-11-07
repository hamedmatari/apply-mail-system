from bs4 import BeautifulSoup
import requests
import json

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def build_search_url(author_name):
    url = "https://scholar.google.com/citations?view_op=search_authors&hl=en&mauthors="
    author_name = "+".join(author_name.split())
    return f"{url}{author_name}"


def get_next_page_link(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    # Find the "Next Page" link
    next_page_button = soup.find("button", {"aria-label": "Next"})

    # Check if the "Next Page" link exists
    if next_page_button:
        next_page_link = (
            next_page_button.get("onclick")
            .split("window.location=")[-1]
            .strip("'")
            .replace("\\x3d", "=")
            .replace("\\x26", "&")
        )
        return f"https://scholar.google.com{next_page_link}"
    else:
        return None


def get_user_profile_link(_author_name, _university):
    author_name = _author_name.strip().lower().replace(",", "")
    university = (
        _university.strip()
        .lower()
        .replace("university", "")
        .replace("the", "")
        .replace("of", "")
    )
    print(author_name, university)
    url = build_search_url(author_name)
    # Iterate through the author elements and extract the information
    while url:
        req = requests.get(url, headers=headers)
        # print("-------------------", url, req.status_code)
        html_content = req.text
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all the author elements
        author_elements = soup.find_all("div", class_="gsc_1usr")
        for author_element in author_elements:
            author = {}
            name_element = author_element.find("h3", class_="gs_ai_name")
            if name_element:
                author["name"] = name_element.get_text().strip()
            university_element = author_element.find("div", class_="gs_ai_aff")
            if university_element:
                author["university"] = university_element.get_text().strip()

            link_element = author_element.find("a", href=True)
            if link_element:
                author["profile_link"] = (
                    "https://scholar.google.com" + link_element["href"]
                )
            print(author["name"], author["university"])
            if (
                set(author_name.split()) == set(author["name"].lower().split())
                and university in author["university"].lower()
            ):
                return author["profile_link"]
        url = get_next_page_link(html_content)


def get_description(url: str) -> str:
    print("desssss")
    request = requests.get("https://scholar.google.com" + url, headers=headers)
    soup = BeautifulSoup(request.text, "html.parser")
    description = soup.find("div", class_="gsh_small")
    return description.get_text().strip()


def get_articles(url: str) -> list:
    request = requests.get(url + "&view_op=list_works&sortby=pubdate", headers=headers)
    soup = BeautifulSoup(request.text, "html.parser")

    research_interests_nodes = soup.find_all("a", class_="gsc_prf_inta gs_ibl")
    research_interest = [each.get_text() for each in research_interests_nodes]

    all_articles = soup.find_all("tr", class_="gsc_a_tr")
    data = []
    for article in all_articles:
        article_name_node = article.find("a", class_="gsc_a_at", href=True)
        article_name = article_name_node.get_text().strip()
        article_year = (
            article.find("span", class_="gsc_a_h gsc_a_hc gs_ibl").get_text().strip()
        )
        article_cite = article.find("a", class_="gsc_a_ac gs_ibl").get_text().strip()
        description = get_description(article_name_node["href"])
        data.append(
            {
                "name": article_name,
                "cited": article_cite,
                "year": article_year,
                "description": description,
            }
        )

    return {"interested": research_interest, "articles": data}


def get_data(prof: str, uni: str) -> list:
    link = get_user_profile_link(prof, uni)
    if link:
        data = get_articles(link)
    else:
        print("link error")
        return False
    data["prof"] = prof
    data["uni"] = uni
    return data


result = get_data("Wang, Xiaorui", "Ohio State")

with open("articles.json", "w") as file:
    if result:
        json.dump(result, file)
