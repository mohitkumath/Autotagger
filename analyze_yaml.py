#!/usr/bin/env python3
import yaml

def analyze_yaml():
    with open('tags_output.yml', 'r') as f:
        data = yaml.safe_load(f)

    tags = data['tags']
    print(f'Total number of tags: {len(tags)}')
    print('\nTags breakdown by main category:')

    categories = {}
    for tag_entry in tags:
        for tag_name in tag_entry.keys():
            main_cat = tag_name.split(' > ')[0]
            if main_cat not in categories:
                categories[main_cat] = 0
            categories[main_cat] += 1

    for cat, count in sorted(categories.items()):
        print(f'  {cat}: {count} tags')
    
    print(f'\nTotal categories represented: {len(categories)}')

if __name__ == "__main__":
    analyze_yaml()
