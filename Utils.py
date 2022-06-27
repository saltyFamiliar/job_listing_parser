from pydoc import describe
import re
from typing import Any
from unicodedata import name
import bs4


class PageContent():
    def __init__(self, fn, soup) -> None:
        self.file_searched = fn
        self.soup = soup
        self.desc_html = []
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


def print_debug(s: Any, name: str):
    print(f"{43 * '-'}-{43 * '-'}")
    print(f"{type(s)} {name} :")
    print('-' * 50)
    print('\n' + str(s))
    print(f"\n{43 * '-'}-{43 * '-'}")


def any_of_in(s: list[str], target: str) -> bool:
    for c in s:
        if c in target:
            return True
    return False

# Writes entry to file at given filename
def add_entry(filename: str, result: PageContent, raw: bool=False) -> None:
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
            # Exp section contains exp requirements. Use exp section contents and move on
            if not 'Not Specified' in soup.find(id=v).text:
                page_content.exp_search.found_explicit = True
                data_dict[k] = soup.find(id=v).text
                continue
            # Attempt to get exp requirements with strict regex pattern. Move on if good result found
            exp_re = re.compile(
                '((\d\+?|([Oo]ne|[Tt]wo|[Tt]hree|[Ff]our|[Ff]ive|[Ss]ix|[Ss]even|[Ee]ight|[Nn]ine|[Tt]en))( |-)([Yy]ear|[Mm]onth)|[Ee]xperience)')
            exp_els = [el for el in desc_soup.find_all(string=exp_re) if 0 < len(el.text) < 400]
            
            bad_matches = ['$', '?', 'DaVita', 'xperiences', 'will experience', 
                           'human experience', 'inexperience', 'experience.', 'age', 'he experience']
            for b in bad_matches:
                exp_els = [e for e in exp_els if b not in e.text.lower()]

            if exp_els:
                exp_text = '\n'.join([x.text for x in exp_els])
                data_dict[k] = exp_text + '\nMain regex'
                page_content.exp_search.found_strict = True
                continue
            
            # Attempt to find appropriate header and match under it leniently
            header_re = re.compile('(EXPERIENCE|Qualifications|QUALIFICATIONS)')
            experience_header = desc_soup.find(string=re.compile(header_re))
            if experience_header:
                # Get description as list of strings
                good_matches = ['year', 'month', 'experience']
                qualifications = page_content.desc_soup.stripped_strings
                for g in good_matches:
                    qualifications = [q for q in qualifications if g in q.lower()]
                if qualifications:
                    data_dict[k] = '\n'.join(qualifications) + '\nHeader search'
                    page_content.exp_search.found_via_header = True
                    continue

                # Get tag where header was found
                # experience_header = experience_header.parent
                # exp_re = re.compile('(year|Year|month|Month)')
                # exp_text = experience_header.find_next(string=exp_re)
                
                # if (exp_text and len(exp_text) > 350) or any_of_in(['%', '$', 'age'], exp_text):
                #     exp_text = 'No experience requirements found'
                # else:
                #     page_content.exp_search.found_via_header = True
                #data_dict[k] = exp_text
                #continue

            # Header was not found. Look for very loose matches and ask user
            bad_matches = ['125 years', 'DaVita', '$', '%', 'million', 'Degree', 'degree', 'UTSW', 'HCA', 'age', 'salary']
            candidates = desc_soup.find_all(string=re.compile('([Yy]ear|[Mm]onth)'))
            candidates = [x for x in candidates if len(x) < 400]
            for b in bad_matches:
                candidates = [x for x in candidates if b not in x]
            
            if candidates:
                fail_str = "No experience requirements found"
                candidates.append(fail_str)
                
                padding = '-' * 40
                print(f"\n{padding}Choose the experience{padding}\n")
                for i, option in enumerate(candidates):
                    print(f"{i}: {option}")
                    print(f"{'-' * 20}\n")
                print(padding)
                choice = int(input('>'))
                
                data_dict[k] = str(candidates[choice]) + '\nUI'
                page_content.exp_search.found_via_ui = data_dict[k] != fail_str
            else:
                data_dict[k] = 'No experience requirements found'
        


        elif k == 'Education':
            possible = []
            if not 'No Minimum' in soup.find(id=v).text:
                page_content.has_education = True
                data_dict[k] = soup.find(id=v).text
            else:
                edu_re = re.compile('([Bb]achelor|[Mm]aster|[Pp][Hh][Dd]|ADN|BSN|BLS)')
                edu_els = page_content.soup.find_all(string=edu_re)
                edu_els = [x for x in edu_els if 0 < len(x.text) < 400]
                if edu_els:
                    bad_matches = []
                    edu_text = '\n'.join([e.text for e in edu_els if e.text not in bad_matches])
                    page_content.edu_in_desc = True
                else:
                    header_re = re.compile('(EDUCATION|Qualifications|QUALIFICATIONS)')
                    education_header = soup.find(string=re.compile(header_re))
                    possible = []
                    if education_header:
                        education_header = education_header.parent
                        if len(education_header.text) > 1000:
                            edu_text = 'No education requirements found'
                        else:
                            edu_re = re.compile('([Bb]achelor|[Mm]aster|[Pp][Hh][Dd]|BLS|[Aa]ccredited|ADN|BSN)')
                            edu_text = education_header.find_next(string=edu_re)
                            if (edu_text and len(edu_text) > 350):
                                edu_text = 'No education requirements found'
                            else:
                                page_content.edu_in_desc = True
                    else:
                        edu_text = 'No education requirements found'
                        for y in ['achelor', 'master', 'Master', 'PhD', 'ssociate', 'BLS', 'ccredited', 'ADN', 'BSN']:
                            inner_soup = soup.find(id=id_dict['Description'])    
                            if y in inner_soup.text:
                                candidates = inner_soup.find_all(string=re.compile(y))
                                candidates = [x.parent for x in candidates if len(x) < 1000]
                                #candidates = [x for x in candidates if not any_of_in(['125 years', 'DaVita'], x.text)]
                                if candidates:
                                    possible += candidates
                                    page_content.edu_in_desc = True
                                #exp_text += soup.find(id=id_dict['Description']).text
                                #exp_text = "Experience requirements in description"
                                #exp_text = str(possible)
                if not possible:
                    data_dict[k] = edu_text
                elif len(possible) == 1:
                    data_dict[k] = str(possible[0])
                else:
                    print('\n')
                    print(len(possible))
                    possible.append("Education not found")
                    for i, choice in enumerate(possible):
                       print(f"{i}: {choice}")
                       print(('-' * 40) + '\n')
                    choice = int(input("Choose correct option for education: \n"))
                    data_dict[k] = str(possible[choice])
                    page_content.edu_in_desc = str(possible[choice]) != "Education not found"
        
        else:
            try:
                data_dict[k] = soup.find(id=v).text
            except:
                data_dict[k] = ''


    
    #Removes location data that is sometimes at the end of the job title in posting
    data_dict['JobTitle'] = data_dict['JobTitle'].split('-')[0]

    return data_dict, page_content