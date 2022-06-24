from typing import Any
from bs4 import BeautifulSoup
import os
import csv
from sys import argv
from tqdm import tqdm
import re

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
    
RESULTS = 'results.txt'
HAS_EXTRA_DATA = 'has_extra_data.txt'
NOT_FOUND = 'not_found.txt'

#dir_name = argv[1]
#dir_name = 'html_files/test_sample'
#dir_name = 'html_files/small'
#dir_name = 'html_files/medium'
dir_name = 'html_files/27-11-2021'

filenames = os.listdir(dir_name)

os.system('clear')
print(f"\n{23 * ' '}COLLECTING DATA FROM FILES IN {dir_name}/\n")

html_docs = []
for i in tqdm(range(len(filenames)), desc="Opening Files", unit_scale=True):
 #   if i == 10:
 #       break
    name = filenames[i]
    if name[-5:] == '.html':
        #print(f"Opening file {i}")
        html_docs.append(open(f"{dir_name}/{name}"))

#making list of beautifulsoup objects
contents = []
for i in tqdm(range(len(html_docs)), desc="Parsing Files", unit_scale=True):
  #  if i == 10:
  #      break
    html = html_docs[i]
    #print(f"Parsing file {i}")
    contents.append(BeautifulSoup(html, 'html.parser'))

# clear output files
for name in [RESULTS, HAS_EXTRA_DATA, NOT_FOUND, 'has_education.txt', 'has_experience.txt']:
    with open(name, 'w') as f:
        f.write('')

# Search for given keywords and write results to appropriate files
def search(desc_html, kws: list[str], fn: str) -> SearchResult:
    # Returns entry header and footer strings
    def entry_border(title: str) -> tuple[str, str]:
        padding = '-' * ((80 - len(title)) // 2)
        header = f"\n{padding}{title}{padding}\n"
        footer = f"\n{'-' * (len(header)-2)}\n"
        return header, footer
    
    # Writes entry to file at given filename
    def write(filename: str, result: SearchResult, raw: bool=False) -> None:
        with open(filename, "a") as f:
            header, footer = entry_border(result.file_searched)
            if result.found():
                content = result.raw_data() if raw else result.data()
            else:
                content = "NO MATCH FOUND IN PAGE\n"
            f.write(header)
            f.write(content)
            f.write(footer)

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

    if result.found():
        if result.has_extra_data():
            write(HAS_EXTRA_DATA, result, raw=True)
        else:
            write(RESULTS, result)
    else:
        write(NOT_FOUND, result)
    
    return result


#finds info on jobs for location, job number, job title and salary
def find_jobinfo(soup, filename):
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

    keywords = ['diploma', 'degree', 'Bachelor', 'Master', 'phd', 'ged', 'associate', 'year', 'graduate']
    #keywords = ['qualifications']

    #gets each key its value in text form
    for k, v in id_dict.items():
        if k == 'Description':
            #for x in soup.find(id=v):
            search_result = search(soup.find(id=v), keywords, filename)
        if k == 'Experience':
            if not 'Not Specified' in soup.find(id=v).text:
                search_result.has_experience = True
                with open('has_experience.txt', 'a') as f:
                    f.write(soup.find(id=v).text + '\n')
            else:
                for y in ['+ year', '+ Year']:
                    if y in soup.find(id=id_dict['Description']).text:
                        search_result.exp_in_desc = True

        if k == 'Education':
            if not 'No Minimum' in soup.find(id=v).text:
                search_result.has_education = True
                with open('has_education.txt', 'a') as f:
                    f.write(soup.find(id=v).text + '\n')
            else:
                for edu in ['achelor', 'master', 'Master', 'egree']:
                    if edu in soup.find(id=id_dict['Description']).text:
                        search_result.education_in_desc = True

        #id_dict[k] = soup.find(id=v).text

    #Removes location data that is sometimes at the end of the job title in posting
    #id_dict['JobTitle'] = id_dict['JobTitle'].split('-')[0]

    return id_dict, search_result

#making list of job info dictionaries to become .csv
job_dicts = []
total_results = []
#for idx, i in enumerate(contents):
for i in tqdm(range(len(contents)), desc="Scraping Data", unit_scale=True):
    #print(f"Scraping {idx}")
    job_dict, search_result = find_jobinfo(contents[i], filenames[i])
    job_dicts.append(job_dict)
    total_results.append(search_result)

# Separate SearchResults into appropriate lists
good_data = []
extra_data = []
no_data = []
has_experience = 0
has_education = 0
edu_in_desc = 0
exp_in_desc = 0
edu_in_desc_list = []
exp_in_desc_list = []
for result in total_results:
    has_experience += result.has_experience
    has_education += result.has_education
    edu_in_desc += result.education_in_desc
    exp_in_desc += result.exp_in_desc
    
    if result.education_in_desc:
        edu_in_desc_list.append(result.file_searched)
    
    if result.exp_in_desc:
        exp_in_desc_list.append(result.file_searched)

    if result.found():
        if result.has_extra_data():
            extra_data.append(result)
        else:
            good_data.append(result)
    else:
        no_data.append(result)

print(f"\n{40 * '-'}RESULTS{40 * '-'}\n")
print(f"Found good data in {len(good_data)/len(total_results) * 100:.2f}% of files")
print(f"Found extra data in {len(extra_data)/len(total_results) * 100:.2f}% of files.")
print(f"Data not found in {len(no_data)/len(total_results) * 100:.2f}% of files.")
print(f"Experience section used in {has_experience/len(total_results) * 100:.2f}% of files.")
print(f"Experience in desc in {exp_in_desc/len(exp_in_desc_list) * 100:.2f}% of files.")
print(f"Education section used in {has_education/len(total_results) * 100:.2f}% of files.")
print(f"Education in desc in {edu_in_desc/len(total_results) * 100:.2f}% of files.")
print(f"\n{43 * '-'}-{43 * '-'}\n")

for res in exp_in_desc_list:
    print("EXP IN DESC")
    print(res.file_searched)

print()

for res in edu_in_desc_list:
    print('EDU IN DESC')
    print(res.file_searched)


def print_debug(s: Any, name: str):
    print(f"{43 * '-'}-{43 * '-'}")
    print(f"{type(s)} {name} :")
    print('-' * 50)
    print('\n' + str(s))
    print(f"\n{43 * '-'}-{43 * '-'}")

# keywords = ['diploma', 'degree', 'Bachelor', 'Master', 'phd', 'ged', 'associate', 'year', 'graduate']
# reduced_results = []
# for e in extra_data:
#     print_debug(e.soup, 'e.soup')
#     for t in e.soup.find_all(string=re.compile('experience')):
#         print_debug(t, 't')
#         #print_debug(t.next_element.next_element.next_element.next_element, 't.next_element')
    
#     break


# #formatting to .csv
# with open('jobinfo.csv', 'w') as csvfile:
#     job_writer = csv.writer(csvfile, delimiter=',')
#     cols = list(job_dicts[0].keys())
#     job_writer.writerow(cols)        
#     for i, job in enumerate(job_dicts):
#         print(f"Writing {i}")
#         vals = list(job.values())
#         job_writer.writerow(vals)

for html_doc in html_docs:
    html_doc.close()