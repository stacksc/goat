import json
def is_empty_entry(entry):
    """Check if the entry is a dictionary with empty args, options, and subcommands."""
    return (isinstance(entry, dict) and 
            'args' in entry and not entry['args'] and 
            'options' in entry and not entry['options'] and 
            'subcommands' in entry and not entry['subcommands'])

def clean_json(data):
    if isinstance(data, dict):
        # Create a list of keys to remove
        keys_to_remove = [key for key, value in data.items() if is_empty_entry(value)]

        # Remove the identified keys
        for key in keys_to_remove:
            del data[key]

        # Recursively clean the remaining items
        for key in data:
            data[key] = clean_json(data[key])

    elif isinstance(data, list):
        # Recursively clean the items in the list
        return [clean_json(item) for item in data if not is_empty_entry(item)]

    return data

def main():
    input_file = 'az.json'  # Replace with the path to your JSON file
    output_file = 'cleaned_az.json'  # The cleaned data will be saved to this file

    with open(input_file, 'r') as file:
        json_data = json.load(file)

    cleaned_data = clean_json(json_data)

    with open(output_file, 'w') as file:
        json.dump(cleaned_data, file, indent=2)

    print(f"Cleaned JSON data has been saved to {output_file}")

if __name__ == "__main__":
    main()
