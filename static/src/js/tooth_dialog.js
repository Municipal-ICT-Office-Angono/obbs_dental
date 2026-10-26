/** @odoo-module **/
import { Component } from "@odoo/owl";
import { getSurfaceInfo } from "./tooth_layout";

export class ToothDialog extends Component {
    static template = "obbs_dental.ToothDialog";

    static props = {
        toothNumber: { type: Number },
        surface: { type: String },
        condition: { type: String, optional: true },
        treatment: { type: String, optional: true },
        notes: { type: String, optional: true },
        conditionOptions: { type: Array },
        wholeTooth: { type: Boolean, optional: true },
        onClose: { type: Function },
        onSave: { type: Function },
        onConditionChange: { type: Function },
        onTreatmentChange: { type: Function },
        onNotesChange: { type: Function },
    };

    get surfaceInfo() {
        return getSurfaceInfo(this.props.toothNumber, this.props.surface) || {
            num: '',
            name: this.props.surface || '',
            label: this.props.surface || '',
        };
    }

    get surfaceLabel() {
        return this.surfaceInfo.label;
    }

    get surfaceName() {
        return this.surfaceInfo.name;
    }

    get surfaceNumber() {
        return this.surfaceInfo.num;
    }

    get selectedColor() {
        const opt = this.props.conditionOptions.find(
            o => o.code === this.props.condition
        );
        return opt ? opt.color : "#ccc";
    }
}