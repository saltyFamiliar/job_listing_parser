import os
import csv
from sys import argv
from tqdm import tqdm
import re

from Utils import *


RESULTS = 'results.txt'
HAS_EXTRA_DATA = 'has_extra_data.txt'
NOT_FOUND = 'not_found.txt'

#dir_name = argv[1]
#dir_name = 'html_files/test_sample'
#dir_name = 'html_files/small'
#dir_name = 'html_files/medium'
dir_name = 'html_files/27-11-2021'

# clear output files
for name in [RESULTS, HAS_EXTRA_DATA, NOT_FOUND, 'has_education.txt', 'has_experience.txt']:
    with open(name, 'w') as f:
        f.write('')
os.system('clear')


print(f"\n{23 * ' '}COLLECTING DATA FROM FILES IN {dir_name}/\n")
job_file_names = os.listdir(dir_name)
job_file_names = [j for j in job_file_names if j[-5:] == '.html']


# Generate soup list from job_file_names
soup_bowls = []
for file_name in tqdm(job_file_names, desc="Parsing Files", unit_scale=True):
    soup_bowls.append(SoupBowl(f"{dir_name}/{file_name}"))


# Create list of job data dicts and SearchResults
job_dicts = []
total_page_contents = []
for bowl in tqdm(soup_bowls, desc="Scraping Data", unit_scale=True):
    job_dict, page_content = find_jobinfo(bowl)
    job_dicts.append(job_dict)
    total_page_contents.append(page_content)


# Separate SearchResults into appropriate lists
no_exp_data = 0
no_edu_data = 0
experience_explicit = 0
education_explicit = 0
experience_strict = 0
education_strict = 0
experience_header = 0
education_header = 0
experience_ui = 0
education_ui = 0
for page_content in total_page_contents:
    experience_explicit += page_content.exp_search.found_explicit
    education_explicit += page_content.edu_search.found_explicit
    experience_strict += page_content.exp_search.found_strict
    education_strict += page_content.edu_search.found_strict
    experience_header += page_content.exp_search.found_via_header
    education_header += page_content.edu_search.found_via_header 
    experience_ui += page_content.exp_search.found_via_ui
    education_ui += page_content.edu_search.found_via_ui
    no_exp_data += not page_content.exp_search.found()
    no_edu_data += not page_content.edu_search.found()


# formatting to .csv
with open('jobinfo.csv', 'w') as csvfile:
     job_writer = csv.writer(csvfile, delimiter=',')
     cols = list(job_dicts[0].keys())
     job_writer.writerow(cols)        
     for job in tqdm(job_dicts, desc="Writing to CSV", unit_scale=True):
         vals = list(job.values())
         job_writer.writerow(vals)


print(f"\n{40 * '-'}RESULTS{40 * '-'}\n")
print(f"{'Found explicit experience data in':>45} {experience_explicit/len(total_page_contents) * 100:>30.2f}% of files.")
print(f"{'Found experience data via strict search in':>45} {experience_strict/len(total_page_contents) * 100:>30.2f}% of files.")
print(f"{'Found experience data via header search in':>45} {experience_header/len(total_page_contents) * 100:>30.2f}% of files.")
print(f"{'Found experience data via ui in':>45} {experience_ui / len(total_page_contents) * 100:>30.2f}% of files.")
print(f"{'Found experience data total:':>45} {(len(total_page_contents) - no_exp_data)/len(total_page_contents) * 100:>30.2f}% of files.")
print(f"{'No experience data found in':>45} {no_exp_data/len(total_page_contents) * 100:>30.2f}% of files.")
print()
print(f"{'Found explicit education data in':>45} {education_explicit/len(total_page_contents) * 100:>30.2f}% of files")
print(f"{'Found education data via strict search in':>45} {education_strict/len(total_page_contents) * 100:>30.2f}% of files.")
print(f"{'Found education data via header search in':>45} {education_header/len(total_page_contents) * 100:>30.2f}% of files.")
print(f"{'Found education data via ui in':>45} {education_ui / len(total_page_contents) * 100:>30.2f}% of files.")
print(f"{'Found education data total:':>45} {(len(total_page_contents) - no_edu_data)/len(total_page_contents) * 100:>30.2f}% of files.")
print(f"{'No education data found in':>45} {no_edu_data/len(total_page_contents) * 100:>30.2f}% of files.")

print(f"\n{43 * '-'}-{43 * '-'}\n")

# print("EXP IN DESC")
# for res in exp_in_desc:
#     print(res.file_searched)
# print('\nEDU IN DESC')
# for res in edu_in_desc:
#     print(res.file_searched)