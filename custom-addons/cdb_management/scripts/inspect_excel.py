import openpyxl
import json

def inspect_excel(filepath):
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        sheet = wb.active
        
        headers = [str(cell.value).strip() if cell.value else '' for cell in sheet[1]]
        
        data_samples = []
        for row in sheet.iter_rows(min_row=2, max_row=6, values_only=True):
            data_samples.append([str(val).strip() if val is not None else '' for val in row])
            
        result = {
            'headers': headers,
            'samples': data_samples
        }
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}))

if __name__ == '__main__':
    inspect_excel('/mnt/custom-addons/cdb_management/data/data-cdb.xlsx')
