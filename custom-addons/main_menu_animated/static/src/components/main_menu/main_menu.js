import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { WidgetHour } from "@main_menu_animated/components/widget_hour/widget_hour";
import { WidgetAnnouncement } from "@main_menu_animated/components/widget_announcement/widget_announcement";
import { user } from "@web/core/user";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

class MenuAction extends Component {
    static components = { WidgetHour, WidgetAnnouncement };
    static props = {...standardActionServiceProps};
    static template = "main_menu_animated.MainMenu";

    setup() {
        this.orm = useService("orm");
        this.menuService = useService("menu");
        // const companyService = useService("company");
        // this.currentCompanyId = companyService.currentCompany.id
        // In client actions, the company service may not be available in Odoo 19.
        // Use the user service to get the current company instead.
        this.currentCompanyId = user.companyId;
        
        let apps = this.menuService.getApps()
                        .filter(app => app.xmlid != "main_menu_animated.main_menu_root")
                        .sort((a, b) => a.name.localeCompare(b.name));

        const savedOrderStr = window.localStorage.getItem(`main_menu_order_${user.userId}`);
        if (savedOrderStr) {
            try {
                const savedOrder = JSON.parse(savedOrderStr);
                apps.sort((a, b) => {
                    let indexA = savedOrder.indexOf(a.id);
                    let indexB = savedOrder.indexOf(b.id);
                    if (indexA === -1) indexA = 9999;
                    if (indexB === -1) indexB = 9999;
                    return indexA - indexB;
                });
            } catch (e) {}
        }
        
        this.state = useState({ apps: apps });
        this.draggedApp = null;
        
        this.deg = `${90 + 180 * Math.atan(window.innerHeight / window.innerWidth) / Math.PI}deg`;

        onWillStart(async () => {
            try {
                this.userIsAdmin = await user.hasGroup("base.group_system");
                const res = await this.orm.searchRead(
                    "res.company",
                    [["id", "=", this.currentCompanyId]],
                    ["announcement", "show_widgets"]
                );
                const rec = Array.isArray(res) && res.length ? res[0] : null;
                this.announcement = rec?.announcement || "";
                this.showWidgets = !!(rec?.show_widgets);
            } catch (error) {
                console.error("Error loading data:", error);
            }
        });
    }

    onClickModule(menu){
        menu && this.menuService.selectMenu(menu);
    }

    onDragStart(ev, app) {
        this.draggedApp = app;
        ev.currentTarget.classList.add("dragging");
        // Required for Firefox
        if (ev.dataTransfer) {
            ev.dataTransfer.effectAllowed = "move";
            ev.dataTransfer.setData("text/plain", app.id);
        }
    }

    onDragOver(ev) {
        ev.preventDefault();
        if (ev.dataTransfer) {
            ev.dataTransfer.dropEffect = "move";
        }
    }

    onDrop(ev, targetApp) {
        ev.preventDefault();
        if (this.draggedApp && this.draggedApp.id !== targetApp.id) {
            const draggedIndex = this.state.apps.findIndex(a => a.id === this.draggedApp.id);
            const targetIndex = this.state.apps.findIndex(a => a.id === targetApp.id);
            
            if (draggedIndex > -1 && targetIndex > -1) {
                // Reorder array
                this.state.apps.splice(draggedIndex, 1);
                this.state.apps.splice(targetIndex, 0, this.draggedApp);
                
                // Save to localStorage
                const newOrder = this.state.apps.map(a => a.id);
                window.localStorage.setItem(`main_menu_order_${user.userId}`, JSON.stringify(newOrder));
            }
        }
    }

    onDragEnd(ev) {
        ev.currentTarget.classList.remove("dragging");
        this.draggedApp = null;
    }

    onChangeAnnouncement(value){
        this.announcement = value;
    }

    async onSaveAnnouncement(){
        try {
            await this.orm.write("res.company", [this.currentCompanyId], {
                "announcement": this.announcement
            });
        } catch (error) {
            console.error("Error saving data:", error);
        }
    }
}

registry
    .category("actions")
    .add("main_menu_animated.action_open_main_menu", MenuAction);
