import re
from typing import Any
import bs4


class PageContent():
    def __init__(self, fn, soup, desc_id=None) -> None:
        self.file_searched = fn
        self.soup = soup
        self.desc_html = []
        if desc_id:
            self.desc_soup = soup.find(id=desc_id)
        else:
            self.desc_soup = None
        self.exp_search = SearchResults()
        self.edu_search = SearchResults()
    
    def has_extra_data(self) -> bool:
        return len(self.data()) > 700

    def found(self) -> bool:
        return len(self.data()) > 0

    def data(self) -> str:
        return ''.join([x.text for x in self.desc_html])
    
    def raw_data(self) -> str:
        return ''.join(map(str, self.desc_html))


class SearchResults():
    def __init__(self) -> None:
        self.data_found = 'No data found'
        self.found_explicit = False
        self.found_strict = False
        self.found_via_header = False
        self.found_via_ui = False

    def found(self):
        return (self.found_explicit or 
                self.found_strict or 
                self.found_via_header or 
                self.found_via_ui)


class SoupBowl():
    def __init__(self, filepath) -> None:
        self.path = filepath
        self.name = filepath.split('/')[-1]

        f = open(filepath, 'r')
        self.soup = bs4.BeautifulSoup(f, 'html.parser')
        f.close


class SearchParams():
    def __init__(self, search_name: str, bowl: SoupBowl, page_content: PageContent, target_id: str, desc_soup: bs4.BeautifulSoup, no_reqs_str: str, regex_strict: str, 
                 regex_loose: str, bad_match_tight: list[str], bad_match_loose: list[str], 
                 regex_header: list[str], header_search_kws: list[str],) -> None:
        self.searh_name = search_name
        self.bowl = bowl
        self.page_content = page_content
        self.desc_soup = desc_soup
        self.target_id = target_id
        self.no_reqs_str = no_reqs_str
        self.regex_strict = regex_strict
        self.regex_loose = regex_loose
        self.bad_match_tight = bad_match_tight
        self.bad_match_loose = bad_match_loose
        self.regex_header = regex_header
        self.header_search_kws = header_search_kws


#finds info on jobs for location, job number, job title and salary
def find_jobinfo(bowl: SoupBowl) -> tuple[dict, PageContent]: 
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

    soup, name = bowl.soup, bowl.name
    page_content = PageContent(name, soup)

    #gets each key its value in text form
    for k, v in id_dict.items():       
        if k == 'Description':
            # Populates page_content desc_html list with html elements in job description section
            for e in soup.find(id=v):
                page_content.desc_html.append(e)
            page_content.desc_soup = soup.find(id=v)
            desc_soup = page_content.desc_soup
            data_dict[k] = soup.find(id=v).text
        

        elif k == 'Experience':
            params = SearchParams(
                search_name=k,
                bowl=bowl,
                page_content=page_content,
                target_id=v,
                desc_soup=desc_soup,
                no_reqs_str='Not Specified',
                regex_strict="(\(?\d\)?\+?|([Oo]ne|[Tt]wo|[Tt]hree|[Ff]our|[Ff]ive|[Ss]ix|[Ss]even|[Ee]ight|[Nn]ine|[Tt]en))( |-)([Yy]ear|[Mm]onth)"
                             "|[Cc]ustomer [Ss]ervice [Ee]xperience|[Ee]xperience (in|with|as)| [Rr]elevant [Ee]xperience"
                             "|[Ee]xperience [aA-zZ]*ing|ing [Ee]xperience|[Ee]xperience [Pp]referred",
                regex_loose='([Yy]ear|[Mm]onth|[Ee]xperience)',
                bad_match_tight=['$', '?', 'DaVita', 'xperiences', 'will experience', 'human experience', 'inexperience', 
                                 'experience.', 'he experience', 'monthly', 'ears of age', 'Life Time champions', 'HCA'],
                bad_match_loose=['125 years', 'DaVita', '$', '%', 'million', 'Degree', 'degree', 'UTSW', 'HCA', 'salary', 
                                 'montly', 'ears of age', 'xperience.', 'inexperience', 'Life Time champions'],
                regex_header='(EXPERIENCE|Qualifications|QUALIFICATIONS|Experience \(Years\)|Experience and Education)',
                header_search_kws=['year', 'month', 'experience'],
            )
            search_result = search_func(params)
            page_content.exp_search = search_result
            data_dict[k] = search_result.data_found

        elif k == 'Education':
            params = SearchParams(
                search_name=k,
                bowl=bowl,
                page_content=page_content,
                target_id=v,
                desc_soup=desc_soup,
                no_reqs_str='No Minimum',
                regex_strict="[Bb]achelor|[Mm]aster|[Pp][Hh][Dd]|ADN|BSN|BLS|ACLS|\(RN\)|[Dd]iploma"
                             "|[Rr]egistered [Nn]urse|[Gg]rad(uate)? of|[Dd]egree in|CNA|CHT|CMA",
                regex_loose='([Bb]achelor|[Mm]aster|[Pp][Hh][Dd]|BLS|[Aa]ccredited|ADN|BSN)',
                bad_match_tight=['AAHC', '?'],
                bad_match_loose=['AAHC', '?'],
                regex_header='(EDUCATION|Qualifications|QUALIFICATIONS|Experience and Education)',
                header_search_kws=['Grad', 'Certifi'],
            )
            search_result = search_func(params)
            page_content.edu_search = search_result
            data_dict[k] = search_result.data_found
        
        else:
            try:
                data_dict[k] = soup.find(id=v).text
            except:
                data_dict[k] = ''

    
    #Removes location data that is sometimes at the end of the job title in posting
    data_dict['JobTitle'] = data_dict['JobTitle'].split('-')[0]

    return data_dict, page_content


def search_func(params: SearchParams) -> SearchResults:
    bowl = params.bowl
    target_id = params.target_id
    soup, name = bowl.soup, bowl.name
    target_soup = soup.find(id=target_id)
    results = SearchResults()

    # Explicit Data
    # Requirements section contains data. Use section contents and move on
    if not params.no_reqs_str in target_soup.text:
        results.data_found = soup.find(id=target_id).text
        results.found_explicit = True
        return results

    #  ______                                               _     
    #  | ___ \                                             | |    
    #  | |_/ /___  __ _  _____  __  ___  ___  __ _ _ __ ___| |__  
    #  |    // _ \/ _` |/ _ \ \/ / / __|/ _ \/ _` | '__/ __| '_ \ 
    #  | |\ \  __/ (_| |  __/>  <  \__ \  __/ (_| | | | (__| | | |
    #  \_| \_\___|\__, |\___/_/\_\ |___/\___|\__,_|_|  \___|_| |_|
    #              __/ |                                          
    #             |___/                                                                    
    # Attempt to get requirements with strict regex pattern. Move on if good result found
    main_re = re.compile(params.regex_strict)
    elements = [el for el in params.page_content.desc_soup.find_all(string=main_re) if 0 < len(el.text) < 475]
    
    for b in params.bad_match_tight:
        elements = [e for e in elements if b not in e.text.lower()]

    if elements:
        text = '\n'.join([x.text for x in elements])
        results.data_found = text + '\n\nFound via main regex pattern'
        params.page_content.exp_search.found_strict = True
        results.found_strict = True
        return results

    #   _   _                _                                     _     
    #  | | | |              | |                                   | |    
    #  | |_| | ___  __ _  __| | ___ _ __   ___  ___  __ _ _ __ ___| |__  
    #  |  _  |/ _ \/ _` |/ _` |/ _ \ '__| / __|/ _ \/ _` | '__/ __| '_ \ 
    #  | | | |  __/ (_| | (_| |  __/ |    \__ \  __/ (_| | | | (__| | | |
    #  \_| |_/\___|\__,_|\__,_|\___|_|    |___/\___|\__,_|_|  \___|_| |_|
    #                                                                    
    #         
    # Attempt to find appropriate header and match under it leniently
    header = params.page_content.desc_soup.find(string=re.compile(params.regex_header))
    if header:
        # Set qualifications to list of strings that come after header
        desc_strs = list(params.page_content.desc_soup.stripped_strings)
        for i, s in enumerate(desc_strs):
            if s == header:
                qualifications = desc_strs[i+1:]
                experience_reqs = []
                for s in qualifications:
                    for kw in params.header_search_kws:
                        if kw.lower() in s.lower():
                            if s not in experience_reqs and len(s) < 400:
                                for b in params.bad_match_tight:
                                    if b.lower() in s.lower():
                                        break
                                else:
                                    experience_reqs.append(s)
                if experience_reqs:
                    results.data_found = '\n'.join(experience_reqs) + '\n\nFound via Header search'
                    results.found_via_header = True
                    return results
                else:
                    break

    #   _   _ _____   _____                     _     
    #  | | | |_   _| /  ___|                   | |    
    #  | | | | | |   \ `--.  ___  __ _ _ __ ___| |__  
    #  | | | | | |    `--. \/ _ \/ _` | '__/ __| '_ \ 
    #  | |_| |_| |_  /\__/ /  __/ (_| | | | (__| | | |
    #   \___/ \___/  \____/ \___|\__,_|_|  \___|_| |_|
    #                                                 
    #                           
    # Header was not found. Look for very loose matches and ask user
    candidates = params.page_content.desc_soup.find_all(string=re.compile(params.regex_loose))
    candidates = [x for x in candidates if len(x) < 400]
    for b in params.bad_match_loose:
        candidates = [x for x in candidates if b not in x]
    
    if candidates:
        fail_str = f"No {params.searh_name} requirements found"
        candidates.append(fail_str)
        
        padding = '-' * 40
        print(f"\n{padding}Choose the {params.searh_name}{padding}\n")
        for i, option in enumerate(candidates):
            print(f"{i}: {option}")
            print(f"{'-' * 20}\n")
        print(padding)
        choice = 0                                                      # Needs to take multiple answers
        
        results.data_found = str(candidates[choice]) + '\n\nFound via UI search'
        results.found_via_ui = results.data_found != fail_str + '\n\nFound via UI search'
    
    return results