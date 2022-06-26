import re
from typing import Any
from unicodedata import name
import bs4


class PageContent():
    def __init__(self, fn, soup):
        self.file_searched = fn
        self.soup = soup
        self.desc_html = []
        self.has_experience = False
        self.has_education = False
        self.edu_in_desc = False
        self.exp_in_desc = False
    
    def has_extra_data(self) -> bool:
        return len(self.data()) > 700

    def found(self) -> bool:
        return len(self.data()) > 0

    def data(self) -> str:
        return ''.join([x.text for x in self.desc_html])
    
    def raw_data(self) -> str:
        return ''.join(map(str, self.desc_html))


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
        possible = []
        
        if k == 'Description':
            for e in soup.find(id=v):
                page_content.desc_html.append(e)
            data_dict[k] = soup.find(id=v).text
        
        elif k == 'Experience':
            if not 'Not Specified' in soup.find(id=v).text:
                page_content.has_experience = True
                with open('has_experience.txt', 'a') as f:
                    f.write(soup.find(id=v).text + '\n')
                data_dict[k] = soup.find(id=v).text
            else:
                exp_re = re.compile('(\d\+?|([Oo]ne|[Tt]wo|[Tt]hree|[Ff]our|[Ff]ive|[Ss]ix|[Ss]even|[Ee]ight|[Nn]ine|[Tt]en)) ([Yy]ear|[Mm]onth)')
                exp_el = soup.find(string=exp_re)
                if exp_el and len(exp_el.text) < 500:
                    exp_text = exp_el.text
                    page_content.exp_in_desc = True
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
                            page_content.exp_in_desc = True
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
                                    page_content.exp_in_desc = True
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
                    choice = int(input("Choose correct option for experience: \n"))
                    data_dict[k] = str(possible[choice])
                    page_content.exp_in_desc = str(possible[choice]) != "Experience not found"
        
        
        elif k == 'Education':
            if not 'No Minimum' in soup.find(id=v).text:
                page_content.has_education = True
                with open('has_education.txt', 'a') as f:
                    f.write(soup.find(id=v).text + '\n')
                data_dict[k] = soup.find(id=v).text
            else:
                edu_re = re.compile('([Bb]achelor|[Mm]aster|[Pp][Hh][Dd]|ADN|BSN|BLS)')
                edu_els = soup.find_all(string=edu_re)
                edu_els = [x for x in edu_els if len(x.text) < 400 and x.text != '']
                if edu_els:
                    edu_text = '\n'.join([e.text for e in edu_els])
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