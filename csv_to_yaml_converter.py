# Autotagger
this script converts csv to yml file
#!/usr/bin/env python3
"""
CSV to YAML Converter
Converts CSV files from Google Sheets export to hierarchical YAML format
"""

import pandas as pd
import yaml
import os
import glob
from collections import defaultdict, OrderedDict

class LiteralStr(str):
    """Custom string class to represent literal style strings in YAML"""
    pass

def literal_str_representer(dumper, data):
    """Custom representer for literal style strings"""
    if '\n' in data or len(data) > 80:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def clean_text(text):
    """Clean and format text for YAML output"""
    if pd.isna(text) or text == '' or str(text).strip() == '':
        return ""
    # Remove extra whitespace and preserve line breaks
    cleaned = str(text).strip()
    # Return as LiteralStr for multiline content
    if '\n' in cleaned or len(cleaned) > 80:
        return LiteralStr(cleaned)
    return cleaned

def read_csv_with_special_handling(csv_file):
    """Read CSV file with special handling for files like Billing.csv"""
    
    # First, try to read normally
    try:
        df = pd.read_csv(csv_file)
        
        # Check if this looks like a Billing.csv type file
        # (first column has metadata, second row is empty, third row has headers)
        if len(df.columns) > 0 and ('Unnamed:' in str(df.columns[0]) or 'Tags in green' in str(df.columns[0])):
            print(f"Detected special format in {csv_file}, trying alternative reading...")
            
            # Try reading from row 2 (0-indexed) where the real headers are
            df = pd.read_csv(csv_file, skiprows=2)
            print(f"Successfully read {csv_file} with skiprows=2")
            
        return df
        
    except Exception as e:
        print(f"Error reading {csv_file}: {str(e)}")
        return None

def process_csv_files():
    """Process all CSV files and convert to YAML structure"""
    
    # Find all CSV files in current directory
    csv_files = glob.glob("*.csv")
    csv_files = [f for f in csv_files if not f.startswith('.') and f != 'github_actions_analysis.csv']
    
    print(f"Found {len(csv_files)} CSV files to process:")
    for file in csv_files:
        print(f"  - {file}")
    
    # Initialize the main tags structure
    tags_structure = OrderedDict()
    
    for csv_file in csv_files:
        print(f"\nProcessing {csv_file}...")
        
        try:
            # Read CSV file with special handling
            df = read_csv_with_special_handling(csv_file)
            
            if df is None:
                continue
            
            # Print column names for debugging
            print(f"Columns in {csv_file}: {list(df.columns)}")
            
            # Handle different column name variations
            main_category_col = None
            feature_col = None
            functionality_col = None
            what_covers_col = None
            faq_col = None
            notes_col = None
            
            for col in df.columns:
                col_lower = col.lower().strip()
                if 'main category' in col_lower or 'main_category' in col_lower:
                    main_category_col = col
                elif 'feature' in col_lower:
                    feature_col = col
                elif 'core functionality' in col_lower or 'functionality' in col_lower:
                    functionality_col = col
                elif 'what does it cover' in col_lower or 'what_it_cover' in col_lower:
                    what_covers_col = col
                elif 'common faq' in col_lower or 'faq' in col_lower:
                    faq_col = col
                elif 'additional note' in col_lower or 'note' in col_lower:
                    notes_col = col
            
            if not main_category_col:
                print(f"Warning: Could not find main category column in {csv_file}")
                continue
            
            # Track the current main category for rows where it's empty
            current_main_category = None
                
            # Process each row
            for idx, row in df.iterrows():
                # Skip completely empty rows
                if row.isna().all():
                    continue
                
                # Get the main category (use previous value if current is empty)
                main_category = clean_text(row.get(main_category_col))
                feature = clean_text(row.get(feature_col))
                functionality = clean_text(row.get(functionality_col))
                
                # Update current main category if we have a new one
                if main_category:
                    current_main_category = main_category
                elif current_main_category:
                    main_category = current_main_category
                
                # Skip rows that don't have meaningful data
                if not main_category and not feature:
                    continue
                
                # Use the CSV filename as main category if main_category is empty
                if not main_category:
                    main_category = os.path.splitext(csv_file)[0]
                
                # Create the hierarchical key
                if feature and functionality:
                    tag_key = f"{main_category} > {feature} > {functionality}"
                elif feature:
                    tag_key = f"{main_category} > {feature}"
                else:
                    tag_key = main_category
                
                # Get the content
                what_it_covers = clean_text(row.get(what_covers_col)) if what_covers_col else ""
                common_faq = clean_text(row.get(faq_col)) if faq_col else ""
                additional_note = clean_text(row.get(notes_col)) if notes_col else ""
                
                # Create the tag structure
                tag_data = OrderedDict()
                if what_it_covers:
                    tag_data['what_it_cover'] = what_it_covers
                if common_faq:
                    tag_data['common_faq'] = common_faq
                if additional_note:
                    tag_data['additional_note'] = additional_note
                
                # Only add if there's meaningful content
                if tag_data:
                    if tag_key not in tags_structure:
                        tags_structure[tag_key] = []
                    tags_structure[tag_key].append(tag_data)
        
        except Exception as e:
            print(f"Error processing {csv_file}: {str(e)}")
            continue
    
    return tags_structure

def save_to_yaml(tags_structure, output_file="tags_output.yml"):
    """Save the tags structure to YAML file"""
    
    # Create the final structure
    final_structure = OrderedDict()
    final_structure['tags'] = []
    
    for tag_name, tag_content_list in tags_structure.items():
        tag_entry = OrderedDict()
        tag_entry[tag_name] = tag_content_list
        final_structure['tags'].append(tag_entry)
    
    # Custom YAML representer for OrderedDict to maintain order
    def represent_ordereddict(dumper, data):
        return dumper.represent_dict(data.items())
    
    # Add custom representers
    yaml.add_representer(OrderedDict, represent_ordereddict)
    yaml.add_representer(LiteralStr, literal_str_representer)
    
    # Write to YAML file with proper formatting
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(final_structure, f, 
                 default_flow_style=False, 
                 allow_unicode=True,
                 sort_keys=False,
                 indent=2,
                 width=1000)
    
    print(f"\nYAML file saved as: {output_file}")
    return output_file

def main():
    """Main function"""
    print("CSV to YAML Converter with Literal Style")
    print("=" * 50)
    
    # Process CSV files
    tags_structure = process_csv_files()
    
    if not tags_structure:
        print("No data found to convert.")
        return
    
    print(f"\nProcessed {len(tags_structure)} unique tags")
    
    # Save to YAML
    output_file = save_to_yaml(tags_structure)
    
    print(f"\nConversion completed successfully!")
    print(f"Output file: {output_file}")
    
    # Show a preview of the structure
    print("\nPreview of generated structure:")
    print("-" * 30)
    count = 0
    for tag_name in tags_structure.keys():
        if count < 5:  # Show first 5 tags
            print(f"  - {tag_name}")
            count += 1
        else:
            print(f"  ... and {len(tags_structure) - 5} more tags")
            break

if __name__ == "__main__":
    main()
