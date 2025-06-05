import {
  takeUntilDestroyed
} from "./chunk-6O2RD5TI.js";
import {
  DefaultValueAccessor,
  FormControl,
  FormControlDirective,
  FormsModule,
  NgControlStatus,
  NgControlStatusGroup,
  NgForm,
  ReactiveFormsModule,
  ɵNgNoValidate
} from "./chunk-BOQEVO5H.js";
import {
  TimeagoModule,
  TimeagoPipe
} from "./chunk-F6W3V265.js";
import {
  LoadIndicatorComponent
} from "./chunk-7SOVNULQ.js";
import {
  Component,
  DestroyRef,
  HttpClient,
  Injectable,
  NgForOf,
  NgIf,
  debounceTime,
  distinctUntilChanged,
  environment,
  inject,
  setClassMetadata,
  ɵsetClassDebugInfo,
  ɵɵadvance,
  ɵɵclassMapInterpolate1,
  ɵɵclassProp,
  ɵɵdefineComponent,
  ɵɵdefineInjectable,
  ɵɵelement,
  ɵɵelementContainer,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵgetCurrentView,
  ɵɵlistener,
  ɵɵnamespaceHTML,
  ɵɵnamespaceSVG,
  ɵɵnextContext,
  ɵɵpipe,
  ɵɵpipeBind1,
  ɵɵproperty,
  ɵɵpropertyInterpolate1,
  ɵɵreference,
  ɵɵresetView,
  ɵɵrestoreView,
  ɵɵtemplate,
  ɵɵtemplateRefExtractor,
  ɵɵtext,
  ɵɵtextInterpolate,
  ɵɵtextInterpolate1
} from "./chunk-FAGZ4ZSE.js";

// src/app/services/logs.service.ts
var LogsService = class _LogsService {
  constructor() {
    this.http = inject(HttpClient);
    this.logsUrl = environment.apiUrl + environment.logs;
    this.downloadLogs = () => this.http.get(this.logsUrl + "download", { responseType: "blob" });
    this.getLogs = () => this.http.get(this.logsUrl);
  }
  static {
    this.\u0275fac = function LogsService_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _LogsService)();
    };
  }
  static {
    this.\u0275prov = /* @__PURE__ */ \u0275\u0275defineInjectable({ token: _LogsService, factory: _LogsService.\u0275fac, providedIn: "root" });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(LogsService, [{
    type: Injectable,
    args: [{ providedIn: "root" }]
  }], null, null);
})();

// src/app/logs/logs.component.ts
function LogsComponent_app_load_indicator_3_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 9);
  }
}
function LogsComponent_ng_template_4_div_10_ng_container_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function LogsComponent_ng_template_4_div_10_ng_container_6_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function LogsComponent_ng_template_4_div_10_ng_container_7_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function LogsComponent_ng_template_4_div_10_ng_container_8_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function LogsComponent_ng_template_4_div_10_ng_container_9_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function LogsComponent_ng_template_4_div_10_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 20)(1, "details")(2, "summary")(3, "p", 21)(4, "i", 22);
    \u0275\u0275template(5, LogsComponent_ng_template_4_div_10_ng_container_5_Template, 1, 0, "ng-container", 23)(6, LogsComponent_ng_template_4_div_10_ng_container_6_Template, 1, 0, "ng-container", 23)(7, LogsComponent_ng_template_4_div_10_ng_container_7_Template, 1, 0, "ng-container", 23)(8, LogsComponent_ng_template_4_div_10_ng_container_8_Template, 1, 0, "ng-container", 23)(9, LogsComponent_ng_template_4_div_10_ng_container_9_Template, 1, 0, "ng-container", 23);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(10, "strong");
    \u0275\u0275text(11);
    \u0275\u0275elementEnd();
    \u0275\u0275text(12);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(13, "small", 24);
    \u0275\u0275text(14);
    \u0275\u0275pipe(15, "timeago");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(16, "p", 25);
    \u0275\u0275text(17);
    \u0275\u0275elementEnd()()();
  }
  if (rf & 2) {
    const log_r3 = ctx.$implicit;
    \u0275\u0275nextContext(2);
    const debugLog_r4 = \u0275\u0275reference(7);
    const infoLog_r5 = \u0275\u0275reference(9);
    const warningLog_r6 = \u0275\u0275reference(11);
    const errorLog_r7 = \u0275\u0275reference(13);
    const otherLog_r8 = \u0275\u0275reference(15);
    \u0275\u0275advance(3);
    \u0275\u0275classMapInterpolate1("logs-text ", log_r3.level.toLowerCase(), "");
    \u0275\u0275propertyInterpolate1("title", "", log_r3.level.toLowerCase(), " log");
    \u0275\u0275advance(2);
    \u0275\u0275property("ngIf", log_r3.level == "DEBUG")("ngIfThen", debugLog_r4);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", log_r3.level == "INFO")("ngIfThen", infoLog_r5);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", log_r3.level == "WARNING")("ngIfThen", warningLog_r6);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", log_r3.level == "ERROR")("ngIfThen", errorLog_r7);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", log_r3.level == "OTHER")("ngIfThen", otherLog_r8);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1("", log_r3.module, ": ");
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1("", log_r3.message, " ");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(\u0275\u0275pipeBind1(15, 19, log_r3.datetime));
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate(log_r3.raw_log);
  }
}
function LogsComponent_ng_template_4_Template(rf, ctx) {
  if (rf & 1) {
    const _r1 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 10)(1, "i", 11);
    \u0275\u0275listener("click", function LogsComponent_ng_template_4_Template_i_click_1_listener() {
      \u0275\u0275restoreView(_r1);
      const ctx_r1 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r1.getLogs());
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(2, "svg", 12);
    \u0275\u0275element(3, "path", 13);
    \u0275\u0275elementEnd()();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(4, "form", 14);
    \u0275\u0275element(5, "input", 15);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(6, "a", 16);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(7, "svg", 12);
    \u0275\u0275element(8, "path", 17);
    \u0275\u0275elementEnd()()();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(9, "div", 18);
    \u0275\u0275template(10, LogsComponent_ng_template_4_div_10_Template, 18, 21, "div", 19);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext();
    \u0275\u0275advance();
    \u0275\u0275classProp("loading", ctx_r1.isUpdating);
    \u0275\u0275advance(4);
    \u0275\u0275property("formControl", ctx_r1.searchForm);
    \u0275\u0275advance(5);
    \u0275\u0275property("ngForOf", ctx_r1.filtered_logs);
  }
}
function LogsComponent_ng_template_6_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 26);
    \u0275\u0275element(1, "path", 27);
    \u0275\u0275elementEnd();
  }
}
function LogsComponent_ng_template_8_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 26);
    \u0275\u0275element(1, "path", 28);
    \u0275\u0275elementEnd();
  }
}
function LogsComponent_ng_template_10_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 26);
    \u0275\u0275element(1, "path", 29);
    \u0275\u0275elementEnd();
  }
}
function LogsComponent_ng_template_12_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 26);
    \u0275\u0275element(1, "path", 30);
    \u0275\u0275elementEnd();
  }
}
function LogsComponent_ng_template_14_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 26);
    \u0275\u0275element(1, "path", 31);
    \u0275\u0275elementEnd();
  }
}
var LogsComponent = class _LogsComponent {
  constructor() {
    this.destroyRef = inject(DestroyRef);
    this.logsService = inject(LogsService);
    this.title = "Logs";
    this.isLoading = true;
    this.isUpdating = false;
    this.all_logs = [];
    this.searchQuery = "";
    this.searchForm = new FormControl();
    this.filtered_logs = [];
  }
  ngOnInit() {
    this.searchForm.valueChanges.pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((value) => {
      this.onSearch(value);
    });
    this.isLoading = true;
    this.getLogs();
  }
  getLogs() {
    this.isUpdating = true;
    this.logsService.getLogs().subscribe((logs) => {
      this.all_logs = logs;
      this.filtered_logs = logs;
      this.isLoading = false;
      this.isUpdating = false;
    });
  }
  // downloadLogs(): void {
  //   // this.isUpdating = true;
  //   this.logsService.downloadLogs().subscribe((data: Blob) => {
  //     const url = window.URL.createObjectURL(data);
  //     const a = document.createElement('a');
  //     a.href = url;
  //     a.click();
  //     window.URL.revokeObjectURL(url);
  //     // this.isUpdating = false;
  //     // return data;
  //   });
  // }
  onSearch(query = "") {
    if (query.length < 3) {
      this.filtered_logs = this.all_logs;
      return;
    }
    if (query.trim() === this.searchQuery) {
      return;
    }
    this.searchQuery = query;
    this.filtered_logs = this.all_logs.filter((log) => {
      return log.raw_log.toLowerCase().includes(this.searchQuery.toLowerCase());
    });
  }
  static {
    this.\u0275fac = function LogsComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _LogsComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _LogsComponent, selectors: [["app-logs"]], decls: 16, vars: 3, consts: [["logsLoaded", ""], ["debugLog", ""], ["infoLog", ""], ["warningLog", ""], ["errorLog", ""], ["otherLog", ""], [1, "logs-container"], [1, "logs-title", "text-center"], ["class", "center", 4, "ngIf", "ngIfElse"], [1, "center"], [1, "logssearch"], ["title", "Refresh", 1, "icononly-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", 1, "refresh-icon"], ["d", "M343-107q-120-42-194.5-146.5T74-490q0-29 4-57.5T91-604l-57 33-37-62 185-107 106 184-63 36-54-92q-13 30-18.5 60.5T147-490q0 113 65.5 200T381-171l-38 64Zm291-516v-73h107q-47-60-115.5-93.5T480-823q-66 0-123.5 24T255-734l-38-65q54-45 121-71t142-26q85 0 160.5 33T774-769v-67h73v213H634ZM598-1 413-107l107-184 62 37-54 94q123-17 204.5-110.5T814-489q0-19-2.5-37.5T805-563h74q4 18 6 36.5t2 36.5q0 142-87 251.5T578-96l56 33-36 62Z"], ["id", "searchForm", 1, "logssearch-form"], ["type", "text", "autocomplete", "off", "name", "query", "placeholder", "Filter logs...", "aria-label", "filter logs", 3, "formControl"], ["title", "Download Logs", "href", "/api/v1/logs/download", "download", "", 1, "icononly-button"], ["d", "M480-313 287-506l43-43 120 120v-371h60v371l120-120 43 43-193 193ZM220-160q-24 0-42-18t-18-42v-143h60v143h520v-143h60v143q0 24-18 42t-42 18H220Z"], [1, "logs-table"], ["class", "logs-row", 4, "ngFor", "ngForOf"], [1, "logs-row"], [3, "title"], [1, "logs-icon"], [4, "ngIf", "ngIfThen"], [1, "logs-dt"], [1, "logs-raw"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M320-242 80-482l242-242 43 43-199 199 197 197-43 43Zm318 2-43-43 199-199-197-197 43-43 240 240-242 242Z"], ["d", "M453-280h60v-240h-60v240Zm26.98-314q14.02 0 23.52-9.2T513-626q0-14.45-9.48-24.22-9.48-9.78-23.5-9.78t-23.52 9.78Q447-640.45 447-626q0 13.6 9.48 22.8 9.48 9.2 23.5 9.2Zm.29 514q-82.74 0-155.5-31.5Q252-143 197.5-197.5t-86-127.34Q80-397.68 80-480.5t31.5-155.66Q143-709 197.5-763t127.34-85.5Q397.68-880 480.5-880t155.66 31.5Q709-817 763-763t85.5 127Q880-563 880-480.27q0 82.74-31.5 155.5Q817-252 763-197.68q-54 54.31-127 86Q563-80 480.27-80Zm.23-60Q622-140 721-239.5t99-241Q820-622 721.19-721T480-820q-141 0-240.5 98.81T140-480q0 141 99.5 240.5t241 99.5Zm-.5-340Z"], ["d", "m40-120 440-760 440 760H40Zm104-60h672L480-760 144-180Zm340.18-57q12.82 0 21.32-8.68 8.5-8.67 8.5-21.5 0-12.82-8.68-21.32-8.67-8.5-21.5-8.5-12.82 0-21.32 8.68-8.5 8.67-8.5 21.5 0 12.82 8.68 21.32 8.67 8.5 21.5 8.5ZM454-348h60v-224h-60v224Zm26-122Z"], ["d", "M479.91-120q-28.91 0-49.41-20.59-20.5-20.59-20.5-49.5t20.59-49.41q20.59-20.5 49.5-20.5t49.41 20.59q20.5 20.59 20.5 49.5t-20.59 49.41q-20.59 20.5-49.5 20.5ZM410-360v-480h140v480H410Z"], ["d", "M477.03-246Q493-246 504-257.03q11-11.03 11-27T503.97-311q-11.03-11-27-11T450-310.97q-11 11.03-11 27T450.03-257q11.03 11 27 11ZM444-394h57q0-31 10-50.5t34.72-44.22Q579-522 592-547.5t13-53.5q0-53-34-84t-91.52-31q-51.87 0-88.17 24.5Q355-667 338-624l53 22q14-28 36.2-42.5Q449.4-659 479-659q32 0 50.5 16t18.5 44.1q0 19.9-11 38.4T500-517q-37 35-46.5 60t-9.5 63ZM180-120q-24 0-42-18t-18-42v-600q0-24 18-42t42-18h600q24 0 42 18t18 42v600q0 24-18 42t-42 18H180Zm0-60h600v-600H180v600Zm0-600v600-600Z"]], template: function LogsComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "div", 6)(1, "h1", 7);
        \u0275\u0275text(2);
        \u0275\u0275elementEnd();
        \u0275\u0275template(3, LogsComponent_app_load_indicator_3_Template, 1, 0, "app-load-indicator", 8)(4, LogsComponent_ng_template_4_Template, 11, 4, "ng-template", null, 0, \u0275\u0275templateRefExtractor);
        \u0275\u0275elementEnd();
        \u0275\u0275template(6, LogsComponent_ng_template_6_Template, 2, 0, "ng-template", null, 1, \u0275\u0275templateRefExtractor)(8, LogsComponent_ng_template_8_Template, 2, 0, "ng-template", null, 2, \u0275\u0275templateRefExtractor)(10, LogsComponent_ng_template_10_Template, 2, 0, "ng-template", null, 3, \u0275\u0275templateRefExtractor)(12, LogsComponent_ng_template_12_Template, 2, 0, "ng-template", null, 4, \u0275\u0275templateRefExtractor)(14, LogsComponent_ng_template_14_Template, 2, 0, "ng-template", null, 5, \u0275\u0275templateRefExtractor);
      }
      if (rf & 2) {
        const logsLoaded_r9 = \u0275\u0275reference(5);
        \u0275\u0275advance(2);
        \u0275\u0275textInterpolate(ctx.title);
        \u0275\u0275advance();
        \u0275\u0275property("ngIf", ctx.isLoading)("ngIfElse", logsLoaded_r9);
      }
    }, dependencies: [NgIf, NgForOf, FormsModule, \u0275NgNoValidate, DefaultValueAccessor, NgControlStatus, NgControlStatusGroup, NgForm, LoadIndicatorComponent, ReactiveFormsModule, FormControlDirective, TimeagoModule, TimeagoPipe], styles: ["\n\n.logs-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n}\n.logs-title[_ngcontent-%COMP%] {\n  position: sticky;\n  top: 76px;\n  margin: 0;\n  padding: 1rem;\n  background-color: var(--color-surface-container-high);\n  z-index: 2;\n}\n@media (width < 765px) {\n  .logs-title[_ngcontent-%COMP%] {\n    top: 62px;\n  }\n}\n.text-center[_ngcontent-%COMP%] {\n  text-align: center;\n}\n.center[_ngcontent-%COMP%] {\n  margin: auto;\n}\n.logssearch[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  justify-content: center;\n  width: auto;\n  flex-grow: 1;\n  padding: 1rem;\n  background-color: var(--color-surface-container-high);\n  position: sticky;\n  top: 145px;\n  z-index: 2;\n  gap: 0.5rem;\n}\n@media (width < 765px) {\n  .logssearch[_ngcontent-%COMP%] {\n    padding: 0.5rem;\n    top: 113px;\n  }\n}\n.refresh-icon[_ngcontent-%COMP%] {\n  cursor: pointer;\n  fill: var(--color-on-surface);\n}\n.loading[_ngcontent-%COMP%] {\n  cursor: progress;\n  animation: spin-animation 2s linear infinite;\n}\n.logssearch-form[_ngcontent-%COMP%] {\n  width: 100%;\n}\n.logssearch-form[_ngcontent-%COMP%]   input[_ngcontent-%COMP%] {\n  width: 100%;\n  padding: 0.5rem;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  margin: 0;\n  font-size: 1rem;\n  background-color: var(--color-surface-container-highest);\n  color: var(--color-on-surface);\n}\n.logssearch-form[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]:focus {\n  outline: var(--color-primary);\n  border: 1px solid var(--color-primary);\n}\n.logs-table[_ngcontent-%COMP%] {\n  padding: 1rem;\n}\n.logs-row[_ngcontent-%COMP%] {\n  padding: 10px;\n  border-bottom: 1px solid #e0e0e0;\n}\n@media (width < 765px) {\n  .logs-row[_ngcontent-%COMP%] {\n    padding: 0;\n  }\n}\n.logs-row[_ngcontent-%COMP%]   details[_ngcontent-%COMP%] {\n  width: 100%;\n  list-style-position: outside;\n}\n.logs-row[_ngcontent-%COMP%]   summary[_ngcontent-%COMP%] {\n  list-style-position: outside;\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  flex-wrap: wrap;\n  gap: 1rem;\n  cursor: pointer;\n  position: relative;\n}\n@media (width < 765px) {\n  .logs-row[_ngcontent-%COMP%]   summary[_ngcontent-%COMP%] {\n    flex-direction: column;\n    align-items: baseline;\n    gap: 0;\n    margin-bottom: 1rem;\n  }\n}\nsummary[_ngcontent-%COMP%]   .logs-text[_ngcontent-%COMP%] {\n  flex: 1;\n  margin-left: 2rem;\n}\n.logs-icon[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 0.75rem;\n  left: 0;\n  font-size: 0;\n  z-index: 0;\n}\n.logs-icon[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  width: 1.5rem;\n  fill: var(--color-outline);\n}\nsummary[_ngcontent-%COMP%]   .debug[_ngcontent-%COMP%] {\n  color: var(--color-info);\n}\nsummary[_ngcontent-%COMP%]   .debug[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  fill: var(--color-info);\n}\nsummary[_ngcontent-%COMP%]   .warning[_ngcontent-%COMP%] {\n  color: var(--color-danger);\n}\nsummary[_ngcontent-%COMP%]   .warning[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  fill: var(--color-danger);\n}\nsummary[_ngcontent-%COMP%]   .error[_ngcontent-%COMP%] {\n  color: var(--color-warning);\n}\nsummary[_ngcontent-%COMP%]   .error[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  fill: var(--color-warning);\n}\n/*# sourceMappingURL=logs.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(LogsComponent, [{
    type: Component,
    args: [{ selector: "app-logs", imports: [NgIf, NgForOf, FormsModule, LoadIndicatorComponent, ReactiveFormsModule, TimeagoModule], template: `<div class="logs-container">
  <h1 class="logs-title text-center">{{ title }}</h1>
  <app-load-indicator *ngIf="isLoading; else logsLoaded" class="center" />
  <ng-template #logsLoaded>
    <div class="logssearch">
      <i class="icononly-button" [class.loading]="isUpdating" title="Refresh" (click)="getLogs()">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="refresh-icon">
          <path
            d="M343-107q-120-42-194.5-146.5T74-490q0-29 4-57.5T91-604l-57 33-37-62 185-107 106 184-63 36-54-92q-13 30-18.5 60.5T147-490q0 113 65.5 200T381-171l-38 64Zm291-516v-73h107q-47-60-115.5-93.5T480-823q-66 0-123.5 24T255-734l-38-65q54-45 121-71t142-26q85 0 160.5 33T774-769v-67h73v213H634ZM598-1 413-107l107-184 62 37-54 94q123-17 204.5-110.5T814-489q0-19-2.5-37.5T805-563h74q4 18 6 36.5t2 36.5q0 142-87 251.5T578-96l56 33-36 62Z"
          />
        </svg>
      </i>
      <form id="searchForm" class="logssearch-form">
        <input
          type="text"
          autocomplete="off"
          [formControl]="searchForm"
          name="query"
          placeholder="Filter logs..."
          aria-label="filter logs"
        />
      </form>
      <a class="icononly-button" title="Download Logs" href="/api/v1/logs/download" download>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="refresh-icon">
          <path
            d="M480-313 287-506l43-43 120 120v-371h60v371l120-120 43 43-193 193ZM220-160q-24 0-42-18t-18-42v-143h60v143h520v-143h60v143q0 24-18 42t-42 18H220Z"
          />
        </svg>
      </a>
    </div>
    <div class="logs-table">
      <div *ngFor="let log of filtered_logs" class="logs-row">
        <details>
          <summary>
            <p class="logs-text {{ log.level.toLowerCase() }}" title="{{ log.level.toLowerCase() }} log">
              <i class="logs-icon">
                <ng-container *ngIf="log.level == 'DEBUG'; then debugLog"></ng-container>
                <ng-container *ngIf="log.level == 'INFO'; then infoLog"></ng-container>
                <ng-container *ngIf="log.level == 'WARNING'; then warningLog"></ng-container>
                <ng-container *ngIf="log.level == 'ERROR'; then errorLog"></ng-container>
                <ng-container *ngIf="log.level == 'OTHER'; then otherLog"></ng-container>
              </i>
              <strong>{{ log.module }}: </strong>{{ log.message }}
            </p>
            <small class="logs-dt">{{ log.datetime | timeago }}</small>
          </summary>
          <!-- <em class="logs-type">{{ log.level}} | {{ log.filename }}:{{ log.lineno }} </em> -->
          <p class="logs-raw">{{ log.raw_log }}</p>
        </details>
      </div>
    </div>
  </ng-template>
</div>

<ng-template #debugLog>
  <!-- Google Fonts Icon: code no-fill -->
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
    <path d="M320-242 80-482l242-242 43 43-199 199 197 197-43 43Zm318 2-43-43 199-199-197-197 43-43 240 240-242 242Z" />
  </svg>
</ng-template>
<ng-template #infoLog>
  <!-- Google Fonts Icon: info no-fill -->
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
    <path
      d="M453-280h60v-240h-60v240Zm26.98-314q14.02 0 23.52-9.2T513-626q0-14.45-9.48-24.22-9.48-9.78-23.5-9.78t-23.52 9.78Q447-640.45 447-626q0 13.6 9.48 22.8 9.48 9.2 23.5 9.2Zm.29 514q-82.74 0-155.5-31.5Q252-143 197.5-197.5t-86-127.34Q80-397.68 80-480.5t31.5-155.66Q143-709 197.5-763t127.34-85.5Q397.68-880 480.5-880t155.66 31.5Q709-817 763-763t85.5 127Q880-563 880-480.27q0 82.74-31.5 155.5Q817-252 763-197.68q-54 54.31-127 86Q563-80 480.27-80Zm.23-60Q622-140 721-239.5t99-241Q820-622 721.19-721T480-820q-141 0-240.5 98.81T140-480q0 141 99.5 240.5t241 99.5Zm-.5-340Z"
    />
  </svg>
</ng-template>
<ng-template #warningLog>
  <!-- Google Fonts Icon: warning no-fill -->
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
    <path
      d="m40-120 440-760 440 760H40Zm104-60h672L480-760 144-180Zm340.18-57q12.82 0 21.32-8.68 8.5-8.67 8.5-21.5 0-12.82-8.68-21.32-8.67-8.5-21.5-8.5-12.82 0-21.32 8.68-8.5 8.67-8.5 21.5 0 12.82 8.68 21.32 8.67 8.5 21.5 8.5ZM454-348h60v-224h-60v224Zm26-122Z"
    />
  </svg>
</ng-template>
<ng-template #errorLog>
  <!-- Google Fonts Icon: priority high no-fill -->
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
    <path
      d="M479.91-120q-28.91 0-49.41-20.59-20.5-20.59-20.5-49.5t20.59-49.41q20.59-20.5 49.5-20.5t49.41 20.59q20.5 20.59 20.5 49.5t-20.59 49.41q-20.59 20.5-49.5 20.5ZM410-360v-480h140v480H410Z"
    />
  </svg>
</ng-template>
<ng-template #otherLog>
  <!-- Google Fonts Icon: help center no-fill -->
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
    <path
      d="M477.03-246Q493-246 504-257.03q11-11.03 11-27T503.97-311q-11.03-11-27-11T450-310.97q-11 11.03-11 27T450.03-257q11.03 11 27 11ZM444-394h57q0-31 10-50.5t34.72-44.22Q579-522 592-547.5t13-53.5q0-53-34-84t-91.52-31q-51.87 0-88.17 24.5Q355-667 338-624l53 22q14-28 36.2-42.5Q449.4-659 479-659q32 0 50.5 16t18.5 44.1q0 19.9-11 38.4T500-517q-37 35-46.5 60t-9.5 63ZM180-120q-24 0-42-18t-18-42v-600q0-24 18-42t42-18h600q24 0 42 18t18 42v600q0 24-18 42t-42 18H180Zm0-60h600v-600H180v600Zm0-600v600-600Z"
    />
  </svg>
</ng-template>
`, styles: ["/* src/app/logs/logs.component.scss */\n.logs-container {\n  display: flex;\n  flex-direction: column;\n}\n.logs-title {\n  position: sticky;\n  top: 76px;\n  margin: 0;\n  padding: 1rem;\n  background-color: var(--color-surface-container-high);\n  z-index: 2;\n}\n@media (width < 765px) {\n  .logs-title {\n    top: 62px;\n  }\n}\n.text-center {\n  text-align: center;\n}\n.center {\n  margin: auto;\n}\n.logssearch {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  justify-content: center;\n  width: auto;\n  flex-grow: 1;\n  padding: 1rem;\n  background-color: var(--color-surface-container-high);\n  position: sticky;\n  top: 145px;\n  z-index: 2;\n  gap: 0.5rem;\n}\n@media (width < 765px) {\n  .logssearch {\n    padding: 0.5rem;\n    top: 113px;\n  }\n}\n.refresh-icon {\n  cursor: pointer;\n  fill: var(--color-on-surface);\n}\n.loading {\n  cursor: progress;\n  animation: spin-animation 2s linear infinite;\n}\n.logssearch-form {\n  width: 100%;\n}\n.logssearch-form input {\n  width: 100%;\n  padding: 0.5rem;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  margin: 0;\n  font-size: 1rem;\n  background-color: var(--color-surface-container-highest);\n  color: var(--color-on-surface);\n}\n.logssearch-form input:focus {\n  outline: var(--color-primary);\n  border: 1px solid var(--color-primary);\n}\n.logs-table {\n  padding: 1rem;\n}\n.logs-row {\n  padding: 10px;\n  border-bottom: 1px solid #e0e0e0;\n}\n@media (width < 765px) {\n  .logs-row {\n    padding: 0;\n  }\n}\n.logs-row details {\n  width: 100%;\n  list-style-position: outside;\n}\n.logs-row summary {\n  list-style-position: outside;\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  flex-wrap: wrap;\n  gap: 1rem;\n  cursor: pointer;\n  position: relative;\n}\n@media (width < 765px) {\n  .logs-row summary {\n    flex-direction: column;\n    align-items: baseline;\n    gap: 0;\n    margin-bottom: 1rem;\n  }\n}\nsummary .logs-text {\n  flex: 1;\n  margin-left: 2rem;\n}\n.logs-icon {\n  position: absolute;\n  top: 0.75rem;\n  left: 0;\n  font-size: 0;\n  z-index: 0;\n}\n.logs-icon svg {\n  width: 1.5rem;\n  fill: var(--color-outline);\n}\nsummary .debug {\n  color: var(--color-info);\n}\nsummary .debug svg {\n  fill: var(--color-info);\n}\nsummary .warning {\n  color: var(--color-danger);\n}\nsummary .warning svg {\n  fill: var(--color-danger);\n}\nsummary .error {\n  color: var(--color-warning);\n}\nsummary .error svg {\n  fill: var(--color-warning);\n}\n/*# sourceMappingURL=logs.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(LogsComponent, { className: "LogsComponent", filePath: "src/app/logs/logs.component.ts", lineNumber: 17 });
})();

// src/app/logs/routes.ts
var routes_default = [{ path: "", loadComponent: () => LogsComponent }];
export {
  routes_default as default
};
//# sourceMappingURL=chunk-X3CULKR6.js.map
