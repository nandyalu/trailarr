import {
  ChangeDetectionStrategy,
  Component,
  HostBinding,
  setClassMetadata,
  ɵsetClassDebugInfo,
  ɵɵclassMap,
  ɵɵdefineComponent,
  ɵɵelement
} from "./chunk-FAGZ4ZSE.js";

// src/app/shared/load-indicator/load-indicator.component.ts
var LoadIndicatorComponent = class _LoadIndicatorComponent {
  constructor() {
    this.hostClass = "loading-wave";
  }
  static {
    this.\u0275fac = function LoadIndicatorComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _LoadIndicatorComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _LoadIndicatorComponent, selectors: [["app-load-indicator"]], hostVars: 2, hostBindings: function LoadIndicatorComponent_HostBindings(rf, ctx) {
      if (rf & 2) {
        \u0275\u0275classMap(ctx.hostClass);
      }
    }, decls: 4, vars: 0, consts: [[1, "loading-bar"]], template: function LoadIndicatorComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275element(0, "div", 0)(1, "div", 0)(2, "div", 0)(3, "div", 0);
      }
    }, encapsulation: 2, changeDetection: 0 });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(LoadIndicatorComponent, [{
    type: Component,
    args: [{
      selector: "app-load-indicator",
      template: `<div class="loading-bar"></div>
    <div class="loading-bar"></div>
    <div class="loading-bar"></div>
    <div class="loading-bar"></div>`,
      changeDetection: ChangeDetectionStrategy.OnPush,
      imports: []
    }]
  }], null, { hostClass: [{
    type: HostBinding,
    args: ["class"]
  }] });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(LoadIndicatorComponent, { className: "LoadIndicatorComponent", filePath: "src/app/shared/load-indicator/load-indicator.component.ts", lineNumber: 12 });
})();

export {
  LoadIndicatorComponent
};
//# sourceMappingURL=chunk-7SOVNULQ.js.map
