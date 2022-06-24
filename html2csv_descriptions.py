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
dir_name = 'html_files/small'
#dir_name = 'html_files/medium'
#dir_name = 'html_files/27-11-2021'

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
total_results = []
for bowl in tqdm(soup_bowls, desc="Scraping Data", unit_scale=True):
    job_dict, search_result = find_jobinfo(bowl)
    job_dicts.append(job_dict)
    total_results.append(search_result)


# Write results to appropriate files
for result in total_results:
    if result.found():
            if result.has_extra_data():
                add_entry(HAS_EXTRA_DATA, result, raw=True)
            else:
                add_entry(RESULTS, result)
    else:
        add_entry(NOT_FOUND, result)


# Separate SearchResults into appropriate lists
good_data = []
extra_data = []
no_data = []
has_experience = 0
has_education = 0
edu_in_desc = []
exp_in_desc = []
for result in total_results:
    has_experience += result.has_experience
    has_education += result.has_education
    
    if result.education_in_desc:
        edu_in_desc.append(result)
    
    if result.exp_in_desc:
        exp_in_desc.append(result)

    if result.found():
        if result.has_extra_data():
            extra_data.append(result)
        else:
            good_data.append(result)
    else:
        no_data.append(result)


# formatting to .csv
with open('jobinfo.csv', 'w') as csvfile:
     job_writer = csv.writer(csvfile, delimiter=',')
     cols = list(job_dicts[0].keys())
     job_writer.writerow(cols)        
     for job in tqdm(job_dicts, desc="Writing to CSV", unit_scale=True):
         vals = list(job.values())
         job_writer.writerow(vals)


print(f"\n{40 * '-'}RESULTS{40 * '-'}\n")
print(f"Found good data in {len(good_data)/len(total_results) * 100:.2f}% of files")
print(f"Found extra data in {len(extra_data)/len(total_results) * 100:.2f}% of files.")
print(f"Data not found in {len(no_data)/len(total_results) * 100:.2f}% of files.")
print(f"Experience section used in {has_experience/len(total_results) * 100:.2f}% of files.")
print(f"Experience in desc in {len(exp_in_desc)/len(total_results) * 100:.2f}% of files.")
print(f"Education section used in {has_education/len(total_results) * 100:.2f}% of files.")
print(f"Education in desc in {len(edu_in_desc)/len(total_results) * 100:.2f}% of files.")
print(f"\n{43 * '-'}-{43 * '-'}\n")

# print("EXP IN DESC")
# for res in exp_in_desc:
#     print(res.file_searched)
# print('\nEDU IN DESC')
# for res in edu_in_desc:
#     print(res.file_searched)