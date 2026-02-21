import openpyxl
from datetime import datetime
import re

# Spanish month map
MONTHS_ES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

def clean_val(val):
    if val is None:
        return False
    s = str(val).strip()
    if s.lower() in ['n/a', 'no aplica', 'no hay', 'ninguno', 'ninguna', '']:
        return False
    return s

def parse_date(val):
    if not val:
        return False
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    s = str(val).lower().strip()
    
    # Try month names in Spanish: "Octubre 17 2020" or "17 de Octubre 2020"
    for month_name, month_num in MONTHS_ES.items():
        if month_name in s:
            match = re.search(r'(\d{1,2})', s)
            match_year = re.search(r'(\d{2,4})', s.split(month_name)[-1])
            if match and match_year:
                day = int(match.group(1))
                year_str = match_year.group(1)
                year = int(year_str)
                if len(year_str) == 2:
                    year += 1900 if year > 30 else 2000
                try:
                    return datetime(year, month_num, day).strftime('%Y-%m-%d')
                except:
                    pass
    
    # Try common formats
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%d/%m/%y', '%y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except:
            continue
            
    # Regex for mixed separators like 71-10-18 or 18/10/71
    match = re.search(r'(\d{2,4})[-/](\d{1,2})[-/](\d{2,4})', s)
    if match:
        p1, m, p2 = match.groups()
        # If p1 > 31, it's likely the year
        if int(p1) > 31:
            y_str, d_str = p1, p2
        else:
            d_str, y_str = p1, p2
            
        y = int(y_str)
        if len(y_str) == 2:
            y += 1900 if y > 30 else 2000
        try:
            return datetime(y, int(m), int(d_str)).strftime('%Y-%m-%d')
        except:
            pass

    # Try year only
    if re.match(r'^\d{4}$', s):
        return f"{s}-01-01"
        
    return False

def smart_search_partner(name):
    if not name:
        return False
    # Clean name: remove extra spaces, commas, etc.
    clean_name = re.sub(r'[,.]', ' ', name).strip()
    # Search for church members first
    partner = env['res.partner'].search([('name', 'ilike', clean_name), ('x_is_church_member', '=', True)], limit=1)
    if not partner:
        # Search all partners
        partner = env['res.partner'].search([('name', 'ilike', clean_name)], limit=1)
    return partner

def get_or_create(model, name):
    if not name:
        return False
    record = env[model].search([('name', 'ilike', name)], limit=1)
    if not record:
        record = env[model].create({'name': name})
    return record.id

def split_children(s):
    if not s:
        return []
    # Pattern to find dates: "Month Day Year"
    # We use this to split the string
    month_pattern = '|'.join(MONTHS_ES.keys())
    # Regex to find names and dates
    # Assuming Name, Month Day Year
    pattern = rf"(.*?)\s+({month_pattern})\s+(\d{{1,2}})\s+(\d{{4}})"
    matches = re.findall(pattern, s, re.IGNORECASE)
    
    children = []
    if matches:
        for match in matches:
            name = match[0].strip().replace(',', '')
            date_str = f"{match[1]} {match[2]} {match[3]}"
            children.append({
                'name': name,
                'birthdate': parse_date(date_str)
            })
    else:
        # Fallback: just split by comma if no dates found
        names = [n.strip() for n in re.split(r'[,;]', s) if n.strip()]
        for n in names:
            children.append({'name': n, 'birthdate': False})
            
    return children

def import_data(filepath):
    wb = openpyxl.load_workbook(filepath, data_only=True)
    sheet = wb.active
    
    rows = list(sheet.iter_rows(min_row=2, values_only=True))
    total = len(rows)
    print(f"Starting import of {total} rows with SMART logic...")
    
    for i, row in enumerate(rows):
        try:
            name = clean_val(row[1])
            if not name:
                continue
            
            # Basic mapping
            partner_vals = {
                'name': name,
                'x_is_church_member': True,
                'x_birthdate': parse_date(clean_val(row[2])),
                'email': clean_val(row[11]),
                'phone': clean_val(row[10]),
                'mobile': clean_val(row[10]),
                'street': clean_val(row[13]),
                'x_current_occupation': clean_val(row[6]),
                'x_baptized': clean_val(row[14]) == 'Si',
                'x_baptism_date': parse_date(clean_val(row[15])),
                'x_church_entry_date': parse_date(clean_val(row[16])),
            }
            
            # Gender, Education, Marital, Occupational mapping (same as before)
            gender = clean_val(row[3])
            if gender: partner_vals['x_gender'] = gender.lower()
            
            edu = clean_val(row[4])
            if edu:
                edu_map = {'primaria': 'primaria', 'secundaria': 'secundaria', 'bachiller': 'secundaria', 'tecnico': 'tecnico', 'universitario': 'universitario', 'grado': 'universitario', 'maestria': 'maestria', 'posgrado': 'maestria', 'doctorado': 'doctorado'}
                for k, v in edu_map.items():
                    if k in edu.lower(): partner_vals['x_education_level'] = v; break
                else: partner_vals['x_education_level'] = 'otro'

            marital = clean_val(row[7])
            if marital:
                m_map = {'soltero': 'soltero', 'casado': 'casado', 'union': 'union_libre', 'divorciado': 'divorciado', 'viudo': 'viudo'}
                for k, v in m_map.items():
                    if k in marital.lower(): partner_vals['x_marital_status'] = v; break
                else: partner_vals['x_marital_status'] = 'otro'

            occ = clean_val(row[5])
            if occ:
                o_map = {'estudiante': 'estudiante', 'privado': 'empleado_privado', 'publico': 'empleado_publico', 'independiente': 'independiente', 'desempleado': 'desempleado', 'hogar': 'hogar', 'jubilado': 'jubilado'}
                for k, v in o_map.items():
                    if k in occ.lower(): partner_vals['x_occupational_status'] = v; break
                else: partner_vals['x_occupational_status'] = 'otro'

            sector_name = clean_val(row[12])
            if sector_name: partner_vals['x_sector'] = sector_name

            for col, field in [(18, 'x_ministry_ids'), (19, 'x_role_ids'), (20, 'x_interested_ministry_ids')]:
                val = clean_val(row[col])
                if val:
                    ids = [get_or_create('church.ministry' if 'ministry' in field else 'church.role', n.strip()) for n in re.split(r'[,;]', val) if n.strip()]
                    partner_vals[field] = [(6, 0, ids)]

            # Create/Update Partner
            partner = env['res.partner'].search([('name', '=', name)], limit=1)
            if partner:
                partner.write(partner_vals)
            else:
                partner = env['res.partner'].create(partner_vals)

            # Clear old relations to refresh
            partner.x_family_relation_ids.unlink()

            # SMART Family Relations
            
            # 1. Spouse
            spouse_name = clean_val(row[8])
            if spouse_name:
                rel_type = 'esposa' if partner_vals.get('x_gender') == 'masculino' else 'esposo'
                related_partner = smart_search_partner(spouse_name)
                env['church.family.relation'].create({
                    'partner_id': partner.id,
                    'relation_type': rel_type,
                    'is_member': True if related_partner else False,
                    'related_partner_id': related_partner.id if related_partner else False,
                    'non_member_name': False if related_partner else spouse_name,
                    'x_birthdate': related_partner.x_birthdate if related_partner else False
                })

            # 2. Children (SPLIT Logic)
            children_str = clean_val(row[9])
            if children_str:
                children = split_children(children_str)
                for child in children:
                    related_partner = smart_search_partner(child['name'])
                    env['church.family.relation'].create({
                        'partner_id': partner.id,
                        'relation_type': 'hijo' if gender == 'masculino' else 'hija', # Simplified
                        'is_member': True if related_partner else False,
                        'related_partner_id': related_partner.id if related_partner else False,
                        'non_member_name': False if related_partner else child['name'],
                        'x_birthdate': child['birthdate'] or (related_partner.x_birthdate if related_partner else False)
                    })
            
            # 3. Parents
            parents_str = clean_val(row[17])
            if parents_str:
                # Parents logic can also be split if they use common formats, but for now we'll keep it simpler or use the same split
                parents = [p.strip() for p in re.split(r'[,;y]', parents_str) if p.strip()]
                for p_name in parents:
                    related_partner = smart_search_partner(p_name)
                    env['church.family.relation'].create({
                        'partner_id': partner.id,
                        'relation_type': 'padre' if 'martinez' in p_name.lower() or 'perez' in p_name.lower() else 'madre', # Just an example
                        'is_member': True if related_partner else False,
                        'related_partner_id': related_partner.id if related_partner else False,
                        'non_member_name': False if related_partner else p_name,
                        'x_birthdate': related_partner.x_birthdate if related_partner else False
                    })

            print(f"Processed {i+1}/{total}: {name}")
            env.cr.commit()
        except Exception as e:
            print(f"Error in row {i+2}: {str(e)}")
            print(f"Vals sought to be written: {partner_vals}")
            print(f"Row data: {row}")
            env.cr.rollback()

if __name__ == '__main__':
    import_data('/mnt/custom-addons/cdb_management/data/data-cdb.xlsx')
