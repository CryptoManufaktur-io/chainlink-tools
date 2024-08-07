#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import yaml
import sys

def get_latest_tag_version():
    url = "https://github.com/smartcontractkit/external-adapters-js/releases"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    for section in soup.select("div#repo-content-pjax-container section"):
        section_title = section.select_one("h2.sr-only").text.strip().split(" ")[1]
        is_latest = section.select("span.Label.Label--success.Label--large")
        if len(is_latest) > 0:
            return section_title

    exit("Could not find the latest version of adapters in release page https://github.com/smartcontractkit/external-adapters-js/releases")

def get_adapter_versions(tag):
    url = f"https://github.com/smartcontractkit/external-adapters-js/blob/{tag}/MASTERLIST.md"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")    
    table = soup.find('markdown-accessiblity-table')
    table = table.find('table')
    adapter_versions = {}

    for row in table.find('tbody').find_all('tr'):
        cells = row.find_all('td')
        name = cells[0].text.strip()
        version = cells[1].text.strip()
        adapter_versions[name + '-adapter'] = version

    return adapter_versions

def get_updates(yaml_file, adapter_versions):
    response = {'replace_strings': {}, 'to_update_image_versions': {}, 'to_retain_image_versions': {}}

    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)

    for service_name, service in data['services'].items():
        image_name, image_version = service['image'].split('/')[-1].split(':')
        if image_name in adapter_versions:
            new_version = adapter_versions[image_name]
            if new_version != image_version:
                response['to_update_image_versions'][image_name] = {'current': image_version, 'new': new_version}
                response['replace_strings'][service['image']] = service['image'].replace(image_version, new_version)
        else:
            response['to_retain_image_versions'][image_name] = image_version

    return response

def confirm_update(yaml_file):
    while True:
        do_update = input(f"Do you want to update the stack '{yaml_file}' file? (yes/no) ")
        if do_update in {'yes', 'no'}:
            return do_update == 'yes'

def save_updated_yaml(yaml_file, replace_strings):
    with open(yaml_file, 'r') as f:
        content = f.read()
        for target, replacement in replace_strings.items():
            content = content.replace(target, replacement)
        
    with open(yaml_file, 'w') as f:
        f.write(content)

    print(f"'{yaml_file}' file updated")

if __name__ == "__main__":
    if not (3 <= len(sys.argv) <= 4):
        print("Missing expected arguments.")
        print("Usage: ./eaupdate.py [version:Latest/v1.79.0/v1.80.0] [yaml-file-to-update:ea-rpc-composite-por.yml/ea-source-adapters.yml] [(optional) update-stack-file:True/False/Confirm]")
        exit(1)

    tag_version = sys.argv[1]
    yaml_file = sys.argv[2]
    update_file = sys.argv[3] if len(sys.argv) == 4 else 'Confirm'

    if tag_version == 'Latest':
        tag_version = get_latest_tag_version()
        print(f"Using adapter release version {tag_version}")

    adapter_versions = get_adapter_versions(tag_version)

    if update_file not in {'True', 'False', 'Confirm'}:
        print("Argument for update stack file must be either True, False, or Confirm")
        exit(1)

    response = get_updates(yaml_file, adapter_versions)
    
    print('To be retained')
    print(json.dumps(response['to_retain_image_versions'], indent=4, sort_keys=True))

    print('\n\nTo be updated')
    print(json.dumps(response['to_update_image_versions'], indent=4, sort_keys=True))

    if len(response['to_update_image_versions']) > 0 and update_file == 'Confirm':
        if confirm_update(yaml_file):
            update_file = 'True'
        else:
            update_file = 'False'

    if len(response['to_update_image_versions']) > 0 and update_file == 'True':
        save_updated_yaml(yaml_file, response['replace_strings'])
