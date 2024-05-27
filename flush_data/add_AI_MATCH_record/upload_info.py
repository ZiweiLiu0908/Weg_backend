import os
import csv
import json


def read_csv_files(directory):
    all_data = []
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader)  # Assuming the first row is the header
                for row in reader:
                    school_name, major_name_cn, major_name_orig, content = row
                    # You can process each row as needed
                    # For now, let's just append it to all_data
                    all_data.append({
                        "学校名称": school_name,
                        "专业中文名称": major_name_cn,
                        "专业原名称": major_name_orig,
                        "内容": content
                    })
    return all_data


def main():
    directory = '.'  # Change this to your directory path
    all_data = read_csv_files(directory)

    # Write all_data to a JSON file
    with open('output.json', 'w', encoding='utf-8') as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
