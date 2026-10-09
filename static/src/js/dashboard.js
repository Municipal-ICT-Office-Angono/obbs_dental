/** @odoo-module **/

import { Component, useState, useRef, useEffect, onWillUnmount, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { loadBundle } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";

class ObbsDashboard extends Component {
    static template = "obbs_dental.Dashboard";

    MONTHS = [
        [1, "January"], [2, "February"], [3, "March"], [4, "April"],
        [5, "May"], [6, "June"], [7, "July"], [8, "August"],
        [9, "September"], [10, "October"], [11, "November"], [12, "December"],
    ];
    QUARTERS = [
        [1, "Q1 (Jan-Mar)"], [2, "Q2 (Apr-Jun)"],
        [3, "Q3 (Jul-Sep)"], [4, "Q4 (Oct-Dec)"],
    ];

    setup() {
        this.action = useService("action");
        this.canvasRef = useRef("chart");
        this.chart = null;
        const now = new Date();
        this.state = useState({
            loading: true,
            error: false,
            year: String(now.getFullYear()),
            reportType: "monthly",
            month: String(now.getMonth() + 1),
            quarter: "1",
            municipality: "ANGONO",
            province: "Rizal",
            availableYears: [],
            data: null,
            openSection: null,
            drillKey: null,
        });
        onWillStart(async () => {
            try {
                await loadBundle("web.chartjs_lib");
            } catch (e) {}
            await this.loadData();
        });
        useEffect(
            () => {
                this.renderChart();
                return () => this.destroyChart();
            },
            () => [this.state.data]
        );
        onWillUnmount(() => this.destroyChart());
    }

    onRootClick(ev) {
        const t = ev.target;
        if (!t.closest) {
            return;
        }
        const openEl = t.closest("[data-open-patient]");
        if (openEl) {
            this.openPatient(Number(openEl.getAttribute("data-open-patient")));
            return;
        }
        const closeEl = t.closest("[data-close-drill]");
        if (closeEl) {
            this.closeDrill();
            return;
        }
        const sectionEl = t.closest("[data-section]");
        if (sectionEl) {
            this.toggleSection(sectionEl.getAttribute("data-section"));
            return;
        }
        const typeEl = t.closest("[data-report-type]");
        if (typeEl) {
            this.setReportType(typeEl.getAttribute("data-report-type"));
            return;
        }
        const refreshEl = t.closest("[data-refresh]");
        if (refreshEl) {
            this.loadData();
            return;
        }
        const drillEl = t.closest("[data-drill]");
        if (drillEl) {
            this.onDrill(drillEl.getAttribute("data-drill"));
            return;
        }
        if (t.closest("[data-chart-canvas]")) {
            this.onChartClick(ev);
        }
    }

    onFilterChange(ev) {
        const el = ev.target;
        const key = el.getAttribute("data-filter");
        if (!key) {
            return;
        }
        const val = el.value;
        if (key === "year") {
            this.state.year = val;
        } else if (key === "month") {
            this.state.month = val;
        } else if (key === "quarter") {
            this.state.quarter = val;
        } else if (key === "municipality") {
            this.state.municipality = val;
        } else if (key === "province") {
            this.state.province = val;
        }
        this.loadData();
    }

    onChartClick(ev) {
        if (!this.chart || !this.state.data) {
            return;
        }
        let points = [];
        try {
            points = this.chart.getElementsAtEventForMode(ev, "nearest", { intersect: true }, false);
            if (!points.length) {
                points = this.chart.getElementsAtEventForMode(ev, "index", { intersect: false }, false);
            }
        } catch (e) {}
        if (points.length) {
            this.onDrill(this.state.data.chart_groups[points[0].index].key);
        }
    }

    async loadData() {
        this.state.loading = true;
        this.state.error = false;
        const params = [
            `year=${encodeURIComponent(this.state.year)}`,
            `report_type=${encodeURIComponent(this.state.reportType)}`,
            `municipality=${encodeURIComponent(this.state.municipality)}`,
            `province=${encodeURIComponent(this.state.province)}`,
        ];
        if (this.state.reportType === "monthly") {
            params.push(`month=${encodeURIComponent(this.state.month)}`);
        }
        if (this.state.reportType === "quarterly") {
            params.push(`quarter=${encodeURIComponent(this.state.quarter)}`);
        }
        try {
            const resp = await fetch(`/obbs/dashboard/data?${params.join("&")}`);
            if (!resp.ok) {
                let msg = `Could not load dashboard data (HTTP ${resp.status}).`;
                try {
                    const body = await resp.json();
                    if (body && body.error) {
                        msg = body.error;
                    }
                } catch (e) {}
                this.state.error = msg;
            } else {
                const data = await resp.json();
                if (data && data.ok) {
                    this.state.data = data;
                    this.state.availableYears = data.available_years || [];
                    this.state.drillKey = null;
                } else {
                    this.state.error =
                        (data && data.error) || "Invalid dashboard response.";
                }
            }
        } catch (e) {
            this.state.error = "Network error while loading dashboard data.";
        }
        this.state.loading = false;
    }

    setReportType(type) {
        if (this.state.reportType !== type) {
            this.state.reportType = type;
            this.loadData();
        }
    }

    kpiCards() {
        if (!this.state.data) {
            return [];
        }
        const k = this.state.data.kpis;
        return [
            { label: "Patients Attended", value: k.attended, drillKey: "kpi:attended" },
            { label: "Male", value: k.male, drillKey: "kpi:male" },
            { label: "Female", value: k.female, drillKey: "kpi:female" },
            { label: "Pregnant Women", value: k.pregnant, drillKey: "kpi:pregnant" },
            { label: "With Dental Caries", value: k.with_caries, drillKey: "kpi:with_caries" },
            { label: "Procedures Performed", value: k.procedures, drillKey: "kpi:procedures" },
        ];
    }

    onDrill(key) {
        this.state.drillKey = this.state.drillKey === key ? null : key;
    }

    toggleSection(key) {
        this.state.openSection = this.state.openSection === key ? null : key;
    }

    isSelectedYear(y) {
        return this.state.year === String(y);
    }

    isSelectedMonth(m) {
        return this.state.month === String(m[0]);
    }

    isSelectedQuarter(q) {
        return this.state.quarter === String(q[0]);
    }

    closeDrill() {
        this.state.drillKey = null;
    }

    drillLabel() {
        if (!this.state.data) {
            return "";
        }
        if (this.state.drillKey && this.state.drillKey.startsWith("kpi:")) {
            const labels = {
                attended: "Patients Attended",
                male: "Male Patients",
                female: "Female Patients",
                pregnant: "Pregnant Women (10-49 y)",
                with_caries: "Patients with Dental Caries",
                procedures: "Patients Who Received Procedures",
            };
            return labels[this.state.drillKey.slice(4)] || "Patients";
        }
        const grp = this.state.data.groups.find((g) => g.key === this.state.drillKey);
        return grp ? grp.label : "";
    }

    drillPatients() {
        if (!this.state.data || !this.state.drillKey) {
            return [];
        }
        if (this.state.drillKey.startsWith("kpi:")) {
            const k = this.state.drillKey.slice(4);
            return this.state.data.patients_by_kpi[k] || [];
        }
        return this.state.data.patients_by_group[this.state.drillKey] || [];
    }

    sexLabel(sex) {
        if (sex === "male") {
            return "Male";
        }
        if (sex === "female") {
            return "Female";
        }
        return "Other";
    }

    openPatient(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "dental.patient",
            res_id: id,
            views: [[false, "form"]],
            viewMode: "form",
        });
    }

    async renderChart() {
        if (!window.Chart) {
            try {
                await loadBundle("web.chartjs_lib");
            } catch (e) {}
        }
        this.destroyChart();
        const canvas = this.canvasRef.el;
        const data = this.state.data;
        if (!canvas || !data || !window.Chart) {
            return;
        }
        this.chart = new window.Chart(canvas, {
            type: "bar",
            data: {
                labels: data.chart_groups.map((g) => g.label),
                datasets: [
                    {
                        label: "Male",
                        data: data.chart_groups.map((g) => g.m),
                        backgroundColor: "#1f6fb2",
                    },
                    {
                        label: "Female",
                        data: data.chart_groups.map((g) => g.f),
                        backgroundColor: "#e3648c",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top" },
                },
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } },
                },
            },
        });
    }

    destroyChart() {
        if (this.chart) {
            try {
                this.chart.destroy();
            } catch (e) {}
            this.chart = null;
        }
    }
}

registry.category("actions").add("obbs_dental_dashboard", ObbsDashboard);

export { ObbsDashboard };
