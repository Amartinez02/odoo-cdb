/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";

/**
 * AttendanceListRenderer
 * Extends standard ListRenderer to provide automatic focus jumping 
 * to the next row when a status (radio) is selected.
 */
class AttendanceListRenderer extends ListRenderer {
    /**
     * @override
     */
    async onCellClicked(record, column, ev) {
        const result = await super.onCellClicked(...arguments);
        
        // If we clicked on the 'status' column (which has the radio widget)
        if (column.name === 'status') {
            // We use a small timeout to allow the browser and OWL to process the radio selection 
            // and potentially the record saving before jumping to the next row.
            setTimeout(() => {
                const records = this.props.list.records;
                const index = records.indexOf(record);
                
                if (index !== -1 && index < records.length - 1) {
                    const nextRecord = records[index + 1];
                    // Find the next row element in the DOM
                    const nextRow = this.rootRef.el.querySelector(`.o_data_row[data-id="${nextRecord.id}"]`);
                    if (nextRow) {
                        // Optional: Highlight or scroll to make it obvious
                        nextRow.scrollIntoView({ block: 'center', behavior: 'smooth' });
                        
                        // Focus the first cell of the next row to enable "editing" mode on it
                        const firstCell = nextRow.querySelector('.o_data_cell');
                        if (firstCell) {
                            firstCell.click();
                        }
                    }
                }
            }, 300); // 300ms is usually safe for Odoo's onchange/save cycle
        }
        return result;
    }
}

// Register the custom list view with the unique key 'cdb_attendance_list'
registry.category("views").add("cdb_attendance_list", {
    ...listView,
    Renderer: AttendanceListRenderer,
});
