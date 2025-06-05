import {
  MediaService
} from "./chunk-3ILQGILQ.js";
import {
  takeUntilDestroyed
} from "./chunk-6O2RD5TI.js";
import {
  RouteHome,
  RouteLogs,
  RouteMedia,
  RouteMovies,
  RouteParamMediaId,
  RouteSeries,
  RouteSettings,
  RouteTasks
} from "./chunk-6WR6ESSR.js";
import {
  msMinute
} from "./chunk-GF5DKDDQ.js";
import {
  ApiModule,
  PreloadAllModules,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
  bootstrapApplication,
  provideRouter,
  withComponentInputBinding,
  withInMemoryScrolling,
  withPreloading,
  withViewTransitions
} from "./chunk-U5GO6X62.js";
import {
  WebsocketService
} from "./chunk-KIVIDEQ5.js";
import {
  CheckboxControlValueAccessor,
  DefaultValueAccessor,
  FormControl,
  FormControlDirective,
  FormsModule,
  NgControlStatus,
  NgControlStatusGroup,
  NgForm,
  NgModel,
  ReactiveFormsModule,
  ɵNgNoValidate
} from "./chunk-BOQEVO5H.js";
import {
  TimeagoModule
} from "./chunk-F6W3V265.js";
import {
  ChangeDetectionStrategy,
  Component,
  DATE_PIPE_DEFAULT_OPTIONS,
  DestroyRef,
  ElementRef,
  HostListener,
  NgClass,
  NgForOf,
  NgIf,
  Renderer2,
  ViewChild,
  debounceTime,
  distinctUntilChanged,
  importProvidersFrom,
  inject,
  provideHttpClient,
  setClassMetadata,
  ɵsetClassDebugInfo,
  ɵɵadvance,
  ɵɵclassProp,
  ɵɵdefineComponent,
  ɵɵelement,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵgetCurrentView,
  ɵɵlistener,
  ɵɵloadQuery,
  ɵɵnamespaceHTML,
  ɵɵnamespaceSVG,
  ɵɵnextContext,
  ɵɵproperty,
  ɵɵpropertyInterpolate,
  ɵɵpureFunction1,
  ɵɵqueryRefresh,
  ɵɵresetView,
  ɵɵresolveDocument,
  ɵɵrestoreView,
  ɵɵsanitizeUrl,
  ɵɵtemplate,
  ɵɵtext,
  ɵɵtextInterpolate,
  ɵɵtwoWayBindingSet,
  ɵɵtwoWayListener,
  ɵɵtwoWayProperty,
  ɵɵviewQuery
} from "./chunk-FAGZ4ZSE.js";

// src/app/nav/sidenav/sidenav.component.ts
var SidenavComponent = class _SidenavComponent {
  constructor() {
    this.RouteHome = RouteHome;
    this.RouteLogs = RouteLogs;
    this.RouteMovies = RouteMovies;
    this.RouteSeries = RouteSeries;
    this.RouteSettings = RouteSettings;
    this.RouteTasks = RouteTasks;
  }
  static {
    this.\u0275fac = function SidenavComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _SidenavComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _SidenavComponent, selectors: [["app-sidenav"]], decls: 31, vars: 6, consts: [[1, "navmenu"], ["routerLinkActive", "active", 1, "sidenav-button", 3, "routerLink"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", 1, "icon"], ["d", "M240-200h120v-240h240v240h120v-360L480-740 240-560v360Zm-80 80v-480l320-240 320 240v480H520v-240h-80v240H160Zm320-350Z"], [1, "btntext"], ["d", "m160-800 80 160h120l-80-160h80l80 160h120l-80-160h80l80 160h120l-80-160h120q33 0 56.5 23.5T880-720v480q0 33-23.5 56.5T800-160H160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800Zm0 240v320h640v-320H160Zm0 0v320-320Z"], ["d", "M320-120v-80H160q-33 0-56.5-23.5T80-280v-480q0-33 23.5-56.5T160-840h640q33 0 56.5 23.5T880-760v480q0 33-23.5 56.5T800-200H640v80H320ZM160-280h640v-480H160v480Zm0 0v-480 480Z"], ["d", "M200-640h560v-80H200v80Zm0 0v-80 80Zm0 560q-33 0-56.5-23.5T120-160v-560q0-33 23.5-56.5T200-800h40v-80h80v80h320v-80h80v80h40q33 0 56.5 23.5T840-720v227q-19-9-39-15t-41-9v-43H200v400h252q7 22 16.5 42T491-80H200Zm520 40q-83 0-141.5-58.5T520-240q0-83 58.5-141.5T720-440q83 0 141.5 58.5T920-240q0 83-58.5 141.5T720-40Zm67-105 28-28-75-75v-112h-40v128l87 87Z"], ["d", "M280-280h280v-80H280v80Zm0-160h400v-80H280v80Zm0-160h400v-80H280v80Zm-80 480q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"], ["d", "m370-80-16-128q-13-5-24.5-12T307-235l-119 50L78-375l103-78q-1-7-1-13.5v-27q0-6.5 1-13.5L78-585l110-190 119 50q11-8 23-15t24-12l16-128h220l16 128q13 5 24.5 12t22.5 15l119-50 110 190-103 78q1 7 1 13.5v27q0 6.5-2 13.5l103 78-110 190-118-50q-11 8-23 15t-24 12L590-80H370Zm70-80h79l14-106q31-8 57.5-23.5T639-327l99 41 39-68-86-65q5-14 7-29.5t2-31.5q0-16-2-31.5t-7-29.5l86-65-39-68-99 42q-22-23-48.5-38.5T533-694l-13-106h-79l-14 106q-31 8-57.5 23.5T321-633l-99-41-39 68 86 64q-5 15-7 30t-2 32q0 16 2 31t7 30l-86 65 39 68 99-42q22 23 48.5 38.5T427-266l13 106Zm42-180q58 0 99-41t41-99q0-58-41-99t-99-41q-59 0-99.5 41T342-480q0 58 40.5 99t99.5 41Zm-2-140Z"]], template: function SidenavComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "nav", 0)(1, "a", 1);
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(2, "svg", 2);
        \u0275\u0275element(3, "path", 3);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(4, "span", 4);
        \u0275\u0275text(5, "Home");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(6, "a", 1);
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(7, "svg", 2);
        \u0275\u0275element(8, "path", 5);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(9, "span", 4);
        \u0275\u0275text(10, "Movies");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(11, "a", 1);
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(12, "svg", 2);
        \u0275\u0275element(13, "path", 6);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(14, "span", 4);
        \u0275\u0275text(15, "Series");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(16, "a", 1);
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(17, "svg", 2);
        \u0275\u0275element(18, "path", 7);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(19, "span", 4);
        \u0275\u0275text(20, "Tasks");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(21, "a", 1);
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(22, "svg", 2);
        \u0275\u0275element(23, "path", 8);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(24, "span", 4);
        \u0275\u0275text(25, "Logs");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(26, "a", 1);
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(27, "svg", 2);
        \u0275\u0275element(28, "path", 9);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(29, "span", 4);
        \u0275\u0275text(30, "Settings");
        \u0275\u0275elementEnd()()();
      }
      if (rf & 2) {
        \u0275\u0275advance();
        \u0275\u0275property("routerLink", ctx.RouteHome);
        \u0275\u0275advance(5);
        \u0275\u0275property("routerLink", ctx.RouteMovies);
        \u0275\u0275advance(5);
        \u0275\u0275property("routerLink", ctx.RouteSeries);
        \u0275\u0275advance(5);
        \u0275\u0275property("routerLink", ctx.RouteTasks);
        \u0275\u0275advance(5);
        \u0275\u0275property("routerLink", ctx.RouteLogs);
        \u0275\u0275advance(5);
        \u0275\u0275property("routerLink", ctx.RouteSettings);
      }
    }, dependencies: [RouterLink, RouterLinkActive], styles: ["\n\n.navmenu[_ngcontent-%COMP%] {\n  overflow: auto;\n  width: 210px;\n  height: 100%;\n  margin: 0;\n  padding: 0;\n  box-sizing: border-box;\n  display: flex;\n  flex-direction: column;\n  align-items: start;\n  justify-items: stretch;\n}\n.sidenav-button[_ngcontent-%COMP%] {\n  margin: 0;\n  padding: 1rem 1rem 1rem 2rem;\n  box-sizing: border-box;\n  width: 100%;\n  text-decoration: none;\n  color: inherit;\n  text-align: start;\n  font-weight: 400;\n  display: flex;\n  align-items: center;\n  transition: 0.3s;\n  cursor: pointer;\n  border-radius: 0;\n  border-bottom: 2px solid transparent;\n}\n.sidenav-button.active[_ngcontent-%COMP%] {\n  background-color: var(--color-secondary-container);\n  opacity: 1;\n  font-weight: 600;\n  color: var(--color-on-secondary-container);\n  border-bottom: 2px solid var(--color-primary);\n}\n.sidenav-button[_ngcontent-%COMP%]:not(.active):hover {\n  background-color: var(--color-secondary-container);\n  opacity: 0.6;\n  font-weight: 500;\n  color: var(--color-on-secondary-container);\n  border-bottom: 2px solid var(--color-primary);\n}\n.sidenav-button[_ngcontent-%COMP%]:last-child {\n  margin-bottom: auto;\n}\n.sidenav-button[_ngcontent-%COMP%]   .icon[_ngcontent-%COMP%] {\n  margin: 0;\n  margin-right: 0.5rem;\n  height: 1.75rem;\n  width: 1.75rem;\n  padding: 0.25rem;\n}\n@media (max-width: 1100px) {\n  .navmenu[_ngcontent-%COMP%] {\n    width: auto;\n  }\n  .sidenav-button[_ngcontent-%COMP%] {\n    padding: 1rem;\n  }\n  .sidenav-button[_ngcontent-%COMP%]   .btntext[_ngcontent-%COMP%] {\n    display: none;\n  }\n  .sidenav-button[_ngcontent-%COMP%]   .icon[_ngcontent-%COMP%] {\n    margin: auto;\n  }\n}\n@media (max-width: 765px) {\n  .navmenu[_ngcontent-%COMP%] {\n    flex-direction: row;\n    width: 100%;\n    height: auto;\n    margin: 0;\n    padding: 0;\n    padding-top: 1rem;\n    padding-bottom: 1rem;\n    justify-content: space-evenly;\n    align-items: center;\n  }\n  .sidenav-button[_ngcontent-%COMP%] {\n    padding: 0;\n    width: auto;\n    border-radius: 0;\n    border-bottom: 2px solid transparent;\n  }\n  .sidenav-button[_ngcontent-%COMP%]   .icon[_ngcontent-%COMP%] {\n    margin: 0.5rem;\n    height: 1.75rem;\n    width: 1.75rem;\n  }\n  .sidenav-button[_ngcontent-%COMP%]:last-child {\n    margin-bottom: 0;\n  }\n}\n/*# sourceMappingURL=sidenav.component.css.map */"], changeDetection: 0 });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(SidenavComponent, [{
    type: Component,
    args: [{ selector: "app-sidenav", imports: [RouterLink, RouterLinkActive], changeDetection: ChangeDetectionStrategy.OnPush, template: '<!-- Side Navbar -->\n<nav class="navmenu">\n  <a class="sidenav-button" [routerLink]="RouteHome" routerLinkActive="active">\n    <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n      <path d="M240-200h120v-240h240v240h120v-360L480-740 240-560v360Zm-80 80v-480l320-240 320 240v480H520v-240h-80v240H160Zm320-350Z" />\n    </svg>\n    <span class="btntext">Home</span>\n  </a>\n  <a class="sidenav-button" [routerLink]="RouteMovies" routerLinkActive="active">\n    <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n      <path\n        d="m160-800 80 160h120l-80-160h80l80 160h120l-80-160h80l80 160h120l-80-160h120q33 0 56.5 23.5T880-720v480q0 33-23.5 56.5T800-160H160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800Zm0 240v320h640v-320H160Zm0 0v320-320Z"\n      />\n    </svg>\n    <span class="btntext">Movies</span>\n  </a>\n  <a class="sidenav-button" [routerLink]="RouteSeries" routerLinkActive="active">\n    <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n      <path\n        d="M320-120v-80H160q-33 0-56.5-23.5T80-280v-480q0-33 23.5-56.5T160-840h640q33 0 56.5 23.5T880-760v480q0 33-23.5 56.5T800-200H640v80H320ZM160-280h640v-480H160v480Zm0 0v-480 480Z"\n      />\n    </svg>\n    <span class="btntext">Series</span>\n  </a>\n  <a class="sidenav-button" [routerLink]="RouteTasks" routerLinkActive="active">\n    <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n      <path\n        d="M200-640h560v-80H200v80Zm0 0v-80 80Zm0 560q-33 0-56.5-23.5T120-160v-560q0-33 23.5-56.5T200-800h40v-80h80v80h320v-80h80v80h40q33 0 56.5 23.5T840-720v227q-19-9-39-15t-41-9v-43H200v400h252q7 22 16.5 42T491-80H200Zm520 40q-83 0-141.5-58.5T520-240q0-83 58.5-141.5T720-440q83 0 141.5 58.5T920-240q0 83-58.5 141.5T720-40Zm67-105 28-28-75-75v-112h-40v128l87 87Z"\n      />\n    </svg>\n    <span class="btntext">Tasks</span>\n  </a>\n  <a class="sidenav-button" [routerLink]="RouteLogs" routerLinkActive="active">\n    <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n      <path\n        d="M280-280h280v-80H280v80Zm0-160h400v-80H280v80Zm0-160h400v-80H280v80Zm-80 480q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"\n      />\n    </svg>\n    <span class="btntext">Logs</span>\n  </a>\n  <a class="sidenav-button" [routerLink]="RouteSettings" routerLinkActive="active">\n    <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n      <path\n        d="m370-80-16-128q-13-5-24.5-12T307-235l-119 50L78-375l103-78q-1-7-1-13.5v-27q0-6.5 1-13.5L78-585l110-190 119 50q11-8 23-15t24-12l16-128h220l16 128q13 5 24.5 12t22.5 15l119-50 110 190-103 78q1 7 1 13.5v27q0 6.5-2 13.5l103 78-110 190-118-50q-11 8-23 15t-24 12L590-80H370Zm70-80h79l14-106q31-8 57.5-23.5T639-327l99 41 39-68-86-65q5-14 7-29.5t2-31.5q0-16-2-31.5t-7-29.5l86-65-39-68-99 42q-22-23-48.5-38.5T533-694l-13-106h-79l-14 106q-31 8-57.5 23.5T321-633l-99-41-39 68 86 64q-5 15-7 30t-2 32q0 16 2 31t7 30l-86 65 39 68 99-42q22 23 48.5 38.5T427-266l13 106Zm42-180q58 0 99-41t41-99q0-58-41-99t-99-41q-59 0-99.5 41T342-480q0 58 40.5 99t99.5 41Zm-2-140Z"\n      />\n    </svg>\n    <span class="btntext">Settings</span>\n  </a>\n</nav>\n', styles: ["/* src/app/nav/sidenav/sidenav.component.scss */\n.navmenu {\n  overflow: auto;\n  width: 210px;\n  height: 100%;\n  margin: 0;\n  padding: 0;\n  box-sizing: border-box;\n  display: flex;\n  flex-direction: column;\n  align-items: start;\n  justify-items: stretch;\n}\n.sidenav-button {\n  margin: 0;\n  padding: 1rem 1rem 1rem 2rem;\n  box-sizing: border-box;\n  width: 100%;\n  text-decoration: none;\n  color: inherit;\n  text-align: start;\n  font-weight: 400;\n  display: flex;\n  align-items: center;\n  transition: 0.3s;\n  cursor: pointer;\n  border-radius: 0;\n  border-bottom: 2px solid transparent;\n}\n.sidenav-button.active {\n  background-color: var(--color-secondary-container);\n  opacity: 1;\n  font-weight: 600;\n  color: var(--color-on-secondary-container);\n  border-bottom: 2px solid var(--color-primary);\n}\n.sidenav-button:not(.active):hover {\n  background-color: var(--color-secondary-container);\n  opacity: 0.6;\n  font-weight: 500;\n  color: var(--color-on-secondary-container);\n  border-bottom: 2px solid var(--color-primary);\n}\n.sidenav-button:last-child {\n  margin-bottom: auto;\n}\n.sidenav-button .icon {\n  margin: 0;\n  margin-right: 0.5rem;\n  height: 1.75rem;\n  width: 1.75rem;\n  padding: 0.25rem;\n}\n@media (max-width: 1100px) {\n  .navmenu {\n    width: auto;\n  }\n  .sidenav-button {\n    padding: 1rem;\n  }\n  .sidenav-button .btntext {\n    display: none;\n  }\n  .sidenav-button .icon {\n    margin: auto;\n  }\n}\n@media (max-width: 765px) {\n  .navmenu {\n    flex-direction: row;\n    width: 100%;\n    height: auto;\n    margin: 0;\n    padding: 0;\n    padding-top: 1rem;\n    padding-bottom: 1rem;\n    justify-content: space-evenly;\n    align-items: center;\n  }\n  .sidenav-button {\n    padding: 0;\n    width: auto;\n    border-radius: 0;\n    border-bottom: 2px solid transparent;\n  }\n  .sidenav-button .icon {\n    margin: 0.5rem;\n    height: 1.75rem;\n    width: 1.75rem;\n  }\n  .sidenav-button:last-child {\n    margin-bottom: 0;\n  }\n}\n/*# sourceMappingURL=sidenav.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(SidenavComponent, { className: "SidenavComponent", filePath: "src/app/nav/sidenav/sidenav.component.ts", lineNumber: 12 });
})();

// src/app/nav/topnav/topnav.component.ts
var _c0 = (a0) => ["/media/", a0];
function TopnavComponent_div_32_img_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "img", 38);
  }
  if (rf & 2) {
    const result_r3 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275propertyInterpolate("src", result_r3.poster_path || "assets/poster-lg.png", \u0275\u0275sanitizeUrl);
    \u0275\u0275propertyInterpolate("alt", result_r3.title);
  }
}
function TopnavComponent_div_32_span_2_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "span", 39);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const result_r3 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(result_r3.title + " (" + result_r3.year + ")");
  }
}
function TopnavComponent_div_32_span_3_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "span", 39);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const result_r3 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(result_r3.title);
  }
}
function TopnavComponent_div_32_Template(rf, ctx) {
  if (rf & 1) {
    const _r1 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 35);
    \u0275\u0275listener("click", function TopnavComponent_div_32_Template_div_click_0_listener() {
      \u0275\u0275restoreView(_r1);
      const ctx_r1 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r1.searchResults = []);
    });
    \u0275\u0275template(1, TopnavComponent_div_32_img_1_Template, 1, 2, "img", 36)(2, TopnavComponent_div_32_span_2_Template, 2, 1, "span", 37)(3, TopnavComponent_div_32_span_3_Template, 2, 1, "span", 37);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const result_r3 = ctx.$implicit;
    const ctx_r1 = \u0275\u0275nextContext();
    \u0275\u0275classProp("selected", result_r3.id === ctx_r1.selectedId);
    \u0275\u0275property("routerLink", result_r3.id === -1 ? null : \u0275\u0275pureFunction1(6, _c0, result_r3.id));
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", result_r3.id > 0);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", result_r3.id > 0);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", result_r3.id < 0);
  }
}
var TopnavComponent = class _TopnavComponent {
  constructor() {
    this.destroyRef = inject(DestroyRef);
    this.elementRef = inject(ElementRef);
    this.mediaService = inject(MediaService);
    this.renderer = inject(Renderer2);
    this.router = inject(Router);
    this.isDarkModeEnabled = true;
    this.searchQuery = "";
    this.searchForm = new FormControl();
    this.searchResults = [];
    this.selectedIndex = -1;
    this.selectedId = -1;
    this.RouteHome = RouteHome;
    this.noSearchResult = {
      id: -1,
      title: "No results found",
      imdb_id: "",
      txdb_id: "",
      poster_path: "",
      year: 0,
      youtube_trailer_id: "",
      is_movie: true
    };
  }
  clickout(event) {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.searchResults = [];
      this.selectedId = -1;
      this.selectedIndex = -1;
    }
  }
  disableSelection(event) {
    if (this.searchResults.length > 0) {
      this.selectedId = -1;
      this.selectedIndex = -1;
    }
  }
  handleKeyboardEvent(event) {
    const activeElement = document.activeElement;
    const isInputField = activeElement.tagName === "INPUT" || activeElement.tagName === "TEXTAREA" || activeElement.isContentEditable;
    if (!isInputField && event.key === "f") {
      event.preventDefault();
      const searchInput = document.getElementById("searchForm")?.querySelector("input");
      searchInput?.focus();
      return;
    }
    if (this.searchResults.length > 0) {
      if (event.key === "Escape") {
        this.searchResults = [];
        this.selectedId = -1;
        this.selectedIndex = -1;
        return;
      }
      let firstId = this.searchResults[0].id;
      let lastId = this.searchResults[this.searchResults.length - 1].id;
      if (event.key === "ArrowDown" || event.key === "Tab" && !event.shiftKey) {
        event.preventDefault();
        if (this.selectedId === lastId) {
          this.selectedIndex = 0;
          this.selectedId = firstId;
          return;
        }
        this.selectedIndex = this.selectedIndex + 1;
        this.selectedId = this.searchResults[this.selectedIndex].id;
        return;
      } else if (event.key === "ArrowUp" || event.shiftKey && event.key === "Tab") {
        event.preventDefault();
        if (this.selectedId === firstId) {
          this.selectedIndex = this.searchResults.length - 1;
          this.selectedId = lastId;
          return;
        }
        this.selectedIndex = this.selectedIndex - 1;
        this.selectedId = this.searchResults[this.selectedIndex].id;
        return;
      } else if (event.key === "Enter") {
        this.router.navigate([RouteMedia, this.selectedId]);
        this.searchResults = [];
        return;
      }
    }
  }
  // Check theme preference on page load and apply it
  ngOnInit() {
    this.searchForm.valueChanges.pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((value) => {
      this.onSearch(value);
    });
    const theme = localStorage.getItem("theme");
    if (theme) {
      let darkTheme = theme === "dark";
      this.setTheme(darkTheme);
    } else {
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        this.setTheme(true);
      } else {
        this.setTheme(false);
      }
    }
  }
  onThemeChange(event) {
    this.setTheme(event ? true : false);
    return;
  }
  setTheme(darkTheme = true) {
    let theme = darkTheme ? "dark" : "light";
    let oldTheme = darkTheme ? "light" : "dark";
    this.isDarkModeEnabled = darkTheme;
    this.renderer.setAttribute(document.documentElement, "theme", theme);
    this.renderer.removeClass(document.body, oldTheme);
    this.renderer.addClass(document.body, theme);
    localStorage.setItem("theme", theme);
    return;
  }
  onSearch(query = "") {
    if (query.length < 3) {
      this.searchResults = [];
      return;
    }
    if (query.trim() === this.searchQuery) {
      return;
    }
    this.searchQuery = query;
    this.mediaService.searchMedia(this.searchQuery).subscribe((media_list) => {
      if (media_list.length === 0) {
        this.searchResults = [this.noSearchResult];
        return;
      }
      this.searchResults = media_list;
    });
  }
  static {
    this.\u0275fac = function TopnavComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _TopnavComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _TopnavComponent, selectors: [["app-topnav"]], hostBindings: function TopnavComponent_HostBindings(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275listener("click", function TopnavComponent_click_HostBindingHandler($event) {
          return ctx.clickout($event);
        }, false, \u0275\u0275resolveDocument)("mousemove", function TopnavComponent_mousemove_HostBindingHandler($event) {
          return ctx.disableSelection($event);
        }, false, \u0275\u0275resolveDocument)("keydown", function TopnavComponent_keydown_HostBindingHandler($event) {
          return ctx.handleKeyboardEvent($event);
        }, false, \u0275\u0275resolveDocument);
      }
    }, decls: 36, vars: 6, consts: [[1, "navbar"], [1, "navlogo", 3, "routerLink"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 0 2260 512", "alt", "Trailarr Logo", "height", "40", 1, "sm-none", "trailarr"], ["d", "M0 90h60c0 -8.284 6.716 -15 15 -15s15 6.716 15 15h90l-75 -74H40C17.909 16 0 33.909 0 56z", "fill", "#d9e7ec"], ["d", "M60 90c0 -8.284 6.716 -15 15 -15s15 6.716 15 15z", "fill", "#005fe4"], ["d", "M180 90h120l-75 -74H105z", "fill", "#005fe4"], ["d", "M300 90h120l-75 -74H225z", "fill", "#d9e7ec"], ["d", "M420 90h92V56c0 -22.091 -17.909 -40 -40 -40H345z", "fill", "#005fe4"], ["d", "M0 90h60c0 8.284 6.716 15 15 15s15 -6.716 15 -15h90l-75 76H0z", "fill", "#b6c4cf"], ["d", "M60 90c0 8.284 6.716 15 15 15s15 -6.716 15 -15z", "fill", "#0040a0"], ["d", "M180 90h120l-75 76H105z", "fill", "#0040a0"], ["d", "M300 90h120l-75 76H225z", "fill", "#b6c4cf"], ["d", "M420 90h92v76H345z", "fill", "#0040a0"], ["d", "M0 166h256v330H40c-22.091 0 -40 -17.909 -40 -40z", "fill", "#ff631a"], ["d", "M512 166H256v330h216c22.091 0 40 -17.909 40 -40z", "fill", "#f03800"], ["d", "M256 256H100c-8.284 0 -15 6.716 -15 15s6.716 15 15 15h50v60h-50c-8.284 0 -15 6.716 -15 15s6.716 15 15 15h156v-30h-76v-60h76z", "fill", "#005fe4"], ["d", "M256 256h156c8.284 0 15 6.716 15 15s-6.716 15 -15 15h-46v60h46c8.284 0 15 6.716 15 15s-6.716 15 -15 15H256v-30h76v-60h-76z", "fill", "#0040a0"], ["transform", "translate(620 50)", "fill", "#006a6a", "fill-rule", "evenodd", "stroke", "#006a6a", "stroke-width", "0.944882", "stroke-linecap", "round", 1, "logo-text"], ["d", "M0 158.208v-41.472h46.08l10.24 -59.904 48.128 -10.752v70.656h62.976l-7.168 41.472h-55.808V309.76c-0.012 1.914 0.12 3.826 0.394 5.72q1.101 7.273 5.285 10.473 0.706 0.54 1.489 0.959a32.74 32.74 0 0 0 14.521 3.817q0.675 0.024 1.351 0.023 7.168 0 14.336 -1.024 3.358 -0.475 6.684 -1.132 3.205 -0.638 6.027 -1.404l0.089 -0.024c4.317 -0.99 8.584 -2.185 12.788 -3.58l0.012 -0.004 9.728 38.4 -4.608 1.536q-1.538 0.676 -3.12 1.239 -3.176 1.143 -7.613 2.361 -1.415 0.387 -2.835 0.752 -8.96 2.304 -20.992 4.096t-26.368 1.792 -26.368 -3.072a58.7 58.7 0 0 1 -13.115 -5.002 50 50 0 0 1 -7.621 -4.982 46.5 46.5 0 0 1 -13.104 -16.664 54 54 0 0 1 -0.464 -1q-4.864 -10.752 -4.864 -26.624V158.208z"], ["d", "M275.968 231.424v140.288H217.6V242.688c0.012 -7.18 -0.178 -14.36 -0.57 -21.531q-0.569 -10.049 -1.705 -18.714a176 176 0 0 0 -1.821 -11.211q-4.096 -20.736 -8.704 -33.536 -5.632 -14.848 -12.288 -24.064l46.08 -18.432q4.608 5.632 9.728 13.824 3.552 6.216 7.104 14.357 0.552 1.266 1.088 2.539 4.096 9.728 6.656 23.04 7.878 -22.845 21.209 -35.842a60 60 0 0 1 8.487 -6.91q19.456 -13.056 44.032 -13.056a87 87 0 0 1 15.131 1.271c2.318 0.407 4.616 0.922 6.885 1.545l2.286 0.631q7.786 2.155 7.453 2.185h-0.011l-16.384 56.832a0.1 0.1 0 0 0 0.032 -0.006q0.189 -0.122 -5.92 -2.81 -5.733 -2.523 -16.603 -2.785 -1.298 -0.03 -2.597 -0.031 -9.216 0 -18.432 4.608t-16.384 12.544a61.2 61.2 0 0 0 -8.641 12.475 75 75 0 0 0 -3.135 6.725q-4.608 11.264 -4.608 25.088Z"], ["d", "M592.384 127.488V248.32c-0.012 7.18 0.166 14.36 0.534 21.531q0.899 16.924 3.306 29.925 1.23 6.687 2.731 13.318 1.346 5.909 2.776 10.964a140 140 0 0 0 2.941 9.254q3.986 10.871 8.485 18.408a60 60 0 0 0 3.803 5.656l-45.568 18.432q-6.656 -6.656 -12.288 -15.872 -4.608 -8.192 -8.704 -19.712 -3.687 -10.37 -4.885 -24.268a145 145 0 0 1 -0.235 -3.124q-8.704 30.72 -27.904 46.336 -16.95 13.786 -44.474 15.402 -3.743 0.217 -7.494 0.214c-6.874 0.036 -13.736 -0.58 -20.494 -1.84a80 80 0 0 1 -21.234 -7.12q-17.664 -8.96 -29.44 -25.6a103.8 103.8 0 0 1 -11.818 -22.197 136 136 0 0 1 -5.59 -17.995q-5.632 -23.552 -5.632 -52.224 0 -29.184 8.96 -54.016a134.2 134.2 0 0 1 15.276 -30.248 119 119 0 0 1 9.812 -12.504q16.128 -17.92 38.656 -28.16t49.664 -10.24q15.36 0 32 2.304t30.976 4.864q10.976 1.96 19.401 3.77 2.463 0.528 4.919 1.094 9.984 2.304 11.52 2.816ZM534.016 232.96v-73.728q-5.12 -1.536 -15.36 -3.584 -9.34 -1.868 -16.976 -2.032 -0.727 -0.015 -1.456 -0.016 -15.212 0 -26.198 4.069a48 48 0 0 0 -5.802 2.587Q455.68 166.912 448 178.688t-10.752 28.16 -3.072 35.84q0 17.92 1.024 34.304t5.376 29.184T453.12 326.4q8.096 7.337 21.693 7.423l0.323 0.001q12.8 0 23.552 -8.704t18.688 -22.784 12.288 -32.256 4.352 -37.12Z"], ["d", "M658.944 315.904V116.736h58.368v194.048a61 61 0 0 0 0.21 5.254q0.447 5.108 1.846 8.178a10 10 0 0 0 1.528 2.44q3.584 4.096 10.752 4.096H736q2.304 0 4.352 -0.512 2.048 0 4.608 -0.512l6.144 36.864q-2.74 1.565 -6.676 2.832 -1.261 0.404 -2.54 0.752 -4.608 1.536 -11.52 2.56a91 91 0 0 1 -7.345 0.767q-3.91 0.257 -8.271 0.257a73 73 0 0 1 -16.43 -1.736q-12.009 -2.771 -20.509 -9.964a45 45 0 0 1 -4.533 -4.428 55.7 55.7 0 0 1 -13.072 -27.363 78 78 0 0 1 -1.264 -14.365ZM689.152 3.072q16.384 0 25.088 9.728t8.704 25.088 -8.96 25.6 -26.368 10.24q-16.384 0 -25.344 -9.984a34.8 34.8 0 0 1 -8.933 -22.765 45 45 0 0 1 -0.027 -1.555 46.1 46.1 0 0 1 1.479 -11.966 34.9 34.9 0 0 1 7.481 -14.146q8.278 -9.46 24.202 -10.181 1.338 -0.06 2.678 -0.059Z"], ["d", "M789.504 316.416V10.752L847.872 0v310.784q0 9.831 3.212 14.666 0.613 0.929 1.396 1.718a14.8 14.8 0 0 0 6.372 3.694q2.298 0.686 5.053 0.857a30 30 0 0 0 1.887 0.057q5.12 0 9.984 -0.512t8.96 -1.536q4.608 -1.024 8.192 -2.048l7.168 36.864q-6.656 2.56 -14.848 4.608 -6.16 1.76 -14.211 2.953 -1.341 0.198 -2.685 0.375 -4.996 0.647 -10.025 0.94 -5.655 0.34 -11.991 0.34a84 84 0 0 1 -15.974 -1.421q-17.314 -3.367 -27.034 -14.707a56.4 56.4 0 0 1 -12.606 -27.11 78.3 78.3 0 0 1 -1.218 -14.106Z"], ["d", "M1139.2 127.488V248.32c-0.012 7.18 0.166 14.36 0.534 21.531q0.899 16.924 3.306 29.925 1.23 6.687 2.731 13.318 1.346 5.909 2.776 10.964a140 140 0 0 0 2.941 9.254q3.986 10.871 8.485 18.408a60 60 0 0 0 3.803 5.656l-45.568 18.432q-6.656 -6.656 -12.288 -15.872 -4.608 -8.192 -8.704 -19.712 -3.687 -10.37 -4.885 -24.268a145 145 0 0 1 -0.235 -3.124q-8.704 30.72 -27.904 46.336 -16.95 13.786 -44.474 15.402 -3.743 0.217 -7.494 0.214c-6.874 0.036 -13.736 -0.58 -20.494 -1.84a80 80 0 0 1 -21.234 -7.12q-17.664 -8.96 -29.44 -25.6a103.8 103.8 0 0 1 -11.818 -22.197 136 136 0 0 1 -5.59 -17.995q-5.632 -23.552 -5.632 -52.224 0 -29.184 8.96 -54.016a134.2 134.2 0 0 1 15.276 -30.248 119 119 0 0 1 9.812 -12.504q16.128 -17.92 38.656 -28.16t49.664 -10.24q15.36 0 32 2.304t30.976 4.864q10.976 1.96 19.401 3.77 2.463 0.528 4.919 1.094 9.984 2.304 11.52 2.816Zm-58.368 105.472v-73.728q-5.12 -1.536 -15.36 -3.584 -9.34 -1.868 -16.976 -2.032 -0.727 -0.015 -1.456 -0.016 -15.212 0 -26.198 4.069a48 48 0 0 0 -5.802 2.587q-12.544 6.656 -20.224 18.432t-10.752 28.16 -3.072 35.84q0 17.92 1.024 34.304t5.376 29.184 12.544 20.224q8.096 7.337 21.693 7.423l0.323 0.001q12.8 0 23.552 -8.704t18.688 -22.784 12.288 -32.256 4.352 -37.12Z"], ["d", "M1260.544 231.424v140.288h-58.368V242.688c0.012 -7.18 -0.178 -14.36 -0.57 -21.531q-0.569 -10.049 -1.705 -18.714a176 176 0 0 0 -1.821 -11.211q-4.096 -20.736 -8.704 -33.536 -5.632 -14.848 -12.288 -24.064l46.08 -18.432q4.608 5.632 9.728 13.824 3.552 6.216 7.104 14.357 0.552 1.266 1.088 2.539 4.096 9.728 6.656 23.04 7.878 -22.845 21.209 -35.842a60 60 0 0 1 8.487 -6.91q19.456 -13.056 44.032 -13.056a87 87 0 0 1 15.131 1.271c2.318 0.407 4.616 0.922 6.885 1.545l2.286 0.631q7.786 2.155 7.453 2.185h-0.011l-16.384 56.832a0.1 0.1 0 0 0 0.032 -0.006q0.189 -0.122 -5.92 -2.81 -5.733 -2.523 -16.603 -2.785 -1.299 -0.03 -2.597 -0.031 -9.216 0 -18.432 4.608t-16.384 12.544a61.2 61.2 0 0 0 -8.641 12.475 75 75 0 0 0 -3.135 6.725q-4.608 11.264 -4.608 25.088Z"], ["d", "M1449.472 231.424v140.288h-58.368V242.688c0.012 -7.18 -0.178 -14.36 -0.57 -21.531q-0.569 -10.049 -1.705 -18.714a176 176 0 0 0 -1.821 -11.211q-4.096 -20.736 -8.704 -33.536 -5.632 -14.848 -12.288 -24.064l46.08 -18.432q4.608 5.632 9.728 13.824 3.552 6.216 7.104 14.357 0.552 1.266 1.088 2.539 4.096 9.728 6.656 23.04 7.878 -22.845 21.209 -35.842a60 60 0 0 1 8.487 -6.91q19.456 -13.056 44.032 -13.056a87 87 0 0 1 15.131 1.271c2.318 0.407 4.616 0.922 6.885 1.545l2.286 0.631q7.786 2.155 7.453 2.185h-0.011l-16.384 56.832a0.1 0.1 0 0 0 0.032 -0.006q0.189 -0.122 -5.92 -2.81 -5.733 -2.523 -16.603 -2.785 -1.299 -0.03 -2.597 -0.031 -9.216 0 -18.432 4.608t-16.384 12.544a61.2 61.2 0 0 0 -8.641 12.475 75 75 0 0 0 -3.135 6.725q-4.608 11.264 -4.608 25.088Z"], ["src", "/assets/logos/trailarr.svg", "alt", "Trailarr Logo", "width", "30", "height", "30", 1, "sm-show"], [1, "navsearch"], ["id", "searchForm", 1, "navsearch-form"], ["type", "text", "autocomplete", "off", "name", "query", "placeholder", "Search for media...", "aria-label", "search", 3, "formControl"], [1, "navsearch-results"], ["class", "title", 3, "selected", "routerLink", "click", 4, "ngFor", "ngForOf"], [1, "switch2", "sm-none"], ["id", "theme-switch", "type", "checkbox", 3, "ngModelChange", "ngModel"], [1, "slider2"], [1, "title", 3, "click", "routerLink"], ["class", "search-poster", 3, "src", "alt", 4, "ngIf"], ["class", "search-title", 4, "ngIf"], [1, "search-poster", 3, "src", "alt"], [1, "search-title"]], template: function TopnavComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "div", 0)(1, "a", 1);
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(2, "svg", 2)(3, "g");
        \u0275\u0275element(4, "path", 3)(5, "path", 4)(6, "path", 5)(7, "path", 6)(8, "path", 7)(9, "path", 8)(10, "path", 9)(11, "path", 10)(12, "path", 11)(13, "path", 12)(14, "path", 13)(15, "path", 14)(16, "path", 15)(17, "path", 16);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(18, "g", 17);
        \u0275\u0275element(19, "path", 18)(20, "path", 19)(21, "path", 20)(22, "path", 21)(23, "path", 22)(24, "path", 23)(25, "path", 24)(26, "path", 25);
        \u0275\u0275elementEnd()();
        \u0275\u0275namespaceHTML();
        \u0275\u0275element(27, "img", 26);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(28, "div", 27)(29, "form", 28);
        \u0275\u0275element(30, "input", 29);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(31, "div", 30);
        \u0275\u0275template(32, TopnavComponent_div_32_Template, 4, 8, "div", 31);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(33, "label", 32)(34, "input", 33);
        \u0275\u0275twoWayListener("ngModelChange", function TopnavComponent_Template_input_ngModelChange_34_listener($event) {
          \u0275\u0275twoWayBindingSet(ctx.isDarkModeEnabled, $event) || (ctx.isDarkModeEnabled = $event);
          return $event;
        });
        \u0275\u0275listener("ngModelChange", function TopnavComponent_Template_input_ngModelChange_34_listener($event) {
          return ctx.onThemeChange($event);
        });
        \u0275\u0275elementEnd();
        \u0275\u0275element(35, "span", 34);
        \u0275\u0275elementEnd()();
      }
      if (rf & 2) {
        \u0275\u0275advance();
        \u0275\u0275property("routerLink", ctx.RouteHome);
        \u0275\u0275advance(29);
        \u0275\u0275property("formControl", ctx.searchForm);
        \u0275\u0275advance();
        \u0275\u0275classProp("active", ctx.searchResults.length > 0);
        \u0275\u0275advance();
        \u0275\u0275property("ngForOf", ctx.searchResults);
        \u0275\u0275advance(2);
        \u0275\u0275twoWayProperty("ngModel", ctx.isDarkModeEnabled);
      }
    }, dependencies: [RouterLink, FormsModule, \u0275NgNoValidate, DefaultValueAccessor, CheckboxControlValueAccessor, NgControlStatus, NgControlStatusGroup, NgModel, NgForm, ReactiveFormsModule, FormControlDirective, NgIf, NgForOf], styles: ['\n\n.navbar[_ngcontent-%COMP%] {\n  padding: 1rem 0.5rem;\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  flex-direction: row;\n  width: 100%;\n}\n.navlogo[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  justify-content: center;\n  font-size: 1.5rem;\n  font-weight: 500;\n  color: var(--color-on-surface);\n  text-decoration: none;\n  margin: 0;\n  padding: 0;\n  width: 210px;\n}\n.trailarr[_ngcontent-%COMP%]   .logo-text[_ngcontent-%COMP%] {\n  fill: var(--color-on-surface);\n}\n.trailarr[_ngcontent-%COMP%]:hover   .logo-text[_ngcontent-%COMP%] {\n  fill: var(--color-primary);\n}\n.navlogotext[_ngcontent-%COMP%] {\n  margin-left: 0.5rem;\n}\n.navsearch[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  justify-content: center;\n  width: auto;\n  flex-grow: 1;\n  padding: 0.25rem;\n  position: relative;\n}\n.navsearch-form[_ngcontent-%COMP%] {\n  width: 100%;\n}\n.navsearch-form[_ngcontent-%COMP%]   input[_ngcontent-%COMP%] {\n  width: 100%;\n  padding: 0.5rem;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  margin: 0;\n  font-size: 1rem;\n  background-color: var(--color-surface-container-highest);\n  color: var(--color-on-surface);\n}\n.navsearch-form[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]:focus {\n  outline: var(--color-primary);\n  border: 1px solid var(--color-primary);\n}\n.navsearch-results[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 100%;\n  left: 2%;\n  color: var(--color-on-surface);\n  background-color: var(--color-surface-container-highest);\n  border: 0.5px solid var(--color-outline);\n  border-radius: 5px;\n  visibility: hidden;\n  opacity: 0;\n  display: none;\n  z-index: 10;\n}\n.active[_ngcontent-%COMP%] {\n  visibility: visible;\n  opacity: 1;\n  display: flex;\n  flex-direction: column;\n  max-height: 40vh;\n  max-width: 60vw;\n  overflow-x: hidden;\n  overflow-y: auto;\n  padding: 0.5rem;\n  scroll-behavior: smooth;\n  scroll-snap-type: y mandatory;\n  transition: 0.25s;\n}\n@media (width < 765px) {\n  .active[_ngcontent-%COMP%] {\n    max-width: 75vw;\n  }\n}\n.navsearch-results[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%] {\n  display: flex;\n  min-width: 300px;\n  width: auto;\n  padding: 0.5rem;\n  text-align: left;\n  text-wrap: pretty;\n  cursor: pointer;\n}\n.search-poster[_ngcontent-%COMP%] {\n  width: 3rem;\n}\n.search-title[_ngcontent-%COMP%] {\n  margin: auto 0.5rem;\n  text-align: left;\n}\n.navsearch-results[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%]:hover, \n.navsearch-results[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%]:focus, \n.navsearch-results[_ngcontent-%COMP%]   .selected[_ngcontent-%COMP%] {\n  background-color: var(--color-surface-variant);\n  outline: none;\n}\n.navsearch-results[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%]:focus, \n.navsearch-results[_ngcontent-%COMP%]   .selected[_ngcontent-%COMP%] {\n  scroll-snap-align: center;\n}\n@media (max-width: 900px) {\n  .navlogo[_ngcontent-%COMP%] {\n    width: auto;\n    padding-left: 1rem;\n    padding-right: 1rem;\n  }\n  .navlogotext[_ngcontent-%COMP%] {\n    display: none;\n  }\n}\n.switch2[_ngcontent-%COMP%] {\n  margin: 0 1rem;\n  display: block;\n  --width-of-switch: 3.5em;\n  --height-of-switch: 2em;\n  --size-of-icon: 1.4em;\n  --slider-offset: 0.3em;\n  position: relative;\n  width: var(--width-of-switch);\n  height: var(--height-of-switch);\n}\n.switch2[_ngcontent-%COMP%]   input[_ngcontent-%COMP%] {\n  opacity: 0;\n  width: 0;\n  height: 0;\n}\n.slider2[_ngcontent-%COMP%] {\n  position: absolute;\n  cursor: pointer;\n  top: 0;\n  left: 0;\n  right: 0;\n  bottom: 0;\n  background-color: #ffffff;\n  transition: 0.5s;\n  border-radius: 30px;\n}\n.slider2[_ngcontent-%COMP%]:before {\n  position: absolute;\n  content: "";\n  height: var(--size-of-icon, 1.4em);\n  width: var(--size-of-icon, 1.4em);\n  border-radius: 20px;\n  left: var(--slider-offset, 0.3em);\n  top: 50%;\n  transform: translateY(-50%);\n  background:\n    linear-gradient(\n      40deg,\n      #775651,\n      #904b40 70%);\n  transition: 0.5s;\n}\ninput[_ngcontent-%COMP%]:checked    + .slider2[_ngcontent-%COMP%] {\n  background-color: #140c0b;\n}\ninput[_ngcontent-%COMP%]:checked    + .slider2[_ngcontent-%COMP%]:before {\n  left: calc(100% - (var(--size-of-icon, 1.4em) + var(--slider-offset, 0.3em)));\n  background: #140c0b;\n  box-shadow: inset -3px -2px 5px -2px #e7bdb6, inset -10px -4px 0 0 #ffb4a8;\n}\n/*# sourceMappingURL=topnav.component.css.map */'] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(TopnavComponent, [{
    type: Component,
    args: [{ selector: "app-topnav", imports: [RouterLink, FormsModule, ReactiveFormsModule, NgIf, NgForOf, RouterLink], template: `<div class="navbar">
  <a class="navlogo" [routerLink]="RouteHome">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2260 512" alt="Trailarr Logo" height="40" class="sm-none trailarr">
      <!-- Logo -->
      <g>
        <path d="M0 90h60c0 -8.284 6.716 -15 15 -15s15 6.716 15 15h90l-75 -74H40C17.909 16 0 33.909 0 56z" fill="#d9e7ec" />
        <path d="M60 90c0 -8.284 6.716 -15 15 -15s15 6.716 15 15z" fill="#005fe4" />
        <path d="M180 90h120l-75 -74H105z" fill="#005fe4" />
        <path d="M300 90h120l-75 -74H225z" fill="#d9e7ec" />
        <path d="M420 90h92V56c0 -22.091 -17.909 -40 -40 -40H345z" fill="#005fe4" />
        <path d="M0 90h60c0 8.284 6.716 15 15 15s15 -6.716 15 -15h90l-75 76H0z" fill="#b6c4cf" />
        <path d="M60 90c0 8.284 6.716 15 15 15s15 -6.716 15 -15z" fill="#0040a0" />
        <path d="M180 90h120l-75 76H105z" fill="#0040a0" />
        <path d="M300 90h120l-75 76H225z" fill="#b6c4cf" />
        <path d="M420 90h92v76H345z" fill="#0040a0" />
        <path d="M0 166h256v330H40c-22.091 0 -40 -17.909 -40 -40z" fill="#ff631a" />
        <path d="M512 166H256v330h216c22.091 0 40 -17.909 40 -40z" fill="#f03800" />
        <path
          d="M256 256H100c-8.284 0 -15 6.716 -15 15s6.716 15 15 15h50v60h-50c-8.284 0 -15 6.716 -15 15s6.716 15 15 15h156v-30h-76v-60h76z"
          fill="#005fe4"
        />
        <path
          d="M256 256h156c8.284 0 15 6.716 15 15s-6.716 15 -15 15h-46v60h46c8.284 0 15 6.716 15 15s-6.716 15 -15 15H256v-30h76v-60h-76z"
          fill="#0040a0"
        />
      </g>
      <!-- Text -->
      <g
        class="logo-text"
        transform="translate(620 50)"
        fill="#006a6a"
        fill-rule="evenodd"
        stroke="#006a6a"
        stroke-width="0.944882"
        stroke-linecap="round"
      >
        <path
          d="M0 158.208v-41.472h46.08l10.24 -59.904 48.128 -10.752v70.656h62.976l-7.168 41.472h-55.808V309.76c-0.012 1.914 0.12 3.826 0.394 5.72q1.101 7.273 5.285 10.473 0.706 0.54 1.489 0.959a32.74 32.74 0 0 0 14.521 3.817q0.675 0.024 1.351 0.023 7.168 0 14.336 -1.024 3.358 -0.475 6.684 -1.132 3.205 -0.638 6.027 -1.404l0.089 -0.024c4.317 -0.99 8.584 -2.185 12.788 -3.58l0.012 -0.004 9.728 38.4 -4.608 1.536q-1.538 0.676 -3.12 1.239 -3.176 1.143 -7.613 2.361 -1.415 0.387 -2.835 0.752 -8.96 2.304 -20.992 4.096t-26.368 1.792 -26.368 -3.072a58.7 58.7 0 0 1 -13.115 -5.002 50 50 0 0 1 -7.621 -4.982 46.5 46.5 0 0 1 -13.104 -16.664 54 54 0 0 1 -0.464 -1q-4.864 -10.752 -4.864 -26.624V158.208z"
        />
        <path
          d="M275.968 231.424v140.288H217.6V242.688c0.012 -7.18 -0.178 -14.36 -0.57 -21.531q-0.569 -10.049 -1.705 -18.714a176 176 0 0 0 -1.821 -11.211q-4.096 -20.736 -8.704 -33.536 -5.632 -14.848 -12.288 -24.064l46.08 -18.432q4.608 5.632 9.728 13.824 3.552 6.216 7.104 14.357 0.552 1.266 1.088 2.539 4.096 9.728 6.656 23.04 7.878 -22.845 21.209 -35.842a60 60 0 0 1 8.487 -6.91q19.456 -13.056 44.032 -13.056a87 87 0 0 1 15.131 1.271c2.318 0.407 4.616 0.922 6.885 1.545l2.286 0.631q7.786 2.155 7.453 2.185h-0.011l-16.384 56.832a0.1 0.1 0 0 0 0.032 -0.006q0.189 -0.122 -5.92 -2.81 -5.733 -2.523 -16.603 -2.785 -1.298 -0.03 -2.597 -0.031 -9.216 0 -18.432 4.608t-16.384 12.544a61.2 61.2 0 0 0 -8.641 12.475 75 75 0 0 0 -3.135 6.725q-4.608 11.264 -4.608 25.088Z"
        />
        <path
          d="M592.384 127.488V248.32c-0.012 7.18 0.166 14.36 0.534 21.531q0.899 16.924 3.306 29.925 1.23 6.687 2.731 13.318 1.346 5.909 2.776 10.964a140 140 0 0 0 2.941 9.254q3.986 10.871 8.485 18.408a60 60 0 0 0 3.803 5.656l-45.568 18.432q-6.656 -6.656 -12.288 -15.872 -4.608 -8.192 -8.704 -19.712 -3.687 -10.37 -4.885 -24.268a145 145 0 0 1 -0.235 -3.124q-8.704 30.72 -27.904 46.336 -16.95 13.786 -44.474 15.402 -3.743 0.217 -7.494 0.214c-6.874 0.036 -13.736 -0.58 -20.494 -1.84a80 80 0 0 1 -21.234 -7.12q-17.664 -8.96 -29.44 -25.6a103.8 103.8 0 0 1 -11.818 -22.197 136 136 0 0 1 -5.59 -17.995q-5.632 -23.552 -5.632 -52.224 0 -29.184 8.96 -54.016a134.2 134.2 0 0 1 15.276 -30.248 119 119 0 0 1 9.812 -12.504q16.128 -17.92 38.656 -28.16t49.664 -10.24q15.36 0 32 2.304t30.976 4.864q10.976 1.96 19.401 3.77 2.463 0.528 4.919 1.094 9.984 2.304 11.52 2.816ZM534.016 232.96v-73.728q-5.12 -1.536 -15.36 -3.584 -9.34 -1.868 -16.976 -2.032 -0.727 -0.015 -1.456 -0.016 -15.212 0 -26.198 4.069a48 48 0 0 0 -5.802 2.587Q455.68 166.912 448 178.688t-10.752 28.16 -3.072 35.84q0 17.92 1.024 34.304t5.376 29.184T453.12 326.4q8.096 7.337 21.693 7.423l0.323 0.001q12.8 0 23.552 -8.704t18.688 -22.784 12.288 -32.256 4.352 -37.12Z"
        />
        <path
          d="M658.944 315.904V116.736h58.368v194.048a61 61 0 0 0 0.21 5.254q0.447 5.108 1.846 8.178a10 10 0 0 0 1.528 2.44q3.584 4.096 10.752 4.096H736q2.304 0 4.352 -0.512 2.048 0 4.608 -0.512l6.144 36.864q-2.74 1.565 -6.676 2.832 -1.261 0.404 -2.54 0.752 -4.608 1.536 -11.52 2.56a91 91 0 0 1 -7.345 0.767q-3.91 0.257 -8.271 0.257a73 73 0 0 1 -16.43 -1.736q-12.009 -2.771 -20.509 -9.964a45 45 0 0 1 -4.533 -4.428 55.7 55.7 0 0 1 -13.072 -27.363 78 78 0 0 1 -1.264 -14.365ZM689.152 3.072q16.384 0 25.088 9.728t8.704 25.088 -8.96 25.6 -26.368 10.24q-16.384 0 -25.344 -9.984a34.8 34.8 0 0 1 -8.933 -22.765 45 45 0 0 1 -0.027 -1.555 46.1 46.1 0 0 1 1.479 -11.966 34.9 34.9 0 0 1 7.481 -14.146q8.278 -9.46 24.202 -10.181 1.338 -0.06 2.678 -0.059Z"
        />
        <path
          d="M789.504 316.416V10.752L847.872 0v310.784q0 9.831 3.212 14.666 0.613 0.929 1.396 1.718a14.8 14.8 0 0 0 6.372 3.694q2.298 0.686 5.053 0.857a30 30 0 0 0 1.887 0.057q5.12 0 9.984 -0.512t8.96 -1.536q4.608 -1.024 8.192 -2.048l7.168 36.864q-6.656 2.56 -14.848 4.608 -6.16 1.76 -14.211 2.953 -1.341 0.198 -2.685 0.375 -4.996 0.647 -10.025 0.94 -5.655 0.34 -11.991 0.34a84 84 0 0 1 -15.974 -1.421q-17.314 -3.367 -27.034 -14.707a56.4 56.4 0 0 1 -12.606 -27.11 78.3 78.3 0 0 1 -1.218 -14.106Z"
        />
        <path
          d="M1139.2 127.488V248.32c-0.012 7.18 0.166 14.36 0.534 21.531q0.899 16.924 3.306 29.925 1.23 6.687 2.731 13.318 1.346 5.909 2.776 10.964a140 140 0 0 0 2.941 9.254q3.986 10.871 8.485 18.408a60 60 0 0 0 3.803 5.656l-45.568 18.432q-6.656 -6.656 -12.288 -15.872 -4.608 -8.192 -8.704 -19.712 -3.687 -10.37 -4.885 -24.268a145 145 0 0 1 -0.235 -3.124q-8.704 30.72 -27.904 46.336 -16.95 13.786 -44.474 15.402 -3.743 0.217 -7.494 0.214c-6.874 0.036 -13.736 -0.58 -20.494 -1.84a80 80 0 0 1 -21.234 -7.12q-17.664 -8.96 -29.44 -25.6a103.8 103.8 0 0 1 -11.818 -22.197 136 136 0 0 1 -5.59 -17.995q-5.632 -23.552 -5.632 -52.224 0 -29.184 8.96 -54.016a134.2 134.2 0 0 1 15.276 -30.248 119 119 0 0 1 9.812 -12.504q16.128 -17.92 38.656 -28.16t49.664 -10.24q15.36 0 32 2.304t30.976 4.864q10.976 1.96 19.401 3.77 2.463 0.528 4.919 1.094 9.984 2.304 11.52 2.816Zm-58.368 105.472v-73.728q-5.12 -1.536 -15.36 -3.584 -9.34 -1.868 -16.976 -2.032 -0.727 -0.015 -1.456 -0.016 -15.212 0 -26.198 4.069a48 48 0 0 0 -5.802 2.587q-12.544 6.656 -20.224 18.432t-10.752 28.16 -3.072 35.84q0 17.92 1.024 34.304t5.376 29.184 12.544 20.224q8.096 7.337 21.693 7.423l0.323 0.001q12.8 0 23.552 -8.704t18.688 -22.784 12.288 -32.256 4.352 -37.12Z"
        />
        <path
          d="M1260.544 231.424v140.288h-58.368V242.688c0.012 -7.18 -0.178 -14.36 -0.57 -21.531q-0.569 -10.049 -1.705 -18.714a176 176 0 0 0 -1.821 -11.211q-4.096 -20.736 -8.704 -33.536 -5.632 -14.848 -12.288 -24.064l46.08 -18.432q4.608 5.632 9.728 13.824 3.552 6.216 7.104 14.357 0.552 1.266 1.088 2.539 4.096 9.728 6.656 23.04 7.878 -22.845 21.209 -35.842a60 60 0 0 1 8.487 -6.91q19.456 -13.056 44.032 -13.056a87 87 0 0 1 15.131 1.271c2.318 0.407 4.616 0.922 6.885 1.545l2.286 0.631q7.786 2.155 7.453 2.185h-0.011l-16.384 56.832a0.1 0.1 0 0 0 0.032 -0.006q0.189 -0.122 -5.92 -2.81 -5.733 -2.523 -16.603 -2.785 -1.299 -0.03 -2.597 -0.031 -9.216 0 -18.432 4.608t-16.384 12.544a61.2 61.2 0 0 0 -8.641 12.475 75 75 0 0 0 -3.135 6.725q-4.608 11.264 -4.608 25.088Z"
        />
        <path
          d="M1449.472 231.424v140.288h-58.368V242.688c0.012 -7.18 -0.178 -14.36 -0.57 -21.531q-0.569 -10.049 -1.705 -18.714a176 176 0 0 0 -1.821 -11.211q-4.096 -20.736 -8.704 -33.536 -5.632 -14.848 -12.288 -24.064l46.08 -18.432q4.608 5.632 9.728 13.824 3.552 6.216 7.104 14.357 0.552 1.266 1.088 2.539 4.096 9.728 6.656 23.04 7.878 -22.845 21.209 -35.842a60 60 0 0 1 8.487 -6.91q19.456 -13.056 44.032 -13.056a87 87 0 0 1 15.131 1.271c2.318 0.407 4.616 0.922 6.885 1.545l2.286 0.631q7.786 2.155 7.453 2.185h-0.011l-16.384 56.832a0.1 0.1 0 0 0 0.032 -0.006q0.189 -0.122 -5.92 -2.81 -5.733 -2.523 -16.603 -2.785 -1.299 -0.03 -2.597 -0.031 -9.216 0 -18.432 4.608t-16.384 12.544a61.2 61.2 0 0 0 -8.641 12.475 75 75 0 0 0 -3.135 6.725q-4.608 11.264 -4.608 25.088Z"
        />
      </g>
    </svg>
    <img src="/assets/logos/trailarr.svg" alt="Trailarr Logo" width="30" height="30" class="sm-show" />
  </a>
  <div class="navsearch">
    <form id="searchForm" class="navsearch-form">
      <input type="text" autocomplete="off" [formControl]="searchForm" name="query" placeholder="Search for media..." aria-label="search" />
    </form>
    <div class="navsearch-results" [class.active]="searchResults.length > 0">
      <!-- <button *ngIf="searchResults.length > 0" (click)="searchResults = []">Close</button> -->

      <div
        *ngFor="let result of searchResults"
        class="title"
        [class.selected]="result.id === selectedId"
        [routerLink]="result.id === -1 ? null : ['/media/', result.id]"
        (click)="searchResults = []"
      >
        <img
          *ngIf="result.id > 0"
          src="{{ result.poster_path || 'assets/poster-lg.png' }}"
          alt="{{ result.title }}"
          class="search-poster"
        />
        <span *ngIf="result.id > 0" class="search-title">{{ result.title + ' (' + result.year + ')' }}</span>
        <span *ngIf="result.id < 0" class="search-title">{{ result.title }}</span>
      </div>
    </div>
  </div>
  <label class="switch2 sm-none">
    <input id="theme-switch" type="checkbox" [(ngModel)]="isDarkModeEnabled" (ngModelChange)="onThemeChange($event)" />
    <span class="slider2"></span>
  </label>
</div>
`, styles: ['/* src/app/nav/topnav/topnav.component.scss */\n.navbar {\n  padding: 1rem 0.5rem;\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  flex-direction: row;\n  width: 100%;\n}\n.navlogo {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  justify-content: center;\n  font-size: 1.5rem;\n  font-weight: 500;\n  color: var(--color-on-surface);\n  text-decoration: none;\n  margin: 0;\n  padding: 0;\n  width: 210px;\n}\n.trailarr .logo-text {\n  fill: var(--color-on-surface);\n}\n.trailarr:hover .logo-text {\n  fill: var(--color-primary);\n}\n.navlogotext {\n  margin-left: 0.5rem;\n}\n.navsearch {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  justify-content: center;\n  width: auto;\n  flex-grow: 1;\n  padding: 0.25rem;\n  position: relative;\n}\n.navsearch-form {\n  width: 100%;\n}\n.navsearch-form input {\n  width: 100%;\n  padding: 0.5rem;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  margin: 0;\n  font-size: 1rem;\n  background-color: var(--color-surface-container-highest);\n  color: var(--color-on-surface);\n}\n.navsearch-form input:focus {\n  outline: var(--color-primary);\n  border: 1px solid var(--color-primary);\n}\n.navsearch-results {\n  position: absolute;\n  top: 100%;\n  left: 2%;\n  color: var(--color-on-surface);\n  background-color: var(--color-surface-container-highest);\n  border: 0.5px solid var(--color-outline);\n  border-radius: 5px;\n  visibility: hidden;\n  opacity: 0;\n  display: none;\n  z-index: 10;\n}\n.active {\n  visibility: visible;\n  opacity: 1;\n  display: flex;\n  flex-direction: column;\n  max-height: 40vh;\n  max-width: 60vw;\n  overflow-x: hidden;\n  overflow-y: auto;\n  padding: 0.5rem;\n  scroll-behavior: smooth;\n  scroll-snap-type: y mandatory;\n  transition: 0.25s;\n}\n@media (width < 765px) {\n  .active {\n    max-width: 75vw;\n  }\n}\n.navsearch-results .title {\n  display: flex;\n  min-width: 300px;\n  width: auto;\n  padding: 0.5rem;\n  text-align: left;\n  text-wrap: pretty;\n  cursor: pointer;\n}\n.search-poster {\n  width: 3rem;\n}\n.search-title {\n  margin: auto 0.5rem;\n  text-align: left;\n}\n.navsearch-results .title:hover,\n.navsearch-results .title:focus,\n.navsearch-results .selected {\n  background-color: var(--color-surface-variant);\n  outline: none;\n}\n.navsearch-results .title:focus,\n.navsearch-results .selected {\n  scroll-snap-align: center;\n}\n@media (max-width: 900px) {\n  .navlogo {\n    width: auto;\n    padding-left: 1rem;\n    padding-right: 1rem;\n  }\n  .navlogotext {\n    display: none;\n  }\n}\n.switch2 {\n  margin: 0 1rem;\n  display: block;\n  --width-of-switch: 3.5em;\n  --height-of-switch: 2em;\n  --size-of-icon: 1.4em;\n  --slider-offset: 0.3em;\n  position: relative;\n  width: var(--width-of-switch);\n  height: var(--height-of-switch);\n}\n.switch2 input {\n  opacity: 0;\n  width: 0;\n  height: 0;\n}\n.slider2 {\n  position: absolute;\n  cursor: pointer;\n  top: 0;\n  left: 0;\n  right: 0;\n  bottom: 0;\n  background-color: #ffffff;\n  transition: 0.5s;\n  border-radius: 30px;\n}\n.slider2:before {\n  position: absolute;\n  content: "";\n  height: var(--size-of-icon, 1.4em);\n  width: var(--size-of-icon, 1.4em);\n  border-radius: 20px;\n  left: var(--slider-offset, 0.3em);\n  top: 50%;\n  transform: translateY(-50%);\n  background:\n    linear-gradient(\n      40deg,\n      #775651,\n      #904b40 70%);\n  transition: 0.5s;\n}\ninput:checked + .slider2 {\n  background-color: #140c0b;\n}\ninput:checked + .slider2:before {\n  left: calc(100% - (var(--size-of-icon, 1.4em) + var(--slider-offset, 0.3em)));\n  background: #140c0b;\n  box-shadow: inset -3px -2px 5px -2px #e7bdb6, inset -10px -4px 0 0 #ffb4a8;\n}\n/*# sourceMappingURL=topnav.component.css.map */\n'] }]
  }], null, { clickout: [{
    type: HostListener,
    args: ["document:click", ["$event"]]
  }], disableSelection: [{
    type: HostListener,
    args: ["document:mousemove", ["$event"]]
  }], handleKeyboardEvent: [{
    type: HostListener,
    args: ["document:keydown", ["$event"]]
  }] });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(TopnavComponent, { className: "TopnavComponent", filePath: "src/app/nav/topnav/topnav.component.ts", lineNumber: 17 });
})();

// src/app/app.component.ts
var _c02 = ["sessionEndedDialog"];
function AppComponent_div_9_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 16)(1, "span");
    \u0275\u0275text(2);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const msg_r2 = ctx.$implicit;
    \u0275\u0275property("ngClass", msg_r2.type.toLowerCase());
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(msg_r2.message);
  }
}
var AppComponent = class _AppComponent {
  constructor() {
    this.websocketService = inject(WebsocketService);
    this.messages = [];
    this.IDLE_LIMIT = 10 * msMinute;
  }
  ngOnInit() {
    this.resetIdleTimer();
    this.toastSubscription = this.websocketService.toastMessage.subscribe({
      next: (data) => {
        this.messages.unshift(data);
        setTimeout(() => {
          this.messages.pop();
        }, 3e3);
      }
    });
  }
  // Uncomment the below code to enable mouse movement detection too!
  // @HostListener('document:mousemove', ['$event'])
  resetIdleTimer() {
    clearTimeout(this.timeoutId);
    this.timeoutId = setTimeout(() => {
      this.closeAllSubscriptions();
    }, this.IDLE_LIMIT);
  }
  closeAllSubscriptions() {
    console.log("Session Idle, closing all subscriptions!");
    this.showDialog();
    this.websocketService.close();
    this.toastSubscription?.unsubscribe();
    document.cookie = "trailarr_api_key=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  }
  ngOnDestroy() {
    this.closeAllSubscriptions();
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
  }
  showDialog() {
    this.sessionEndedDialog.nativeElement.showModal();
  }
  reloadPage() {
    window.location.reload();
  }
  static {
    this.\u0275fac = function AppComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _AppComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _AppComponent, selectors: [["app-root"]], viewQuery: function AppComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuery(_c02, 5);
      }
      if (rf & 2) {
        let _t;
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.sessionEndedDialog = _t.first);
      }
    }, hostBindings: function AppComponent_HostBindings(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275listener("click", function AppComponent_click_HostBindingHandler($event) {
          return ctx.resetIdleTimer($event);
        }, false, \u0275\u0275resolveDocument)("keypress", function AppComponent_keypress_HostBindingHandler($event) {
          return ctx.resetIdleTimer($event);
        }, false, \u0275\u0275resolveDocument);
      }
    }, decls: 25, vars: 1, consts: [["sessionEndedDialog", ""], [1, "mainroot"], [1, "topnavbar"], [1, "mainbody"], [1, "sidebar"], [1, "main-content"], [1, "toast-container"], ["class", "toast", 3, "ngClass", 4, "ngFor", "ngForOf"], [1, "dialog-content", 3, "click"], [1, "loading-container"], [1, "loading-container-inner"], [1, "dash", "first"], [1, "dash", "seconde"], [1, "dash", "third"], [1, "dash", "fourth"], ["tabindex", "1", 1, "secondary", 3, "click"], [1, "toast", 3, "ngClass"]], template: function AppComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275elementStart(0, "div", 1)(1, "header", 2);
        \u0275\u0275element(2, "app-topnav");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(3, "div", 3)(4, "div", 4);
        \u0275\u0275element(5, "app-sidenav");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(6, "main", 5);
        \u0275\u0275element(7, "router-outlet");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(8, "div", 6);
        \u0275\u0275template(9, AppComponent_div_9_Template, 3, 2, "div", 7);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(10, "dialog", null, 0)(12, "div", 8);
        \u0275\u0275listener("click", function AppComponent_Template_div_click_12_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(13, "h2");
        \u0275\u0275text(14, "Session Timed Out!");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(15, "p");
        \u0275\u0275text(16, "You we gone for a while, we closed your session!");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(17, "div", 9)(18, "div", 10);
        \u0275\u0275element(19, "div", 11)(20, "div", 12)(21, "div", 13)(22, "div", 14);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(23, "button", 15);
        \u0275\u0275listener("click", function AppComponent_Template_button_click_23_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.reloadPage());
        });
        \u0275\u0275text(24, "Refresh");
        \u0275\u0275elementEnd()()();
      }
      if (rf & 2) {
        \u0275\u0275advance(9);
        \u0275\u0275property("ngForOf", ctx.messages);
      }
    }, dependencies: [RouterOutlet, TopnavComponent, SidenavComponent, NgForOf, NgClass], styles: ["\n\n.mainroot[_ngcontent-%COMP%] {\n  height: 100%;\n  display: flex;\n  flex-direction: column;\n  background-color: var(--color-background);\n  color: var(--color-on-background);\n  position: relative;\n}\n@media (width < 765px) {\n  .mainroot[_ngcontent-%COMP%] {\n    height: auto;\n  }\n}\n.topnavbar[_ngcontent-%COMP%] {\n  width: 100%;\n  height: auto;\n  z-index: 100;\n  position: sticky;\n  top: 0;\n  background-color: var(--color-surface-container);\n  color: var(--color-on-surface);\n}\n.mainbody[_ngcontent-%COMP%] {\n  margin: 0;\n  display: flex;\n  flex-direction: row;\n  flex: 1 1 auto;\n  background-color: var(--color-surface);\n  color: var(--color-on-surface);\n}\n@media (width < 765px) {\n  .mainbody[_ngcontent-%COMP%] {\n    flex-direction: column;\n  }\n}\n.sidebar[_ngcontent-%COMP%] {\n  width: auto;\n  z-index: 100;\n  background-color: var(--color-surface-container);\n  color: var(--color-on-surface);\n  order: 1;\n  position: sticky;\n  top: 76px;\n  height: calc(100vh - 76px);\n}\n@media (width < 765px) {\n  .sidebar[_ngcontent-%COMP%] {\n    width: 100%;\n    height: auto;\n    position: fixed;\n    bottom: 0;\n    top: auto;\n    left: 0;\n    order: 2;\n  }\n}\n.main-content[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  flex: 1 1 auto;\n  order: 2;\n  background-color: var(--color-surface);\n  color: var(--color-on-surface);\n}\n@media (width < 765px) {\n  .main-content[_ngcontent-%COMP%] {\n    order: 1;\n    margin: 0.5rem;\n    margin-bottom: 80px;\n  }\n}\n.toast-container[_ngcontent-%COMP%] {\n  position: fixed;\n  top: 5rem;\n  right: 3rem;\n  z-index: 999;\n  max-width: 25%;\n  padding: 1rem;\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n}\n@media (width < 765px) {\n  .toast-container[_ngcontent-%COMP%] {\n    max-width: 80%;\n    right: 1rem;\n    padding: 0.5rem;\n  }\n}\n.toast[_ngcontent-%COMP%] {\n  text-wrap: wrap;\n  padding: 1rem;\n  border-radius: 0.5rem;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  animation: _ngcontent-%COMP%_slideInRight 0.3s ease-out forwards;\n}\n.info[_ngcontent-%COMP%] {\n  background-color: var(--color-info);\n  color: var(--color-info-text);\n}\n.success[_ngcontent-%COMP%] {\n  background-color: var(--color-success);\n  color: var(--color-success-text);\n}\n.error[_ngcontent-%COMP%] {\n  background-color: var(--color-warning);\n  color: var(--color-warning-text);\n}\n@keyframes _ngcontent-%COMP%_slideInRight {\n  from {\n    transform: translateX(100%);\n    opacity: 0;\n  }\n  to {\n    transform: translateX(0);\n    opacity: 1;\n  }\n}\n.dialog-content[_ngcontent-%COMP%] {\n  padding: 1rem;\n}\n.loading-container[_ngcontent-%COMP%] {\n  position: relative;\n  height: 6rem;\n  margin: 1rem;\n}\n.loading-container-inner[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 50%;\n  left: 50%;\n  transform: translate(-50%, -50%);\n  display: flex;\n}\n.dash[_ngcontent-%COMP%] {\n  margin: 0 15px;\n  width: 35px;\n  height: 15px;\n  border-radius: 8px;\n  background: var(--color-primary);\n  box-shadow: var(--color-surface-tint) 0 0 15px 0;\n}\n.first[_ngcontent-%COMP%] {\n  margin-right: -18px;\n  transform-origin: center left;\n  animation: _ngcontent-%COMP%_spin 3s linear infinite;\n}\n.seconde[_ngcontent-%COMP%] {\n  transform-origin: center right;\n  animation: _ngcontent-%COMP%_spin2 3s linear infinite;\n  animation-delay: 0.2s;\n}\n.third[_ngcontent-%COMP%] {\n  transform-origin: center right;\n  animation: _ngcontent-%COMP%_spin3 3s linear infinite;\n  animation-delay: 0.3s;\n}\n.fourth[_ngcontent-%COMP%] {\n  transform-origin: center right;\n  animation: _ngcontent-%COMP%_spin4 3s linear infinite;\n  animation-delay: 0.4s;\n}\n@keyframes _ngcontent-%COMP%_spin {\n  0% {\n    transform: rotate(0deg);\n  }\n  25% {\n    transform: rotate(360deg);\n  }\n  30% {\n    transform: rotate(370deg);\n  }\n  35% {\n    transform: rotate(360deg);\n  }\n  100% {\n    transform: rotate(360deg);\n  }\n}\n@keyframes _ngcontent-%COMP%_spin2 {\n  0% {\n    transform: rotate(0deg);\n  }\n  20% {\n    transform: rotate(0deg);\n  }\n  30% {\n    transform: rotate(-180deg);\n  }\n  35% {\n    transform: rotate(-190deg);\n  }\n  40% {\n    transform: rotate(-180deg);\n  }\n  78% {\n    transform: rotate(-180deg);\n  }\n  95% {\n    transform: rotate(-360deg);\n  }\n  98% {\n    transform: rotate(-370deg);\n  }\n  100% {\n    transform: rotate(-360deg);\n  }\n}\n@keyframes _ngcontent-%COMP%_spin3 {\n  0% {\n    transform: rotate(0deg);\n  }\n  27% {\n    transform: rotate(0deg);\n  }\n  40% {\n    transform: rotate(180deg);\n  }\n  45% {\n    transform: rotate(190deg);\n  }\n  50% {\n    transform: rotate(180deg);\n  }\n  62% {\n    transform: rotate(180deg);\n  }\n  75% {\n    transform: rotate(360deg);\n  }\n  80% {\n    transform: rotate(370deg);\n  }\n  85% {\n    transform: rotate(360deg);\n  }\n  100% {\n    transform: rotate(360deg);\n  }\n}\n@keyframes _ngcontent-%COMP%_spin4 {\n  0% {\n    transform: rotate(0deg);\n  }\n  38% {\n    transform: rotate(0deg);\n  }\n  60% {\n    transform: rotate(-360deg);\n  }\n  65% {\n    transform: rotate(-370deg);\n  }\n  75% {\n    transform: rotate(-360deg);\n  }\n  100% {\n    transform: rotate(-360deg);\n  }\n}\n/*# sourceMappingURL=app.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(AppComponent, [{
    type: Component,
    args: [{ selector: "app-root", imports: [RouterOutlet, TopnavComponent, SidenavComponent, NgForOf, NgClass], template: `<div class="mainroot">
  <header class="topnavbar">
    <!-- Navbar content goes here -->
    <app-topnav></app-topnav>
  </header>
  <div class="mainbody">
    <div class="sidebar">
      <!-- Sidebar content goes here -->
      <app-sidenav></app-sidenav>
    </div>
    <main class="main-content">
      <!-- Main content goes here -->
      <router-outlet></router-outlet>
    </main>
  </div>
  <!-- Container to show Websocket messages received from server -->
  <div class="toast-container">
    <div *ngFor="let msg of messages" class="toast" [ngClass]="msg.type.toLowerCase()">
      <span>{{ msg.message }}</span>
    </div>
  </div>
</div>

<!-- Session Timed Out Dialog -->
<dialog #sessionEndedDialog>
  <div class="dialog-content" (click)="$event.stopPropagation()">
    <h2>Session Timed Out!</h2>
    <p>You we gone for a while, we closed your session!</p>
    <!-- <p>Click on 'Refresh' button below to refresh the page</p> -->
    <div class="loading-container">
      <div class="loading-container-inner">
        <div class="dash first"></div>
        <div class="dash seconde"></div>
        <div class="dash third"></div>
        <div class="dash fourth"></div>
      </div>
    </div>
    <button class="secondary" (click)="reloadPage()" tabindex="1">Refresh</button>
  </div>
</dialog>
`, styles: ["/* src/app/app.component.scss */\n.mainroot {\n  height: 100%;\n  display: flex;\n  flex-direction: column;\n  background-color: var(--color-background);\n  color: var(--color-on-background);\n  position: relative;\n}\n@media (width < 765px) {\n  .mainroot {\n    height: auto;\n  }\n}\n.topnavbar {\n  width: 100%;\n  height: auto;\n  z-index: 100;\n  position: sticky;\n  top: 0;\n  background-color: var(--color-surface-container);\n  color: var(--color-on-surface);\n}\n.mainbody {\n  margin: 0;\n  display: flex;\n  flex-direction: row;\n  flex: 1 1 auto;\n  background-color: var(--color-surface);\n  color: var(--color-on-surface);\n}\n@media (width < 765px) {\n  .mainbody {\n    flex-direction: column;\n  }\n}\n.sidebar {\n  width: auto;\n  z-index: 100;\n  background-color: var(--color-surface-container);\n  color: var(--color-on-surface);\n  order: 1;\n  position: sticky;\n  top: 76px;\n  height: calc(100vh - 76px);\n}\n@media (width < 765px) {\n  .sidebar {\n    width: 100%;\n    height: auto;\n    position: fixed;\n    bottom: 0;\n    top: auto;\n    left: 0;\n    order: 2;\n  }\n}\n.main-content {\n  display: flex;\n  flex-direction: column;\n  flex: 1 1 auto;\n  order: 2;\n  background-color: var(--color-surface);\n  color: var(--color-on-surface);\n}\n@media (width < 765px) {\n  .main-content {\n    order: 1;\n    margin: 0.5rem;\n    margin-bottom: 80px;\n  }\n}\n.toast-container {\n  position: fixed;\n  top: 5rem;\n  right: 3rem;\n  z-index: 999;\n  max-width: 25%;\n  padding: 1rem;\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n}\n@media (width < 765px) {\n  .toast-container {\n    max-width: 80%;\n    right: 1rem;\n    padding: 0.5rem;\n  }\n}\n.toast {\n  text-wrap: wrap;\n  padding: 1rem;\n  border-radius: 0.5rem;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  animation: slideInRight 0.3s ease-out forwards;\n}\n.info {\n  background-color: var(--color-info);\n  color: var(--color-info-text);\n}\n.success {\n  background-color: var(--color-success);\n  color: var(--color-success-text);\n}\n.error {\n  background-color: var(--color-warning);\n  color: var(--color-warning-text);\n}\n@keyframes slideInRight {\n  from {\n    transform: translateX(100%);\n    opacity: 0;\n  }\n  to {\n    transform: translateX(0);\n    opacity: 1;\n  }\n}\n.dialog-content {\n  padding: 1rem;\n}\n.loading-container {\n  position: relative;\n  height: 6rem;\n  margin: 1rem;\n}\n.loading-container-inner {\n  position: absolute;\n  top: 50%;\n  left: 50%;\n  transform: translate(-50%, -50%);\n  display: flex;\n}\n.dash {\n  margin: 0 15px;\n  width: 35px;\n  height: 15px;\n  border-radius: 8px;\n  background: var(--color-primary);\n  box-shadow: var(--color-surface-tint) 0 0 15px 0;\n}\n.first {\n  margin-right: -18px;\n  transform-origin: center left;\n  animation: spin 3s linear infinite;\n}\n.seconde {\n  transform-origin: center right;\n  animation: spin2 3s linear infinite;\n  animation-delay: 0.2s;\n}\n.third {\n  transform-origin: center right;\n  animation: spin3 3s linear infinite;\n  animation-delay: 0.3s;\n}\n.fourth {\n  transform-origin: center right;\n  animation: spin4 3s linear infinite;\n  animation-delay: 0.4s;\n}\n@keyframes spin {\n  0% {\n    transform: rotate(0deg);\n  }\n  25% {\n    transform: rotate(360deg);\n  }\n  30% {\n    transform: rotate(370deg);\n  }\n  35% {\n    transform: rotate(360deg);\n  }\n  100% {\n    transform: rotate(360deg);\n  }\n}\n@keyframes spin2 {\n  0% {\n    transform: rotate(0deg);\n  }\n  20% {\n    transform: rotate(0deg);\n  }\n  30% {\n    transform: rotate(-180deg);\n  }\n  35% {\n    transform: rotate(-190deg);\n  }\n  40% {\n    transform: rotate(-180deg);\n  }\n  78% {\n    transform: rotate(-180deg);\n  }\n  95% {\n    transform: rotate(-360deg);\n  }\n  98% {\n    transform: rotate(-370deg);\n  }\n  100% {\n    transform: rotate(-360deg);\n  }\n}\n@keyframes spin3 {\n  0% {\n    transform: rotate(0deg);\n  }\n  27% {\n    transform: rotate(0deg);\n  }\n  40% {\n    transform: rotate(180deg);\n  }\n  45% {\n    transform: rotate(190deg);\n  }\n  50% {\n    transform: rotate(180deg);\n  }\n  62% {\n    transform: rotate(180deg);\n  }\n  75% {\n    transform: rotate(360deg);\n  }\n  80% {\n    transform: rotate(370deg);\n  }\n  85% {\n    transform: rotate(360deg);\n  }\n  100% {\n    transform: rotate(360deg);\n  }\n}\n@keyframes spin4 {\n  0% {\n    transform: rotate(0deg);\n  }\n  38% {\n    transform: rotate(0deg);\n  }\n  60% {\n    transform: rotate(-360deg);\n  }\n  65% {\n    transform: rotate(-370deg);\n  }\n  75% {\n    transform: rotate(-360deg);\n  }\n  100% {\n    transform: rotate(-360deg);\n  }\n}\n/*# sourceMappingURL=app.component.css.map */\n"] }]
  }], null, { resetIdleTimer: [{
    type: HostListener,
    args: ["document:click", ["$event"]]
  }, {
    type: HostListener,
    args: ["document:keypress", ["$event"]]
  }], sessionEndedDialog: [{
    type: ViewChild,
    args: ["sessionEndedDialog"]
  }] });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(AppComponent, { className: "AppComponent", filePath: "src/app/app.component.ts", lineNumber: 16 });
})();

// src/app/app.routes.ts
var routes = [
  { path: RouteMedia, redirectTo: RouteHome, pathMatch: "full" },
  { path: RouteHome, loadChildren: () => import("./chunk-KDSDJ3VX.js") },
  { path: `${RouteMedia}/:${RouteParamMediaId}`, loadChildren: () => import("./chunk-CTR4T5O6.js") },
  { path: RouteMovies, loadChildren: () => import("./chunk-KDSDJ3VX.js") },
  { path: RouteSeries, loadChildren: () => import("./chunk-KDSDJ3VX.js") },
  // {path: 'series/:id', loadChildren: () => import('./media/media-details/routes')},
  { path: RouteTasks, loadChildren: () => import("./chunk-GIP5ZCB2.js") },
  { path: RouteLogs, loadChildren: () => import("./chunk-X3CULKR6.js") },
  { path: RouteSettings, loadChildren: () => import("./chunk-GOLNWYFZ.js") },
  { path: "", redirectTo: RouteHome, pathMatch: "full" },
  { path: "**", redirectTo: "" }
];

// src/app/app.config.ts
var appConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding(), withPreloading(PreloadAllModules), withViewTransitions(), withInMemoryScrolling({ scrollPositionRestoration: "top", anchorScrolling: "enabled" })),
    provideHttpClient(),
    // withInterceptors([authInterceptor]),
    { provide: DATE_PIPE_DEFAULT_OPTIONS, useValue: { dateFormat: "medium", timezone: "UTC" } },
    importProvidersFrom(ApiModule.forRoot({ rootUrl: "" }), TimeagoModule.forRoot())
  ]
};

// src/main.ts
bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err));
//# sourceMappingURL=main.js.map
