import re
from typing import Any
import bs4


class SearchResult():
    def __init__(self, fn, soup):
        self.file_searched = fn
        self.soup = soup
        self.html_sources = []
        self.has_experience = False
        self.has_education = False
        self.education_in_desc = False
        self.exp_in_desc = False
    
    def has_extra_data(self) -> bool:
        return len(self.data()) > 700

    def found(self) -> bool:
        return len(self.data()) > 0

    def data(self) -> str:
        return ''.join([x.text for x in self.html_sources])
    
    def raw_data(self) -> str:
        return ''.join(map(str, self.html_sources))


class SoupBowl():
    def __init__(self, filepath):
        self.path = filepath
        self.name = filepath.split('/')[-1]

        f = open(filepath, 'r')
        self.soup = bs4.BeautifulSoup(f, 'html.parser')
        f.close


def print_debug(s: Any, name: str):
    print(f"{43 * '-'}-{43 * '-'}")
    print(f"{type(s)} {name} :")
    print('-' * 50)
    print('\n' + str(s))
    print(f"\n{43 * '-'}-{43 * '-'}")


# Writes entry to file at given filename
def add_entry(filename: str, result: SearchResult, raw: bool=False) -> None:
    # Returns entry header and footer strings
    def entry_border(title: str) -> tuple[str, str]:
        padding = '-' * ((80 - len(title)) // 2)
        header = f"\n{padding}{title}{padding}\n"
        footer = f"\n{'-' * (len(header)-2)}\n"
        return header, footer
    
    with open(filename, "a") as f:
        header, footer = entry_border(result.file_searched)
        if result.found():
            content = result.raw_data() if raw else result.data()
        else:
            content = "NO MATCH FOUND IN PAGE\n"
        f.write(header)
        f.write(content)
        f.write(footer)


# Search for given keywords                        
def search(desc_html, kws: list[str], fn: str) -> SearchResult:
    # Iterates over keyword list, updating SearchResult if kw found in target
    # Returns bool representing whether a keyword was found in target
    def find_kw(target, keywords: list[str], result: SearchResult) -> bool:
        for kw in keywords:
            if kw.upper() in str(target).upper():
                #result.data += target.text
                result.html_sources.append(target)
                return True
        return False

    result = SearchResult(fn, desc_html)
    for e in desc_html:
        find_kw(e, kws, result)
    
    return result

def any_of_in(s: list[str], target: str) -> bool:
    for c in s:
        if c in target:
            return True
    return False

#finds info on jobs for location, job number, job title and salary
def find_jobinfo(bowl: SoupBowl) -> tuple[dict, SearchResult]: 
    #values are unique div id's
    id_dict = {'Location': "ctl00_Main_content_JobLocationData",
                'JobNum': "ctl00_Main_content_JobNumberData",
                'Updated Date': "ctl00_Main_content_jobUpdatedDate",
                'Expiration Date': "ctl00_Main_content_jobExpiresDate",
                'JobTitle': "ctl00_Main_content_JobTitleLabel",
                'Company': "ctl00_Main_content_JobCompanyLabel",
                'Salary': "ctl00_Main_content_JobSalaryMaxLabel",
                'Description': "ctl00_Main_content_divPnlPartialJob0",
                'Experience': "ctl00_Main_content_pnlWorkExperienceMatch",
                'Education': "ctl00_Main_content_lblEduTraining"}
    data_dict = {}

    soup = bowl.soup

    keywords = ['diploma', 'degree', 'Bachelor', 'Master', 'phd', 'ged', 'associate', 'year', 'graduate']
    #gets each key its value in text form
    for k, v in id_dict.items():
        possible = []
        if k == 'Description':
            search_result = search(soup.find(id=v), keywords, bowl.name)
            data_dict[k] = soup.find(id=v).text
        
        
        elif k == 'Experience':
            if not 'Not Specified' in soup.find(id=v).text:
                search_result.has_experience = True
                with open('has_experience.txt', 'a') as f:
                    f.write(soup.find(id=v).text + '\n')
                data_dict[k] = soup.find(id=v).text
            else:
                exp_re = re.compile('(\d\+?|([Oo]ne|[Tt]wo|[Tt]hree|[Ff]our|[Ff]ive|[Ss]ix|[Ss]even|[Ee]ight|[Nn]ine|[Tt]en)) ([Yy]ear|[Mm]onth)')
                exp_el = soup.find(string=exp_re)
                if exp_el and len(exp_el.text) < 350:
                    exp_text = exp_el.text
                    search_result.exp_in_desc = True
                else:
                    header_re = re.compile('(EXPERIENCE|Qualifications|QUALIFICATIONS)')
                    experience_header = soup.find(string=re.compile(header_re))
                    possible = []
                    if experience_header:
                        experience_header = experience_header.parent
                        exp_re = re.compile('(year|Year|month|Month)')
                        exp_text = experience_header.find_next(string=exp_re)
                        if (exp_text and len(exp_text) > 350) or any_of_in(['%', '$', 'age'], exp_text):
                            exp_text = 'No experience requirements found'
                        else:
                            search_result.exp_in_desc = True
                    else:
                        exp_text = 'No experience requirements found'
                        for y in ['year', 'Year', 'month', 'Month']:
                            inner_soup = soup.find(id=id_dict['Description'])    
                            if y in inner_soup.text:
                                candidates = inner_soup.find_all(string=re.compile(y))
                                candidates = [x.parent for x in candidates if len(x) < 1000]
                                candidates = [x for x in candidates if not any_of_in(['125 years', 'DaVita'], x.text)]
                                if candidates:
                                    possible += candidates
                                    search_result.exp_in_desc = True
                                #exp_text += soup.find(id=id_dict['Description']).text
                                #exp_text = "Experience requirements in description"
                                #exp_text = str(possible)
                if not possible:
                    data_dict[k] = exp_text
                else:
                    print('\n')
                    possible.append("Experience not found")
                    for i, choice in enumerate(possible):
                       print(f"{i}: {choice}")
                       print(('-' * 40) + '\n')
                    choice = int(input("Choose correct option: \n"))
                    data_dict[k] = str(possible[choice])
                    search_result.exp_in_desc = str(possible[choice]) != "Experience not found"
        
        
        elif k == 'Education':
            if not 'No Minimum' in soup.find(id=v).text:
                search_result.has_education = True
                with open('has_education.txt', 'a') as f:
                    f.write(soup.find(id=v).text + '\n')
                data_dict[k] = soup.find(id=v).text
            else:
                edu_text = 'No education requirements found'
                for edu in ['achelor', 'master', 'Master', 'egree', 'ccredited']:
                    if edu in soup.find(id=id_dict['Description']).text:
                        search_result.education_in_desc = True
                        #edu_text += soup.find(id=id_dict['Description']).text
                        edu_text = "Education requirements in description"
                data_dict[k] = edu_text
        else:
            try:
                data_dict[k] = soup.find(id=v).text
            except:
                data_dict[k] = ''

    #Removes location data that is sometimes at the end of the job title in posting
    data_dict['JobTitle'] = data_dict['JobTitle'].split('-')[0]

    return data_dict, search_result