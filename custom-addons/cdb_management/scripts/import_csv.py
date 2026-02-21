import csv
import os

def import_csv(filepath):
    print(f"Starting import from {filepath}...")
    
    with open(filepath, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        count = 0
        for row in reader:
            first_name = row.get('Nombres', '').strip()
            last_name = row.get('Apellidos', '').strip()
            
            if not first_name and not last_name:
                continue
            
            # If one is missing, use a placeholder to avoid ValidationError
            if first_name and not last_name:
                last_name = "."
            elif last_name and not first_name:
                first_name = "."
                
            full_name = f"{first_name} {last_name}".strip()
            
            # Search for existing partner
            partner = env['res.partner'].search([('name', '=', full_name)], limit=1)
            
            vals = {
                'name': full_name,
                'x_first_name': first_name,
                'x_last_name': last_name,
                'x_is_church_member': True,
                'active': True,
                'company_type': 'person',
            }
            
            try:
                if partner:
                    partner.write(vals)
                    print(f"Updated: {full_name}")
                else:
                    env['res.partner'].create(vals)
                    print(f"Created: {full_name}")
                
                count += 1
                if count % 10 == 0:
                    env.cr.commit()
            except Exception as e:
                print(f"Error importing {full_name}: {e}")
                env.cr.rollback()
        
        env.cr.commit()
        print(f"Import finished. Processed {count} records.")

if __name__ == '__main__':
    # This script is intended to be run within an Odoo context (e.g., odoo shell)
    # where 'env' is already defined.
    filepath = '/mnt/custom-addons/cdb_management/data/MIEMBROS CDB - MIEMBROS.csv'
    if os.path.exists(filepath):
        import_csv(filepath)
    else:
        # Local path for debugging/reference
        import_csv('/Users/anthonymartinez/Documents/CASA DE BENDICION/odoo-cdb/custom-addons/cdb_management/data/MIEMBROS CDB - MIEMBROS.csv')
