import {
  ProfileSelectDialogComponent
} from "./chunk-L4Z4F7TL.js";
import {
  MediaService,
  mapMedia
} from "./chunk-3ILQGILQ.js";
import {
  AddCustomFilterDialogComponent,
  CustomfilterService,
  DateFilterCondition,
  NumberFilterCondition,
  StringFilterCondition,
  booleanFilterKeys,
  dateFilterKeys,
  numberFilterKeys,
  stringFilterKeys
} from "./chunk-GVMLCJCM.js";
import "./chunk-J3HM2TW5.js";
import {
  Router,
  RouterLink
} from "./chunk-U5GO6X62.js";
import {
  WebsocketService
} from "./chunk-KIVIDEQ5.js";
import {
  FormsModule
} from "./chunk-BOQEVO5H.js";
import {
  LoadIndicatorComponent
} from "./chunk-7SOVNULQ.js";
import {
  Component,
  Directive,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  NgTemplateOutlet,
  Output,
  Pipe,
  ViewContainerRef,
  computed,
  inject,
  setClassMetadata,
  signal,
  viewChild,
  ɵsetClassDebugInfo,
  ɵɵadvance,
  ɵɵclassProp,
  ɵɵconditional,
  ɵɵdefineComponent,
  ɵɵdefineDirective,
  ɵɵdefinePipe,
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
  ɵɵpureFunction1,
  ɵɵqueryAdvance,
  ɵɵreference,
  ɵɵrepeater,
  ɵɵrepeaterCreate,
  ɵɵrepeaterTrackByIdentity,
  ɵɵresetView,
  ɵɵresolveWindow,
  ɵɵrestoreView,
  ɵɵsanitizeUrl,
  ɵɵtemplate,
  ɵɵtemplateRefExtractor,
  ɵɵtext,
  ɵɵtextInterpolate,
  ɵɵtextInterpolate1,
  ɵɵviewQuerySignal
} from "./chunk-FAGZ4ZSE.js";

// src/app/helpers/scroll-near-end-directive.ts
var ScrollNearEndDirective = class _ScrollNearEndDirective {
  constructor() {
    this.el = inject(ElementRef);
    this.nearEnd = new EventEmitter();
    this.threshold = 200;
  }
  ngOnInit() {
    this.window = window;
  }
  windowScrollEvent(event) {
    const heightOfWholePage = this.window.document.documentElement.scrollHeight;
    const heightOfElement = this.el.nativeElement.scrollHeight;
    const currentScrolledY = this.window.scrollY;
    const innerHeight = this.window.innerHeight;
    const spaceOfElementAndPage = heightOfWholePage - heightOfElement;
    const scrollToBottom = heightOfElement - innerHeight - currentScrolledY + spaceOfElementAndPage;
    if (scrollToBottom < this.threshold) {
      this.nearEnd.emit();
    }
  }
  static {
    this.\u0275fac = function ScrollNearEndDirective_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _ScrollNearEndDirective)();
    };
  }
  static {
    this.\u0275dir = /* @__PURE__ */ \u0275\u0275defineDirective({ type: _ScrollNearEndDirective, selectors: [["", "appScrollNearEnd", ""]], hostBindings: function ScrollNearEndDirective_HostBindings(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275listener("scroll", function ScrollNearEndDirective_scroll_HostBindingHandler($event) {
          return ctx.windowScrollEvent($event);
        }, false, \u0275\u0275resolveWindow);
      }
    }, inputs: { threshold: "threshold" }, outputs: { nearEnd: "nearEnd" } });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ScrollNearEndDirective, [{
    type: Directive,
    args: [{
      selector: "[appScrollNearEnd]",
      standalone: true
    }]
  }], null, { nearEnd: [{
    type: Output
  }], threshold: [{
    type: Input
  }], windowScrollEvent: [{
    type: HostListener,
    args: ["window:scroll", ["$event"]]
  }] });
})();

// src/app/media/pipes/display-title.pipe.ts
var DisplayTitlePipe = class _DisplayTitlePipe {
  /**
   * Formats the given title string by removing the substring '_at' and capitalizing the first letter.
   *
   * @param title - The title string to be formatted.
   * @returns The formatted option string with '_at' removed and the first letter capitalized.
   */
  transform(title) {
    title = title.replace("_at", "");
    return title.charAt(0).toUpperCase() + title.slice(1);
  }
  static {
    this.\u0275fac = function DisplayTitlePipe_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _DisplayTitlePipe)();
    };
  }
  static {
    this.\u0275pipe = /* @__PURE__ */ \u0275\u0275definePipe({ name: "displayTitle", type: _DisplayTitlePipe, pure: true });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(DisplayTitlePipe, [{
    type: Pipe,
    args: [{ name: "displayTitle", pure: true }]
  }], null, null);
})();

// src/app/media/media.component.ts
var _c0 = ["showFiltersDialog"];
var _c1 = (a0) => ({ media: a0 });
var _c2 = (a0) => ["/media", a0];
function MediaComponent_Conditional_0_For_15_Conditional_3_Conditional_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 19);
    \u0275\u0275element(1, "path", 29);
    \u0275\u0275elementEnd();
  }
}
function MediaComponent_Conditional_0_For_15_Conditional_3_Conditional_2_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 19);
    \u0275\u0275element(1, "path", 30);
    \u0275\u0275elementEnd();
  }
}
function MediaComponent_Conditional_0_For_15_Conditional_3_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div");
    \u0275\u0275template(1, MediaComponent_Conditional_0_For_15_Conditional_3_Conditional_1_Template, 2, 0, ":svg:svg", 19)(2, MediaComponent_Conditional_0_For_15_Conditional_3_Conditional_2_Template, 2, 0, ":svg:svg", 19);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(3);
    \u0275\u0275advance();
    \u0275\u0275conditional(ctx_r2.sortAscending() ? 1 : 2);
  }
}
function MediaComponent_Conditional_0_For_15_Template(rf, ctx) {
  if (rf & 1) {
    const _r4 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 28);
    \u0275\u0275listener("click", function MediaComponent_Conditional_0_For_15_Template_div_click_0_listener() {
      const sortOption_r5 = \u0275\u0275restoreView(_r4).$implicit;
      const ctx_r2 = \u0275\u0275nextContext(2);
      return \u0275\u0275resetView(ctx_r2.setMediaSort(sortOption_r5));
    });
    \u0275\u0275text(1);
    \u0275\u0275pipe(2, "displayTitle");
    \u0275\u0275template(3, MediaComponent_Conditional_0_For_15_Conditional_3_Template, 3, 1, "div");
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const sortOption_r5 = ctx.$implicit;
    const ctx_r2 = \u0275\u0275nextContext(2);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", \u0275\u0275pipeBind1(2, 2, sortOption_r5), " ");
    \u0275\u0275advance(2);
    \u0275\u0275conditional(ctx_r2.selectedSort() == sortOption_r5 ? 3 : -1);
  }
}
function MediaComponent_Conditional_0_For_24_Conditional_3_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div");
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 19);
    \u0275\u0275element(2, "path", 32);
    \u0275\u0275elementEnd()();
  }
}
function MediaComponent_Conditional_0_For_24_Template(rf, ctx) {
  if (rf & 1) {
    const _r6 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 31);
    \u0275\u0275listener("click", function MediaComponent_Conditional_0_For_24_Template_div_click_0_listener() {
      const filterOption_r7 = \u0275\u0275restoreView(_r6).$implicit;
      const ctx_r2 = \u0275\u0275nextContext(2);
      return \u0275\u0275resetView(ctx_r2.setMediaFilter(filterOption_r7));
    });
    \u0275\u0275text(1);
    \u0275\u0275pipe(2, "displayTitle");
    \u0275\u0275template(3, MediaComponent_Conditional_0_For_24_Conditional_3_Template, 3, 0, "div");
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const filterOption_r7 = ctx.$implicit;
    const ctx_r2 = \u0275\u0275nextContext(2);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", \u0275\u0275pipeBind1(2, 2, filterOption_r7), " ");
    \u0275\u0275advance(2);
    \u0275\u0275conditional(ctx_r2.selectedFilter() == filterOption_r7 ? 3 : -1);
  }
}
function MediaComponent_Conditional_0_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 3)(1, "div", 14);
    \u0275\u0275listener("click", function MediaComponent_Conditional_0_Template_div_click_1_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.inEditMode = true);
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(2, "svg", 15);
    \u0275\u0275element(3, "path", 16);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(4, "span");
    \u0275\u0275text(5, "Edit");
    \u0275\u0275elementEnd()();
    \u0275\u0275element(6, "div", 17);
    \u0275\u0275elementStart(7, "div", 18);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(8, "svg", 19);
    \u0275\u0275element(9, "path", 20);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(10, "div");
    \u0275\u0275text(11);
    \u0275\u0275pipe(12, "displayTitle");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(13, "div", 21);
    \u0275\u0275repeaterCreate(14, MediaComponent_Conditional_0_For_15_Template, 4, 4, "div", 22, \u0275\u0275repeaterTrackByIdentity);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(16, "div", 23);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(17, "svg", 19);
    \u0275\u0275element(18, "path", 24);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(19, "div");
    \u0275\u0275text(20);
    \u0275\u0275pipe(21, "displayTitle");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(22, "div", 25);
    \u0275\u0275repeaterCreate(23, MediaComponent_Conditional_0_For_24_Template, 4, 4, "div", 10, \u0275\u0275repeaterTrackByIdentity);
    \u0275\u0275elementStart(25, "div", 26);
    \u0275\u0275listener("click", function MediaComponent_Conditional_0_Template_div_click_25_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.openFilterDialog());
    });
    \u0275\u0275elementStart(26, "span");
    \u0275\u0275text(27, "Custom Filters");
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(28, "svg", 19);
    \u0275\u0275element(29, "path", 27);
    \u0275\u0275elementEnd()()()()();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275advance(11);
    \u0275\u0275textInterpolate(\u0275\u0275pipeBind1(12, 2, ctx_r2.selectedSort()));
    \u0275\u0275advance(3);
    \u0275\u0275repeater(ctx_r2.sortOptions);
    \u0275\u0275advance(6);
    \u0275\u0275textInterpolate(\u0275\u0275pipeBind1(21, 4, ctx_r2.selectedFilter()));
    \u0275\u0275advance(3);
    \u0275\u0275repeater(ctx_r2.allFilters());
  }
}
function MediaComponent_Conditional_1_Template(rf, ctx) {
  if (rf & 1) {
    const _r8 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 4)(1, "div", 33);
    \u0275\u0275listener("click", function MediaComponent_Conditional_1_Template_div_click_1_listener() {
      \u0275\u0275restoreView(_r8);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.batchUpdate("monitor"));
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(2, "svg", 34);
    \u0275\u0275element(3, "path", 35);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(4, "span");
    \u0275\u0275text(5, "Monitor");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(6, "div", 36);
    \u0275\u0275listener("click", function MediaComponent_Conditional_1_Template_div_click_6_listener() {
      \u0275\u0275restoreView(_r8);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.batchUpdate("unmonitor"));
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(7, "svg", 37);
    \u0275\u0275element(8, "path", 38);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(9, "span");
    \u0275\u0275text(10, "UnMonitor");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(11, "div", 39);
    \u0275\u0275listener("click", function MediaComponent_Conditional_1_Template_div_click_11_listener() {
      \u0275\u0275restoreView(_r8);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.openProfileSelectDialog());
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(12, "svg", 40);
    \u0275\u0275element(13, "path", 41);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(14, "span");
    \u0275\u0275text(15, "Download");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(16, "div", 42);
    \u0275\u0275listener("click", function MediaComponent_Conditional_1_Template_div_click_16_listener() {
      \u0275\u0275restoreView(_r8);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.batchUpdate("delete"));
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(17, "svg", 43);
    \u0275\u0275element(18, "path", 44);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(19, "span");
    \u0275\u0275text(20, "Delete");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(21, "div", 45);
    \u0275\u0275listener("click", function MediaComponent_Conditional_1_Template_div_click_21_listener() {
      \u0275\u0275restoreView(_r8);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.toggleEditMode(false));
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(22, "svg", 46);
    \u0275\u0275element(23, "path", 47);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(24, "span");
    \u0275\u0275text(25, "Cancel");
    \u0275\u0275elementEnd()();
    \u0275\u0275element(26, "div", 17);
    \u0275\u0275elementStart(27, "p", 48)(28, "span");
    \u0275\u0275text(29, "Selected: ");
    \u0275\u0275elementEnd();
    \u0275\u0275text(30);
    \u0275\u0275elementStart(31, "span");
    \u0275\u0275text(32);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(33, "div", 49);
    \u0275\u0275listener("click", function MediaComponent_Conditional_1_Template_div_click_33_listener() {
      \u0275\u0275restoreView(_r8);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.selectAll());
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(34, "svg", 50);
    \u0275\u0275element(35, "path", 51);
    \u0275\u0275elementEnd()();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(36, "div", 52);
    \u0275\u0275listener("click", function MediaComponent_Conditional_1_Template_div_click_36_listener() {
      \u0275\u0275restoreView(_r8);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.selectedMedia = []);
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(37, "svg", 50);
    \u0275\u0275element(38, "path", 53);
    \u0275\u0275elementEnd()()();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275advance(30);
    \u0275\u0275textInterpolate1(" ", ctx_r2.selectedMedia.length, " ");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1(" / ", ctx_r2.filteredSortedMedia().length, "");
  }
}
function MediaComponent_Conditional_3_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 6);
  }
}
function MediaComponent_Conditional_4_Conditional_0_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 6);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 55);
    \u0275\u0275element(2, "path", 56);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(3, "p");
    \u0275\u0275text(4, "No media items found matching the selected filter!");
    \u0275\u0275elementEnd()();
  }
}
function MediaComponent_Conditional_4_For_3_Conditional_0_ng_container_2_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function MediaComponent_Conditional_4_For_3_Conditional_0_Template(rf, ctx) {
  if (rf & 1) {
    const _r10 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 57)(1, "input", 59);
    \u0275\u0275listener("click", function MediaComponent_Conditional_4_For_3_Conditional_0_Template_input_click_1_listener($event) {
      \u0275\u0275restoreView(_r10);
      return \u0275\u0275resetView($event.stopPropagation());
    })("change", function MediaComponent_Conditional_4_For_3_Conditional_0_Template_input_change_1_listener($event) {
      \u0275\u0275restoreView(_r10);
      const media_r11 = \u0275\u0275nextContext().$implicit;
      const ctx_r2 = \u0275\u0275nextContext(2);
      return \u0275\u0275resetView(ctx_r2.onMediaSelected(media_r11, $event));
    });
    \u0275\u0275elementEnd();
    \u0275\u0275template(2, MediaComponent_Conditional_4_For_3_Conditional_0_ng_container_2_Template, 1, 0, "ng-container", 60);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const media_r11 = \u0275\u0275nextContext().$implicit;
    const ctx_r2 = \u0275\u0275nextContext(2);
    const mediaCard_r12 = \u0275\u0275reference(6);
    \u0275\u0275property("title", media_r11.title);
    \u0275\u0275advance();
    \u0275\u0275property("id", media_r11.id)("checked", ctx_r2.selectedMedia.includes(media_r11.id));
    \u0275\u0275advance();
    \u0275\u0275property("ngTemplateOutlet", mediaCard_r12)("ngTemplateOutletContext", \u0275\u0275pureFunction1(5, _c1, media_r11));
  }
}
function MediaComponent_Conditional_4_For_3_Conditional_1_ng_container_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function MediaComponent_Conditional_4_For_3_Conditional_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 58);
    \u0275\u0275template(1, MediaComponent_Conditional_4_For_3_Conditional_1_ng_container_1_Template, 1, 0, "ng-container", 60);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const media_r11 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275nextContext(2);
    const mediaCard_r12 = \u0275\u0275reference(6);
    \u0275\u0275property("routerLink", \u0275\u0275pureFunction1(5, _c2, media_r11.id))("title", media_r11.title)("id", media_r11.id);
    \u0275\u0275advance();
    \u0275\u0275property("ngTemplateOutlet", mediaCard_r12)("ngTemplateOutletContext", \u0275\u0275pureFunction1(7, _c1, media_r11));
  }
}
function MediaComponent_Conditional_4_For_3_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, MediaComponent_Conditional_4_For_3_Conditional_0_Template, 3, 7, "div", 57)(1, MediaComponent_Conditional_4_For_3_Conditional_1_Template, 2, 9, "div", 58);
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(2);
    \u0275\u0275conditional(ctx_r2.inEditMode ? 0 : 1);
  }
}
function MediaComponent_Conditional_4_Template(rf, ctx) {
  if (rf & 1) {
    const _r9 = \u0275\u0275getCurrentView();
    \u0275\u0275template(0, MediaComponent_Conditional_4_Conditional_0_Template, 5, 0, "div", 6);
    \u0275\u0275elementStart(1, "div", 54);
    \u0275\u0275listener("nearEnd", function MediaComponent_Conditional_4_Template_div_nearEnd_1_listener() {
      \u0275\u0275restoreView(_r9);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.onNearEndScroll());
    });
    \u0275\u0275repeaterCreate(2, MediaComponent_Conditional_4_For_3_Template, 2, 1, null, null, \u0275\u0275repeaterTrackByIdentity);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275conditional(ctx_r2.filteredSortedMedia().length === 0 ? 0 : -1);
    \u0275\u0275advance(2);
    \u0275\u0275repeater(ctx_r2.displayMedia());
  }
}
function MediaComponent_ng_template_5_Conditional_4_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 63)(1, "g", 66)(2, "path", 67);
    \u0275\u0275element(3, "animateTransform", 68);
    \u0275\u0275elementEnd()()();
  }
}
function MediaComponent_ng_template_5_Conditional_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 64);
    \u0275\u0275element(1, "path", 35);
    \u0275\u0275elementEnd();
  }
}
function MediaComponent_ng_template_5_Conditional_6_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 69);
    \u0275\u0275element(1, "path", 70);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const media_r14 = \u0275\u0275nextContext().media;
    \u0275\u0275classProp("success", media_r14.trailer_exists);
  }
}
function MediaComponent_ng_template_5_Template(rf, ctx) {
  if (rf & 1) {
    const _r13 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "label", 61)(1, "img", 62);
    \u0275\u0275listener("load", function MediaComponent_ng_template_5_Template_img_load_1_listener() {
      const media_r14 = \u0275\u0275restoreView(_r13).media;
      return \u0275\u0275resetView(media_r14.isImageLoaded = true);
    })("error", function MediaComponent_ng_template_5_Template_img_error_1_listener() {
      const media_r14 = \u0275\u0275restoreView(_r13).media;
      return \u0275\u0275resetView(media_r14.isImageLoaded = true);
    });
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(2, "p");
    \u0275\u0275text(3);
    \u0275\u0275elementEnd()();
    \u0275\u0275template(4, MediaComponent_ng_template_5_Conditional_4_Template, 4, 0, ":svg:svg", 63)(5, MediaComponent_ng_template_5_Conditional_5_Template, 2, 0, ":svg:svg", 64)(6, MediaComponent_ng_template_5_Conditional_6_Template, 2, 2, ":svg:svg", 65);
  }
  if (rf & 2) {
    const media_r14 = ctx.media;
    \u0275\u0275property("for", media_r14.id);
    \u0275\u0275advance();
    \u0275\u0275classProp("animated-gradient", !media_r14.isImageLoaded);
    \u0275\u0275propertyInterpolate1("id", "mediaImage", media_r14.id, "");
    \u0275\u0275property("src", media_r14.poster_path || "assets/poster-sm.png", \u0275\u0275sanitizeUrl)("alt", media_r14.title);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(media_r14.title);
    \u0275\u0275advance();
    \u0275\u0275conditional(media_r14.status.toLowerCase() == "downloading" ? 4 : media_r14.monitor ? 5 : 6);
  }
}
function MediaComponent_For_13_Template(rf, ctx) {
  if (rf & 1) {
    const _r15 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 10)(1, "span", 71);
    \u0275\u0275listener("click", function MediaComponent_For_13_Template_span_click_1_listener() {
      const filter_r16 = \u0275\u0275restoreView(_r15).$implicit;
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.openFilterEditDialog(filter_r16));
    });
    \u0275\u0275text(2);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(3, "svg", 72);
    \u0275\u0275listener("click", function MediaComponent_For_13_Template_svg_click_3_listener() {
      const filter_r16 = \u0275\u0275restoreView(_r15).$implicit;
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.deleteFilter(filter_r16.id));
    });
    \u0275\u0275element(4, "path", 44);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const filter_r16 = ctx.$implicit;
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1(" ", filter_r16.filter_name, " ");
  }
}
var MediaComponent = class _MediaComponent {
  constructor() {
    this.mediaService = inject(MediaService);
    this.router = inject(Router);
    this.webSocketService = inject(WebsocketService);
    this.viewContainerRef = inject(ViewContainerRef);
    this.customfilterService = inject(CustomfilterService);
    this.moviesOnly = signal(null);
    this.isLoading = signal(true);
    this.inEditMode = false;
    this.selectedMedia = [];
    this.sortOptions = ["title", "year", "added_at", "updated_at"];
    this.filterOptions = ["all", "downloaded", "downloading", "missing", "monitored", "unmonitored"];
    this.customFilters = signal([]);
    this.allFilters = computed(() => {
      return this.filterOptions.concat(this.customFilters().map((f) => f.filter_name));
    });
    this.selectedSort = signal("added_at");
    this.sortAscending = signal(true);
    this.selectedFilter = signal("all");
    this.defaultDisplayCount = 50;
    this.displayCount = signal(this.defaultDisplayCount);
    this.allMedia = signal([]);
    this.filteredSortedMedia = computed(() => this.computeFilteredNSortedMedia());
    this.displayMedia = computed(() => this.filteredSortedMedia().slice(0, this.displayCount()));
    this.lastUpdateTime = 0;
    this.UPDATE_INTERVAL = 3;
    this.filterDisplayed = false;
    this.showFiltersDialog = viewChild.required("showFiltersDialog");
  }
  ngOnInit() {
    this.isLoading.set(true);
    const state = this.router.routerState;
    const currentRoute = state.snapshot.url.toLowerCase();
    switch (currentRoute) {
      case "/movies":
        this.moviesOnly.set(true);
        break;
      case "/series":
        this.moviesOnly.set(false);
        break;
      default:
        this.moviesOnly.set(null);
        this.filterOptions = ["all", "movies", "series"];
        this.selectedFilter.set("all");
        this.selectedSort.set("updated_at");
        this.sortAscending.set(false);
    }
    this.retrieveSortNFilterOptions();
    let filterBy = this.moviesOnly() == null ? "downloaded" : "all";
    this.mediaService.fetchAllMedia(this.moviesOnly(), filterBy).subscribe((mediaList) => {
      this.allMedia.set(mediaList.map((media) => mapMedia(media)));
      this.isLoading.set(false);
    });
    this.webSocketService.toastMessage.subscribe(() => {
      this.fetchUpdatedMedia();
    });
    setTimeout(() => {
      this.fetchUpdatedMedia();
    }, 1e4);
  }
  applyFilter(filter, media) {
    let filterValue = filter.filter_value;
    let filterBy = filter.filter_by;
    if (booleanFilterKeys.includes(filterBy)) {
      let origValue = media[filterBy];
      let filterValueBool = filterValue.toLowerCase() === "true";
      return origValue === filterValueBool;
    }
    if (dateFilterKeys.includes(filterBy)) {
      let mediaDate = new Date(media[filterBy]);
      let filterDate = new Date(filterValue);
      switch (filter.filter_condition) {
        case DateFilterCondition.IS_AFTER:
          return mediaDate > filterDate;
        case DateFilterCondition.IS_BEFORE:
          return mediaDate < filterDate;
        case DateFilterCondition.IN_THE_LAST:
          let last = /* @__PURE__ */ new Date();
          last.setDate(last.getDate() - parseInt(filterValue));
          return mediaDate > last;
        case DateFilterCondition.NOT_IN_THE_LAST:
          let last2 = /* @__PURE__ */ new Date();
          last2.setDate(last2.getDate() - parseInt(filterValue));
          return mediaDate < last2;
        case DateFilterCondition.EQUALS:
          return mediaDate.getDate() === filterDate.getDate();
        case DateFilterCondition.NOT_EQUALS:
          return mediaDate.getDate() !== filterDate.getDate();
        default:
          return true;
      }
    }
    if (numberFilterKeys.includes(filterBy)) {
      let origValue = media[filterBy];
      let filterValueNum = parseInt(filterValue);
      switch (filter.filter_condition) {
        case NumberFilterCondition.GREATER_THAN:
          return origValue > filterValueNum;
        case NumberFilterCondition.GREATER_THAN_EQUAL:
          return origValue >= filterValueNum;
        case NumberFilterCondition.LESS_THAN:
          return origValue < filterValueNum;
        case NumberFilterCondition.LESS_THAN_EQUAL:
          return origValue <= filterValueNum;
        case NumberFilterCondition.EQUALS:
          return origValue === filterValueNum;
        case NumberFilterCondition.NOT_EQUALS:
          return origValue !== filterValueNum;
        default:
          return true;
      }
    }
    if (stringFilterKeys.includes(filterBy)) {
      let origValue = media[filterBy];
      switch (filter.filter_condition) {
        case StringFilterCondition.CONTAINS:
          return origValue.includes(filterValue);
        case StringFilterCondition.NOT_CONTAINS:
          return !origValue.includes(filterValue);
        case StringFilterCondition.EQUALS:
          return origValue === filterValue;
        case StringFilterCondition.NOT_EQUALS:
          return origValue !== filterValue;
        case StringFilterCondition.STARTS_WITH:
          return origValue.startsWith(filterValue);
        case StringFilterCondition.NOT_STARTS_WITH:
          return !origValue.startsWith(filterValue);
        case StringFilterCondition.ENDS_WITH:
          return origValue.endsWith(filterValue);
        case StringFilterCondition.NOT_ENDS_WITH:
          return !origValue.endsWith(filterValue);
        case StringFilterCondition.IS_EMPTY:
          return origValue === "";
        case StringFilterCondition.IS_NOT_EMPTY:
          return origValue !== "";
        default:
          return true;
      }
    }
    return true;
  }
  applyCustomFilter(filter_name, media) {
    let customFilter = this.customFilters().find((f) => f.filter_name === filter_name);
    if (!this.filterDisplayed) {
      this.filterDisplayed = true;
    }
    if (!customFilter) {
      return true;
    }
    return customFilter.filters.every((filter) => this.applyFilter(filter, media));
  }
  /**
   * Filters and sorts the media list based on the selected filter and sort options.
   *
   * @returns {Media[]} The filtered and sorted media list.
   */
  computeFilteredNSortedMedia() {
    this.lastUpdateTime = Date.now();
    let mediaList = this.allMedia().filter((media) => {
      switch (this.selectedFilter()) {
        case "all":
          return true;
        case "downloaded":
          return media.trailer_exists;
        case "downloading":
          return media.status.toLowerCase() === "downloading";
        case "missing":
          return !media.trailer_exists;
        case "monitored":
          return media.monitor;
        case "unmonitored":
          return !media.monitor && !media.trailer_exists;
        case "movies":
          return media.is_movie && media.trailer_exists;
        case "series":
          return !media.is_movie && media.trailer_exists;
        default:
          return this.applyCustomFilter(this.selectedFilter(), media);
      }
    });
    mediaList.sort((a, b) => {
      let aVal = a[this.selectedSort()];
      let bVal = b[this.selectedSort()];
      if (aVal instanceof Date && bVal instanceof Date) {
        if (this.sortAscending()) {
          return aVal.getTime() - bVal.getTime();
        }
        return bVal.getTime() - aVal.getTime();
      }
      if (typeof aVal === "number" && typeof bVal === "number") {
        if (this.sortAscending()) {
          return aVal - bVal;
        }
        return bVal - aVal;
      }
      if (this.sortAscending()) {
        return a[this.selectedSort()].toString().localeCompare(b[this.selectedSort()].toString());
      }
      return b[this.selectedSort()].toString().localeCompare(a[this.selectedSort()].toString());
    });
    return mediaList;
  }
  /**
   * Fetches updated media items from the server and updates the allMedia signal.
   *
   * @param {boolean} forceUpdate - Whether to force an update regardless of
   * the time interval.
   *
   * @returns {void}
   */
  fetchUpdatedMedia(forceUpdate = false) {
    const currentTime = Date.now();
    const delta = Math.min(Math.floor(Math.abs(currentTime - this.lastUpdateTime) / 1e3), 1e3);
    if (delta > this.UPDATE_INTERVAL || forceUpdate) {
      this.mediaService.fetchUpdatedMedia(delta).subscribe((mediaList) => {
        let updatedMedia = mediaList.map((media) => mapMedia(media));
        this.allMedia.update((existingMedia) => {
          return existingMedia.map((media) => {
            let updated = updatedMedia.find((m) => m.id === media.id);
            if (updated) {
              return updated;
            }
            return media;
          });
        });
      });
      this.lastUpdateTime = currentTime;
    }
  }
  /**
   * Toggles the edit mode for the media list.
   *
   * @param {boolean} enabled - Whether to enable or disable edit mode.
   * @returns {void}
   */
  toggleEditMode(enabled) {
    this.inEditMode = enabled;
  }
  selectAll() {
    this.selectedMedia = this.filteredSortedMedia().map((media) => media.id);
  }
  /**
   * Handles the event when a media item is selected, either by checking or unchecking a checkbox.
   * Adds or removes the media item from the selectedMedia array based on the checkbox state.
   *
   * @param {Media} media - The media item that was selected.
   * @param {Event} event - The event that triggered the selection.
   * @returns {void}
   */
  onMediaSelected(media, event) {
    const inputElement = event.target;
    if (inputElement.checked) {
      this.selectedMedia.push(media.id);
    } else {
      this.selectedMedia = this.selectedMedia.filter((id) => id !== media.id);
    }
  }
  openProfileSelectDialog() {
    const dialogRef = this.viewContainerRef.createComponent(ProfileSelectDialogComponent);
    dialogRef.instance.onSubmit.subscribe((profileId) => {
      this.batchUpdate("download", profileId);
      dialogRef.destroy();
    });
    dialogRef.instance.onClosed.subscribe(() => {
      dialogRef.destroy();
    });
  }
  /**
   * Handles the batch update action for the selected media items.
   *
   * @param {string} action
   * The action to perform on the selected media items. Available actions are:
   * - `monitor`: Monitor the selected media items.
   * - `unmonitor`: Unmonitor the selected media items.
   * - `delete`: Delete the trailers for the selected media items.
   * - `download`: Download the trailers for the selected media items.
   * @param {number} profileID
   * The ID of the profile to use for the download action. \
   * Defaults to `-1` if not provided. \
   * Only required for `download` action.
   * @returns {void}
   */
  batchUpdate(action, profileID = -1) {
    this.webSocketService.showToast(`Batch update: ${action} ${this.selectedMedia.length} items`);
    this.mediaService.batchUpdate(this.selectedMedia, action, profileID).subscribe(() => {
      this.fetchUpdatedMedia(true);
    });
    this.selectedMedia = [];
  }
  /**
   * Retrieves the sort and filter options from the local session.
   * If no options are found, sets the default sort option to 'added_at' and the default filter option to 'all'.
   *
   * - The sort option is stored with the key `Trailarr{pageType}Sort`.
   * - The sort order is stored with the key `Trailarr{pageType}SortAscending`.
   * - The filter option is stored with the key `Trailarr{pageType}Filter`.
   *
   * @returns {void} This method does not return a value.
   */
  retrieveSortNFilterOptions() {
    const moviesOnlyValue = this.moviesOnly();
    const pageType = moviesOnlyValue == null ? "AllMedia" : moviesOnlyValue ? "Movies" : "Series";
    this.customfilterService.getViewFilters(moviesOnlyValue).subscribe((filters) => {
      this.customFilters.set(filters);
    });
    let filterOption = localStorage.getItem(`Trailarr${pageType}Filter`);
    if (filterOption) {
      this.selectedFilter.set(filterOption);
    }
    let sortOption = localStorage.getItem(`Trailarr${pageType}Sort`);
    let sortAscending = localStorage.getItem(`Trailarr${pageType}SortAscending`);
    if (sortOption) {
      this.selectedSort.set(sortOption);
    }
    if (sortAscending) {
      this.sortAscending.set(sortAscending == "true");
    }
  }
  /**
   * Sets the media sort option and resets the display count to the default.
   * Also, saves the sort option to the local session.
   * If the same sort option is selected, toggles the sort direction.
   *
   * @param sortBy - The sort option to set.
   * @returns {void} This method does not return a value.
   */
  setMediaSort(sortBy) {
    this.selectedMedia = [];
    this.displayCount.set(this.defaultDisplayCount);
    if (this.selectedSort() === sortBy) {
      this.sortAscending.set(!this.sortAscending());
    } else {
      this.selectedSort.set(sortBy);
      this.sortAscending.set(true);
    }
    const moviesOnly = this.moviesOnly();
    const pageType = moviesOnly == null ? "AllMedia" : moviesOnly ? "Movies" : "Series";
    localStorage.setItem(`Trailarr${pageType}Sort`, this.selectedSort());
    localStorage.setItem(`Trailarr${pageType}SortAscending`, this.sortAscending().toString());
    return;
  }
  /**
   * Sets the media filter option and resets the display count to the default.
   *
   * @param filterBy - The filter option to set.
   * @returns {void} This method does not return a value.
   */
  setMediaFilter(filterBy) {
    this.selectedMedia = [];
    this.displayCount.set(this.defaultDisplayCount);
    this.selectedFilter.set(filterBy);
    const moviesOnly = this.moviesOnly();
    const pageType = moviesOnly == null ? "AllMedia" : moviesOnly ? "Movies" : "Series";
    localStorage.setItem(`Trailarr${pageType}Filter`, this.selectedFilter());
    return;
  }
  /**
   * Handles the event when the user scrolls near the end of the media list.
   * Loads more media items into the display list if there are more items to show.
   *
   * @returns {void} This method does not return a value.
   */
  onNearEndScroll() {
    if (this.displayCount() >= this.filteredSortedMedia().length) {
      return;
    }
    this.displayCount.update((count) => count + this.defaultDisplayCount);
  }
  openFilterDialog() {
    if (this.customFilters().length === 0) {
      this.openFilterEditDialog(null);
    } else {
      this.showFiltersDialog().nativeElement.showModal();
    }
  }
  openFilterEditDialog(filter) {
    this.showFiltersDialog().nativeElement.close();
    const dialogRef = this.viewContainerRef.createComponent(AddCustomFilterDialogComponent);
    dialogRef.setInput("customFilter", filter);
    dialogRef.setInput("filterType", this.moviesOnly() == null ? "HOME" : this.moviesOnly() ? "MOVIES" : "SERIES");
    dialogRef.instance.dialogClosed.subscribe(() => {
      this.retrieveSortNFilterOptions();
      dialogRef.destroy();
    });
  }
  deleteFilter(filter_id) {
    this.customfilterService.delete(filter_id).subscribe(() => {
      this.customFilters.update((filters) => {
        return filters.filter((f) => f.id !== filter_id);
      });
    });
  }
  closeFilterDialog() {
    this.showFiltersDialog().nativeElement.close();
    this.retrieveSortNFilterOptions();
  }
  static {
    this.\u0275fac = function MediaComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _MediaComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _MediaComponent, selectors: [["app-media2"]], viewQuery: function MediaComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuerySignal(ctx.showFiltersDialog, _c0, 5);
      }
      if (rf & 2) {
        \u0275\u0275queryAdvance();
      }
    }, decls: 21, vars: 2, consts: [["mediaCard", ""], ["showFiltersDialog", ""], ["dialogContainer", ""], [1, "media-header"], [1, "media-header", "edit"], [1, "media-container"], [1, "center"], [3, "close"], [1, "dialog-content", 3, "click"], [1, "dialog-title"], [1, "filteritem-dropdown-option"], [1, "buttons-row"], [1, "danger", 3, "click"], [1, "primary", 3, "click"], ["aria-label", "Edit", "title", "Edit", 1, "media-header-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", 1, "button-icon"], ["d", "M640-160v-360H160v360h480Zm80-200v-80h80v-360H320v200h-80v-200q0-33 23.5-56.5T320-880h480q33 0 56.5 23.5T880-800v360q0 33-23.5 56.5T800-360h-80ZM160-80q-33 0-56.5-23.5T80-160v-360q0-33 23.5-56.5T160-600h480q33 0 56.5 23.5T720-520v360q0 33-23.5 56.5T640-80H160Zm400-603ZM400-340Z"], [1, "empty-space"], [1, "media-header-sortitem"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", 1, "icon"], ["d", "M74-159v-135h304v135H74Zm0-255v-134h558v134H74Zm0-254v-135h812v135H74Z"], [1, "sortitem-dropdown"], [1, "sortitem-dropdown-option"], [1, "media-header-filteritem"], ["d", "M371-158v-135h219v135H371ZM200-413v-135h558v135H200ZM74-668v-135h812v135H74Z"], [1, "filteritem-dropdown"], ["aria-label", "CustomFilters", "title", "Edit", 1, "filteritem-dropdown-option", 3, "click"], ["d", "M421-97v-248h83v83h353v83H504v82h-83Zm-318-82v-83h270v83H103Zm187-178v-82H103v-82h187v-84h83v248h-83Zm131-82v-82h436v82H421Zm166-176v-248h83v82h187v83H670v83h-83Zm-484-83v-83h436v83H103Z"], [1, "sortitem-dropdown-option", 3, "click"], ["d", "M480-130 200-410l96-96 184 185 184-185 96 96-280 280Zm0-299L200-708l96-97 184 185 184-185 96 97-280 279Z"], ["d", "m296-155-96-97 280-279 280 279-96 97-184-185-184 185Zm0-299-96-96 280-280 280 280-96 96-184-185-184 185Z"], [1, "filteritem-dropdown-option", 3, "click"], ["d", "M382-200 113-469l97-97 172 173 369-369 97 96-466 466Z"], ["aria-label", "Monitor", "title", "Monitor", 1, "media-header-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Monitor", 1, "button-icon"], ["d", "M713-600 600-713l56-57 57 57 141-142 57 57-198 198ZM200-120v-640q0-33 23.5-56.5T280-840h280q-20 30-30 57.5T520-720q0 72 45.5 127T680-524q23 3 40 3t40-3v404L480-240 200-120Z"], ["aria-label", "UnMonitor", "title", "UnMonitor", 1, "media-header-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "UnMonitor", 1, "button-icon"], ["d", "M200-120v-640q0-33 23.5-56.5T280-840h240v80H280v518l200-86 200 86v-278h80v400L480-240 200-120Zm80-640h240-240Zm400 160v-80h-80v-80h80v-80h80v80h80v80h-80v80h-80Z"], ["aria-label", "Download", "title", "Download", 1, "media-header-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Download", 1, "button-icon"], ["d", "M480-320 280-520l56-58 104 104v-326h80v326l104-104 56 58-200 200ZM240-160q-33 0-56.5-23.5T160-240v-120h80v120h480v-120h80v120q0 33-23.5 56.5T720-160H240Z"], ["aria-label", "Delete", "title", "Delete", 1, "media-header-button", "delete", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Delete", 1, "button-icon"], ["d", "M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"], ["aria-label", "Cancel", "title", "Cancel", 1, "media-header-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Cancel", 1, "button-icon"], ["d", "M819-28 407-440H160v280h480v-161l80 80v81q0 33-23.5 56.5T640-80H160q-33 0-56.5-23.5T80-160v-360q0-33 23.5-56.5T160-600h80v-7L27-820l57-57L876-85l-57 57Zm-99-327-80-80-165-165h165q33 0 56.5 23.5T720-520v80h80v-280H355L246-829q8-23 28.5-37t45.5-14h480q33 0 56.5 23.5T880-800v360q0 33-23.5 56.5T800-360h-80v5Z"], [1, "count"], ["aria-label", "Select All", "title", "Select All", 1, "media-header-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Clear", 1, "button-icon"], ["d", "M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q8 0 15 1.5t14 4.5l-74 74H200v560h560v-266l80-80v346q0 33-23.5 56.5T760-120H200Zm261-160L235-506l56-56 170 170 367-367 57 55-424 424Z"], ["aria-label", "Clear", "title", "Clear", 1, "media-header-button", 3, "click"], ["d", "m500-120-56-56 142-142-142-142 56-56 142 142 142-142 56 56-142 142 142 142-56 56-142-142-142 142Zm-220 0v-80h80v80h-80Zm-80-640h-80q0-33 23.5-56.5T200-840v80Zm80 0v-80h80v80h-80Zm160 0v-80h80v80h-80Zm160 0v-80h80v80h-80Zm160 0v-80q33 0 56.5 23.5T840-760h-80ZM200-200v80q-33 0-56.5-23.5T120-200h80Zm-80-80v-80h80v80h-80Zm0-160v-80h80v80h-80Zm0-160v-80h80v80h-80Zm640 0v-80h80v80h-80Z"], ["appScrollNearEnd", "", 1, "media-row", 3, "nearEnd"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", 1, "empty-icon"], ["d", "M215.38-160q-23.05 0-39.22-16.16Q160-192.33 160-215.38v-529.24q0-23.05 16.16-39.22Q192.33-800 215.38-800h529.24q23.05 0 39.22 16.16Q800-767.67 800-744.62V-418q-7.33-4.55-15.4-7.82-8.08-3.27-15.37-6.8v-185.84H495.38v201.61q-10.84 6.39-22.26 13.54-11.43 7.16-21.89 14.85H190.77v173.08q0 10.76 6.92 17.69 6.93 6.92 17.69 6.92h128.16q6.15 8.54 12.42 16.12 6.27 7.57 12.66 14.65H215.38Zm-24.61-259.23h273.85v-199.23H190.77v199.23Zm0-230h578.46v-95.39q0-10.76-6.92-17.69-6.93-6.92-17.69-6.92H215.38q-10.76 0-17.69 6.92-6.92 6.93-6.92 17.69v95.39ZM480-480Zm0 0Zm0 0Zm0 0ZM650.37-98.46q-71.22 0-131.91-36.54t-97.23-97.31q36.54-60.77 97.23-97.31 60.69-36.53 132.16-36.53 71.46 0 131.76 36.53 60.31 36.54 97.62 97.81-36.08 61.27-97.25 97.31T650.37-98.46Zm.25-30.77q57.76 0 108.07-28.35 50.31-28.34 85.08-74.73-34.77-46.38-84.9-74.73-50.12-28.34-108.64-28.34-57.38 0-108.08 28.34-50.69 28.35-84.69 74.73 34 46.39 84.69 74.73 50.7 28.35 108.47 28.35Zm-.12-67.69q-15.12 0-25.38-10.44-10.27-10.43-10.27-25.11t10.42-24.95q10.41-10.27 25.08-10.27 15.5 0 25.38 10.43 9.89 10.43 9.89 25.12 0 14.68-10.01 24.95-10 10.27-25.11 10.27Z"], [1, "media-card", 3, "title"], [1, "media-card", 3, "routerLink", "title", "id"], ["type", "checkbox", 1, "media-card-checkbox", 3, "click", "change", "id", "checked"], [4, "ngTemplateOutlet", "ngTemplateOutletContext"], [3, "for"], ["loading", "lazy", 3, "load", "error", "id", "src", "alt"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Downloading", 1, "monitored-icon"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Monitored", 1, "monitored-icon"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Trailer Exists", 1, "downloaded-icon", 3, "success"], ["transform", "scale(0.9) translate(65,-60)"], ["d", "M343 -107q-120 -42 -194.5 -146.5T74 -490q0 -29 4 -57.5T91 -604l-57 33 -37 -62 185 -107 106 184 -63 36 -54 -92q-13 30 -18.5 60.5T147 -490q0 113 65.5 200T381 -171zm291 -516v-73h107q-47 -60 -115.5 -93.5T480 -823q-66 0 -123.5 24T255 -734l-38 -65q54 -45 121 -71t142 -26q85 0 160.5 33T774 -769v-67h73v213zM598 -1 413 -107l107 -184 62 37 -54 94q123 -17 204.5 -110.5T814 -489q0 -19 -2.5 -37.5T805 -563h74q4 18 6 36.5t2 36.5q0 142 -87 251.5T578 -96l56 33z"], ["attributeName", "transform", "type", "rotate", "from", "0 470 -480", "to", "360 470 -480", "dur", "5", "repeatCount", "indefinite"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Trailer Exists", 1, "downloaded-icon"], ["d", "M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q65 0 123 19t107 53l-58 59q-38-24-81-37.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160q133 0 226.5-93.5T800-480q0-18-2-36t-6-35l65-65q11 32 17 66t6 70q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm-56-216L254-466l56-56 114 114 400-401 56 56-456 457Z"], ["title", "Edit Custom Filter", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Delete", "title", "Delete Custom Filter", 1, "icon", "delete-icon", 3, "click"]], template: function MediaComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275template(0, MediaComponent_Conditional_0_Template, 30, 6, "div", 3)(1, MediaComponent_Conditional_1_Template, 39, 2, "div", 4);
        \u0275\u0275elementStart(2, "div", 5);
        \u0275\u0275template(3, MediaComponent_Conditional_3_Template, 1, 0, "app-load-indicator", 6)(4, MediaComponent_Conditional_4_Template, 4, 1);
        \u0275\u0275elementEnd();
        \u0275\u0275template(5, MediaComponent_ng_template_5_Template, 7, 9, "ng-template", null, 0, \u0275\u0275templateRefExtractor);
        \u0275\u0275elementStart(7, "dialog", 7, 1);
        \u0275\u0275listener("close", function MediaComponent_Template_dialog_close_7_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeFilterDialog());
        });
        \u0275\u0275elementStart(9, "div", 8);
        \u0275\u0275listener("click", function MediaComponent_Template_div_click_9_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(10, "div", 9);
        \u0275\u0275text(11, "Custom Filters");
        \u0275\u0275elementEnd();
        \u0275\u0275repeaterCreate(12, MediaComponent_For_13_Template, 5, 1, "div", 10, \u0275\u0275repeaterTrackByIdentity);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(14, "div", 11)(15, "button", 12);
        \u0275\u0275listener("click", function MediaComponent_Template_button_click_15_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeFilterDialog());
        });
        \u0275\u0275text(16, "Cancel");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(17, "button", 13);
        \u0275\u0275listener("click", function MediaComponent_Template_button_click_17_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.openFilterEditDialog(null));
        });
        \u0275\u0275text(18, "Add New");
        \u0275\u0275elementEnd()()();
        \u0275\u0275element(19, "template", null, 2);
      }
      if (rf & 2) {
        \u0275\u0275conditional(!ctx.inEditMode ? 0 : 1);
        \u0275\u0275advance(3);
        \u0275\u0275conditional(ctx.isLoading() ? 3 : 4);
        \u0275\u0275advance(9);
        \u0275\u0275repeater(ctx.customFilters());
      }
    }, dependencies: [FormsModule, NgTemplateOutlet, LoadIndicatorComponent, RouterLink, ScrollNearEndDirective, DisplayTitlePipe], styles: ['\n\n.media-header[_ngcontent-%COMP%] {\n  display: flex;\n  position: sticky;\n  top: 76px;\n  width: 100%;\n  justify-content: flex-end;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  align-items: center;\n  padding: 0 1rem;\n  z-index: 99;\n}\n@media (width < 765px) {\n  .media-header[_ngcontent-%COMP%] {\n    position: fixed;\n    top: auto;\n    bottom: 78px;\n    left: 0;\n    right: 0;\n  }\n}\n.media-header[_ngcontent-%COMP%]   .empty-space[_ngcontent-%COMP%] {\n  flex: 1;\n  margin: auto;\n}\n.edit[_ngcontent-%COMP%] {\n  justify-content: flex-start;\n  gap: 1rem;\n}\n@media (width < 765px) {\n  .edit[_ngcontent-%COMP%] {\n    gap: 0.5rem;\n  }\n}\n.edit[_ngcontent-%COMP%]   .count[_ngcontent-%COMP%] {\n  font-weight: bold;\n  color: var(--color-primary);\n}\n@media (width < 765px) {\n  .edit[_ngcontent-%COMP%]   .count[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n    display: none;\n  }\n}\n.media-header-button[_ngcontent-%COMP%] {\n  display: flex;\n  align-items: center;\n  font-weight: bold;\n  cursor: pointer;\n  padding: 0.75rem 0;\n}\n.media-header-button[_ngcontent-%COMP%]   .button-icon[_ngcontent-%COMP%] {\n  width: 2.25rem;\n  height: 2.25rem;\n  font-size: 0;\n  margin: 0;\n  padding: 0.25rem;\n  fill: var(--color-on-surface);\n}\n@media (width < 765px) {\n  .media-header-button[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n    display: none;\n  }\n}\n.media-header-button[_ngcontent-%COMP%]:hover:not(.delete) {\n  color: var(--color-primary);\n}\n.media-header-button[_ngcontent-%COMP%]:hover:not(.delete)   svg[_ngcontent-%COMP%] {\n  fill: var(--color-primary) !important;\n}\n.delete[_ngcontent-%COMP%] {\n  color: var(--color-error);\n}\n.delete[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  fill: var(--color-error) !important;\n}\n.media-header-sortitem[_ngcontent-%COMP%], \n.media-header-filteritem[_ngcontent-%COMP%] {\n  position: relative;\n  display: flex;\n  flex-wrap: nowrap;\n  align-items: center;\n  justify-content: flex-start;\n  cursor: pointer;\n  font-weight: bold;\n  padding: 1rem;\n  gap: 0.5rem;\n}\n.icon[_ngcontent-%COMP%] {\n  margin: 0;\n}\n.empty-icon[_ngcontent-%COMP%] {\n  width: 100%;\n  height: clamp(10rem, 25vh, 30rem);\n  fill: var(--color-on-surface);\n}\n.media-header-sortitem[_ngcontent-%COMP%]:hover, \n.media-header-filteritem[_ngcontent-%COMP%]:hover, \n.media-header-button[_ngcontent-%COMP%]:hover {\n  background-color: var(--color-surface-container-highest);\n}\n.sortitem-dropdown[_ngcontent-%COMP%], \n.filteritem-dropdown[_ngcontent-%COMP%] {\n  display: none;\n  position: absolute;\n  min-width: 8rem;\n  top: 3.5rem;\n  right: 0;\n  background-color: var(--color-surface-container-highest);\n  z-index: 100;\n  box-shadow: 0.5rem 1rem 1rem 0px var(--color-shadow);\n}\n@media (width < 765px) {\n  .sortitem-dropdown[_ngcontent-%COMP%], \n   .filteritem-dropdown[_ngcontent-%COMP%] {\n    top: auto;\n    bottom: 3.5rem;\n    box-shadow: 0.5rem -1rem 1rem 0 var(--color-shadow);\n  }\n}\n.filteritem-dropdown[_ngcontent-%COMP%] {\n  min-width: 11rem;\n}\n.media-header-sortitem[_ngcontent-%COMP%]:hover   .sortitem-dropdown[_ngcontent-%COMP%], \n.media-header-filteritem[_ngcontent-%COMP%]:hover   .filteritem-dropdown[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n}\n.sortitem-dropdown-option[_ngcontent-%COMP%], \n.filteritem-dropdown-option[_ngcontent-%COMP%] {\n  display: flex;\n  cursor: pointer;\n  align-items: center;\n  justify-content: space-between;\n  gap: 0.5rem;\n  font-weight: 400;\n  height: 2.75rem;\n  padding: 0.5rem 0.25rem 0.5rem 0.75rem;\n}\n.sortitem-dropdown-option[_ngcontent-%COMP%]   span[_ngcontent-%COMP%], \n.filteritem-dropdown-option[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n  text-align: left;\n  flex: 1;\n}\n.sortitem-dropdown-option[_ngcontent-%COMP%]:hover, \n.filteritem-dropdown-option[_ngcontent-%COMP%]:hover {\n  background-color: var(--color-secondary-container);\n  color: var(--color-primary);\n}\n.media-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  overflow-y: auto;\n}\n@media (width < 765px) {\n  .media-container[_ngcontent-%COMP%] {\n    margin-bottom: 80px;\n  }\n}\n.text-center[_ngcontent-%COMP%] {\n  text-align: center;\n}\n.center[_ngcontent-%COMP%] {\n  margin: auto;\n  align-content: center;\n  min-height: 70vh;\n}\n.media-row[_ngcontent-%COMP%] {\n  display: grid;\n  grid-template-columns: repeat(auto-fill, minmax(min(180px, 100%), 1fr));\n  gap: 1rem;\n  padding: 1rem;\n}\n@media (width < 900px) {\n  .media-row[_ngcontent-%COMP%] {\n    grid-template-columns: repeat(auto-fill, minmax(min(120px, 100%), 1fr));\n    gap: 0.5rem;\n    padding: 0.5rem;\n  }\n}\n.media-card[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  transition: all 0.4s;\n  border-radius: 10px;\n  cursor: pointer;\n  position: relative;\n  overflow: hidden;\n  background-image: url("./media/poster-sm.png");\n  background-repeat: no-repeat;\n  background-size: cover;\n}\n.media-card[_ngcontent-%COMP%]   label[_ngcontent-%COMP%] {\n  cursor: pointer;\n  display: flex;\n  flex-direction: column;\n}\n.media-card-checkbox[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 0.5rem;\n  left: 0.5rem;\n  width: 1.5rem;\n  height: 1.5rem;\n  background-color: var(--color-surface-container-high);\n  outline: 2px solid var(--color-primary);\n}\n@media (width < 765px) {\n  .media-card-checkbox[_ngcontent-%COMP%] {\n    top: 0.25rem;\n    left: 0.25rem;\n    width: 1rem;\n    height: 1rem;\n  }\n}\n.media-card-checkbox[_ngcontent-%COMP%]:checked {\n  outline: none;\n  accent-color: var(--color-primary);\n}\n.media-card-checkbox[_ngcontent-%COMP%]:checked    + label[_ngcontent-%COMP%] {\n  border: 4px solid var(--color-primary);\n  border-radius: 10px;\n}\n.media-card[_ngcontent-%COMP%]   label[_ngcontent-%COMP%]   p[_ngcontent-%COMP%] {\n  width: 100%;\n  text-align: center;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-primary);\n  padding: 0.5rem 0;\n  margin: 0;\n  white-space: nowrap;\n  overflow: hidden;\n  text-overflow: ellipsis;\n  border-radius: 0 0 6px 6px;\n}\n.animated-gradient[_ngcontent-%COMP%] {\n  animation: _ngcontent-%COMP%_animateBg 2s linear infinite;\n  background-image:\n    linear-gradient(\n      135deg,\n      var(--color-surface-container-highest),\n      var(--color-surface-container-low),\n      var(--color-surface-container-highest),\n      var(--color-surface-container-low));\n  background-size: 100% 450%;\n}\n@keyframes _ngcontent-%COMP%_animateBg {\n  0% {\n    background-position: 0% 100%;\n  }\n  100% {\n    background-position: 0% 0%;\n  }\n}\n.media-card[_ngcontent-%COMP%]   img[_ngcontent-%COMP%] {\n  object-fit: cover;\n  overflow: hidden;\n  width: 100%;\n  aspect-ratio: 2/3;\n  border-radius: 6px 6px 0 0;\n}\n.media-card[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 5px;\n  height: 24px;\n  width: 24px;\n}\n.media-card[_ngcontent-%COMP%]   .monitored-icon[_ngcontent-%COMP%], \n.media-card[_ngcontent-%COMP%]   .downloaded-icon[_ngcontent-%COMP%] {\n  fill: var(--color-info);\n  right: 5px;\n}\n.media-card[_ngcontent-%COMP%]   .success[_ngcontent-%COMP%] {\n  fill: var(--color-success);\n}\n.media-card[_ngcontent-%COMP%]   h5[_ngcontent-%COMP%] {\n  display: none;\n}\n.media-card[_ngcontent-%COMP%]:hover {\n  box-shadow: 0px 0px 10px 5px var(--color-outline);\n}\n.dialog-content[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n  padding: 1rem;\n  min-width: max(25vw, min(300px, 80vw));\n}\n.dialog-content[_ngcontent-%COMP%]    > *[_ngcontent-%COMP%] {\n  border-bottom: 1px solid var(--color-outline);\n}\n.dialog-title[_ngcontent-%COMP%] {\n  font-size: larger;\n  font-weight: 700;\n  border-bottom: none !important;\n  padding-bottom: 0.5rem;\n  margin: 1rem;\n}\n.delete-icon[_ngcontent-%COMP%] {\n  fill: var(--color-error);\n  width: 2rem;\n  height: 2rem;\n}\n.buttons-row[_ngcontent-%COMP%] {\n  display: block flex;\n  align-items: center;\n  justify-content: space-around;\n  padding: 1rem 0;\n}\n/*# sourceMappingURL=media.component.css.map */'] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(MediaComponent, [{
    type: Component,
    args: [{ selector: "app-media2", imports: [FormsModule, NgTemplateOutlet, LoadIndicatorComponent, RouterLink, ScrollNearEndDirective, DisplayTitlePipe], template: `@if (!inEditMode) {
  <div class="media-header">
    <!-- Edit Button -->
    <div class="media-header-button" (click)="inEditMode = true" aria-label="Edit" title="Edit">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="button-icon">
        <path
          d="M640-160v-360H160v360h480Zm80-200v-80h80v-360H320v200h-80v-200q0-33 23.5-56.5T320-880h480q33 0 56.5 23.5T880-800v360q0 33-23.5 56.5T800-360h-80ZM160-80q-33 0-56.5-23.5T80-160v-360q0-33 23.5-56.5T160-600h480q33 0 56.5 23.5T720-520v360q0 33-23.5 56.5T640-80H160Zm400-603ZM400-340Z"
        />
      </svg>
      <span>Edit</span>
    </div>
    <div class="empty-space"></div>
    <!-- Sort Options -->
    <div class="media-header-sortitem">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="icon">
        <path d="M74-159v-135h304v135H74Zm0-255v-134h558v134H74Zm0-254v-135h812v135H74Z" />
      </svg>
      <div>{{ selectedSort() | displayTitle }}</div>
      <div class="sortitem-dropdown">
        @for (sortOption of sortOptions; track sortOption) {
          <div class="sortitem-dropdown-option" (click)="setMediaSort(sortOption)">
            {{ sortOption | displayTitle }}
            @if (selectedSort() == sortOption) {
              <div>
                @if (sortAscending()) {
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="icon">
                    <path d="M480-130 200-410l96-96 184 185 184-185 96 96-280 280Zm0-299L200-708l96-97 184 185 184-185 96 97-280 279Z" />
                  </svg>
                } @else {
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="icon">
                    <path d="m296-155-96-97 280-279 280 279-96 97-184-185-184 185Zm0-299-96-96 280-280 280 280-96 96-184-185-184 185Z" />
                  </svg>
                }
              </div>
            }
          </div>
        }
      </div>
    </div>

    <!-- Filter Options -->
    <div class="media-header-filteritem">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="icon">
        <path d="M371-158v-135h219v135H371ZM200-413v-135h558v135H200ZM74-668v-135h812v135H74Z" />
      </svg>
      <div>{{ selectedFilter() | displayTitle }}</div>
      <div class="filteritem-dropdown">
        @for (filterOption of allFilters(); track filterOption) {
          <div class="filteritem-dropdown-option" (click)="setMediaFilter(filterOption)">
            {{ filterOption | displayTitle }}
            @if (selectedFilter() == filterOption) {
              <div>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="icon">
                  <path d="M382-200 113-469l97-97 172 173 369-369 97 96-466 466Z" />
                </svg>
              </div>
            }
          </div>
        }
        <div class="filteritem-dropdown-option" (click)="openFilterDialog()" aria-label="CustomFilters" title="Edit">
          <span>Custom Filters</span>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="icon">
            <path
              d="M421-97v-248h83v83h353v83H504v82h-83Zm-318-82v-83h270v83H103Zm187-178v-82H103v-82h187v-84h83v248h-83Zm131-82v-82h436v82H421Zm166-176v-248h83v82h187v83H670v83h-83Zm-484-83v-83h436v83H103Z"
            />
          </svg>
        </div>
      </div>
    </div>
  </div>
} @else {
  <!-- Edit Mode Header -->
  <div class="media-header edit">
    <!-- Monitor Button -->
    <div class="media-header-button" (click)="batchUpdate('monitor')" aria-label="Monitor" title="Monitor">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="button-icon" aria-label="Monitor">
        <path
          d="M713-600 600-713l56-57 57 57 141-142 57 57-198 198ZM200-120v-640q0-33 23.5-56.5T280-840h280q-20 30-30 57.5T520-720q0 72 45.5 127T680-524q23 3 40 3t40-3v404L480-240 200-120Z"
        />
      </svg>
      <span>Monitor</span>
    </div>
    <!-- Unmonitor Button -->
    <div class="media-header-button" (click)="batchUpdate('unmonitor')" aria-label="UnMonitor" title="UnMonitor">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="button-icon" aria-label="UnMonitor">
        <path
          d="M200-120v-640q0-33 23.5-56.5T280-840h240v80H280v518l200-86 200 86v-278h80v400L480-240 200-120Zm80-640h240-240Zm400 160v-80h-80v-80h80v-80h80v80h80v80h-80v80h-80Z"
        />
      </svg>
      <span>UnMonitor</span>
    </div>
    <!-- Download Trailer Button -->
    <div class="media-header-button" (click)="openProfileSelectDialog()" aria-label="Download" title="Download">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="button-icon" aria-label="Download">
        <path
          d="M480-320 280-520l56-58 104 104v-326h80v326l104-104 56 58-200 200ZM240-160q-33 0-56.5-23.5T160-240v-120h80v120h480v-120h80v120q0 33-23.5 56.5T720-160H240Z"
        />
      </svg>
      <span>Download</span>
    </div>
    <!-- Delete Trailer Button -->
    <div class="media-header-button delete" (click)="batchUpdate('delete')" aria-label="Delete" title="Delete">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="button-icon" aria-label="Delete">
        <path
          d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"
        />
      </svg>
      <span>Delete</span>
    </div>
    <!-- Cancel Button -->
    <div class="media-header-button" (click)="toggleEditMode(false)" aria-label="Cancel" title="Cancel">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="button-icon" aria-label="Cancel">
        <path
          d="M819-28 407-440H160v280h480v-161l80 80v81q0 33-23.5 56.5T640-80H160q-33 0-56.5-23.5T80-160v-360q0-33 23.5-56.5T160-600h80v-7L27-820l57-57L876-85l-57 57Zm-99-327-80-80-165-165h165q33 0 56.5 23.5T720-520v80h80v-280H355L246-829q8-23 28.5-37t45.5-14h480q33 0 56.5 23.5T880-800v360q0 33-23.5 56.5T800-360h-80v5Z"
        />
      </svg>
      <span>Cancel</span>
    </div>
    <div class="empty-space"></div>
    <!-- Selected Count -->
    <p class="count">
      <span>Selected: </span>
      {{ selectedMedia.length }}
      <span> / {{ filteredSortedMedia().length }}</span>
    </p>
    <!-- Select All Button -->
    <div class="media-header-button" (click)="selectAll()" aria-label="Select All" title="Select All">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="button-icon" aria-label="Clear">
        <path
          d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q8 0 15 1.5t14 4.5l-74 74H200v560h560v-266l80-80v346q0 33-23.5 56.5T760-120H200Zm261-160L235-506l56-56 170 170 367-367 57 55-424 424Z"
        />
      </svg>
    </div>
    <!-- Clear Button -->
    <div class="media-header-button" (click)="selectedMedia = []" aria-label="Clear" title="Clear">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="button-icon" aria-label="Clear">
        <path
          d="m500-120-56-56 142-142-142-142 56-56 142 142 142-142 56 56-142 142 142 142-56 56-142-142-142 142Zm-220 0v-80h80v80h-80Zm-80-640h-80q0-33 23.5-56.5T200-840v80Zm80 0v-80h80v80h-80Zm160 0v-80h80v80h-80Zm160 0v-80h80v80h-80Zm160 0v-80q33 0 56.5 23.5T840-760h-80ZM200-200v80q-33 0-56.5-23.5T120-200h80Zm-80-80v-80h80v80h-80Zm0-160v-80h80v80h-80Zm0-160v-80h80v80h-80Zm640 0v-80h80v80h-80Z"
        />
      </svg>
    </div>
  </div>
}

<div class="media-container">
  <!-- <h1 class="text-center">{{title}}</h1> -->
  @if (isLoading()) {
    <app-load-indicator class="center" />
  } @else {
    @if (filteredSortedMedia().length === 0) {
      <!-- No media items found -->
      <div class="center">
        <!-- Table Eye Icon - Google Fonts -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="empty-icon">
          <path
            d="M215.38-160q-23.05 0-39.22-16.16Q160-192.33 160-215.38v-529.24q0-23.05 16.16-39.22Q192.33-800 215.38-800h529.24q23.05 0 39.22 16.16Q800-767.67 800-744.62V-418q-7.33-4.55-15.4-7.82-8.08-3.27-15.37-6.8v-185.84H495.38v201.61q-10.84 6.39-22.26 13.54-11.43 7.16-21.89 14.85H190.77v173.08q0 10.76 6.92 17.69 6.93 6.92 17.69 6.92h128.16q6.15 8.54 12.42 16.12 6.27 7.57 12.66 14.65H215.38Zm-24.61-259.23h273.85v-199.23H190.77v199.23Zm0-230h578.46v-95.39q0-10.76-6.92-17.69-6.93-6.92-17.69-6.92H215.38q-10.76 0-17.69 6.92-6.92 6.93-6.92 17.69v95.39ZM480-480Zm0 0Zm0 0Zm0 0ZM650.37-98.46q-71.22 0-131.91-36.54t-97.23-97.31q36.54-60.77 97.23-97.31 60.69-36.53 132.16-36.53 71.46 0 131.76 36.53 60.31 36.54 97.62 97.81-36.08 61.27-97.25 97.31T650.37-98.46Zm.25-30.77q57.76 0 108.07-28.35 50.31-28.34 85.08-74.73-34.77-46.38-84.9-74.73-50.12-28.34-108.64-28.34-57.38 0-108.08 28.34-50.69 28.35-84.69 74.73 34 46.39 84.69 74.73 50.7 28.35 108.47 28.35Zm-.12-67.69q-15.12 0-25.38-10.44-10.27-10.43-10.27-25.11t10.42-24.95q10.41-10.27 25.08-10.27 15.5 0 25.38 10.43 9.89 10.43 9.89 25.12 0 14.68-10.01 24.95-10 10.27-25.11 10.27Z"
          />
        </svg>
        <p>No media items found matching the selected filter!</p>
        <!-- <div class="all-empty-card" [routerLink]="['/settings', 'connections', 'add']">
                    Click me!
                </div> -->
      </div>
    }

    <div class="media-row" appScrollNearEnd (nearEnd)="onNearEndScroll()">
      @for (media of displayMedia(); track media) {
        <!-- <div class="media-card" [routerLink]="['/media', media.id]"> -->
        @if (inEditMode) {
          <!-- Edit Mode - Show Checkboxes -->
          <div class="media-card" [title]="media.title">
            <input
              type="checkbox"
              [id]="media.id"
              class="media-card-checkbox"
              (click)="$event.stopPropagation()"
              (change)="onMediaSelected(media, $event)"
              [checked]="selectedMedia.includes(media.id)"
            />
            <ng-container *ngTemplateOutlet="mediaCard; context: {media: media}"></ng-container>
          </div>
        } @else {
          <!-- Normal Mode - Show Media Card -->
          <div class="media-card" [routerLink]="['/media', media.id]" [title]="media.title" [id]="media.id">
            <ng-container *ngTemplateOutlet="mediaCard; context: {media: media}"></ng-container>
          </div>
        }
      }
    </div>
  }
</div>

<ng-template #mediaCard let-media="media">
  <label [for]="media.id">
    <img
      id="mediaImage{{ media.id }}"
      [src]="media.poster_path || 'assets/poster-sm.png'"
      [alt]="media.title"
      loading="lazy"
      (load)="media.isImageLoaded = true"
      (error)="media.isImageLoaded = true"
      [class.animated-gradient]="!media.isImageLoaded"
    />
    <p>{{ media.title }}</p>
  </label>
  @if (media.status.toLowerCase() == 'downloading') {
    <!-- Downloading Icon -->
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="monitored-icon" aria-label="Downloading">
      <g transform="scale(0.9) translate(65,-60)">
        <path
          d="M343 -107q-120 -42 -194.5 -146.5T74 -490q0 -29 4 -57.5T91 -604l-57 33 -37 -62 185 -107 106 184 -63 36 -54 -92q-13 30 -18.5 60.5T147 -490q0 113 65.5 200T381 -171zm291 -516v-73h107q-47 -60 -115.5 -93.5T480 -823q-66 0 -123.5 24T255 -734l-38 -65q54 -45 121 -71t142 -26q85 0 160.5 33T774 -769v-67h73v213zM598 -1 413 -107l107 -184 62 37 -54 94q123 -17 204.5 -110.5T814 -489q0 -19 -2.5 -37.5T805 -563h74q4 18 6 36.5t2 36.5q0 142 -87 251.5T578 -96l56 33z"
        >
          <animateTransform attributeName="transform" type="rotate" from="0 470 -480" to="360 470 -480" dur="5" repeatCount="indefinite" />
        </path>
      </g>
    </svg>
  } @else if (media.monitor) {
    <!-- Monitored Icon -->
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="monitored-icon" aria-label="Monitored">
      <path
        d="M713-600 600-713l56-57 57 57 141-142 57 57-198 198ZM200-120v-640q0-33 23.5-56.5T280-840h280q-20 30-30 57.5T520-720q0 72 45.5 127T680-524q23 3 40 3t40-3v404L480-240 200-120Z"
      />
    </svg>
  } @else {
    <!-- Trailer Exists Icon -->
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 -960 960 960"
      class="downloaded-icon"
      [class.success]="media.trailer_exists"
      aria-label="Trailer Exists"
    >
      <path
        d="M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q65 0 123 19t107 53l-58 59q-38-24-81-37.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160q133 0 226.5-93.5T800-480q0-18-2-36t-6-35l65-65q11 32 17 66t6 70q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm-56-216L254-466l56-56 114 114 400-401 56 56-456 457Z"
      />
    </svg>
  }
</ng-template>

<!-- Dialog to show List of Custom Filters -->
<dialog #showFiltersDialog (close)="closeFilterDialog()">
  <div class="dialog-content" (click)="$event.stopPropagation()">
    <div class="dialog-title">Custom Filters</div>
    @for (filter of customFilters(); track filter) {
      <div class="filteritem-dropdown-option">
        <span (click)="openFilterEditDialog(filter)" title="Edit Custom Filter">
          {{ filter.filter_name }}
        </span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 -960 960 960"
          class="icon delete-icon"
          aria-label="Delete"
          (click)="deleteFilter(filter.id)"
          title="Delete Custom Filter"
        >
          <path
            d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"
          />
        </svg>
      </div>
    }
  </div>
  <div class="buttons-row">
    <!-- Button to Cancel Dialog -->
    <button class="danger" (click)="closeFilterDialog()">Cancel</button>
    <!-- Add New Custom Filter button -->
    <button class="primary" (click)="openFilterEditDialog(null)">Add New</button>
  </div>
</dialog>
<template #dialogContainer></template>
`, styles: ['/* src/app/media/media.component.scss */\n.media-header {\n  display: flex;\n  position: sticky;\n  top: 76px;\n  width: 100%;\n  justify-content: flex-end;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  align-items: center;\n  padding: 0 1rem;\n  z-index: 99;\n}\n@media (width < 765px) {\n  .media-header {\n    position: fixed;\n    top: auto;\n    bottom: 78px;\n    left: 0;\n    right: 0;\n  }\n}\n.media-header .empty-space {\n  flex: 1;\n  margin: auto;\n}\n.edit {\n  justify-content: flex-start;\n  gap: 1rem;\n}\n@media (width < 765px) {\n  .edit {\n    gap: 0.5rem;\n  }\n}\n.edit .count {\n  font-weight: bold;\n  color: var(--color-primary);\n}\n@media (width < 765px) {\n  .edit .count span {\n    display: none;\n  }\n}\n.media-header-button {\n  display: flex;\n  align-items: center;\n  font-weight: bold;\n  cursor: pointer;\n  padding: 0.75rem 0;\n}\n.media-header-button .button-icon {\n  width: 2.25rem;\n  height: 2.25rem;\n  font-size: 0;\n  margin: 0;\n  padding: 0.25rem;\n  fill: var(--color-on-surface);\n}\n@media (width < 765px) {\n  .media-header-button span {\n    display: none;\n  }\n}\n.media-header-button:hover:not(.delete) {\n  color: var(--color-primary);\n}\n.media-header-button:hover:not(.delete) svg {\n  fill: var(--color-primary) !important;\n}\n.delete {\n  color: var(--color-error);\n}\n.delete svg {\n  fill: var(--color-error) !important;\n}\n.media-header-sortitem,\n.media-header-filteritem {\n  position: relative;\n  display: flex;\n  flex-wrap: nowrap;\n  align-items: center;\n  justify-content: flex-start;\n  cursor: pointer;\n  font-weight: bold;\n  padding: 1rem;\n  gap: 0.5rem;\n}\n.icon {\n  margin: 0;\n}\n.empty-icon {\n  width: 100%;\n  height: clamp(10rem, 25vh, 30rem);\n  fill: var(--color-on-surface);\n}\n.media-header-sortitem:hover,\n.media-header-filteritem:hover,\n.media-header-button:hover {\n  background-color: var(--color-surface-container-highest);\n}\n.sortitem-dropdown,\n.filteritem-dropdown {\n  display: none;\n  position: absolute;\n  min-width: 8rem;\n  top: 3.5rem;\n  right: 0;\n  background-color: var(--color-surface-container-highest);\n  z-index: 100;\n  box-shadow: 0.5rem 1rem 1rem 0px var(--color-shadow);\n}\n@media (width < 765px) {\n  .sortitem-dropdown,\n  .filteritem-dropdown {\n    top: auto;\n    bottom: 3.5rem;\n    box-shadow: 0.5rem -1rem 1rem 0 var(--color-shadow);\n  }\n}\n.filteritem-dropdown {\n  min-width: 11rem;\n}\n.media-header-sortitem:hover .sortitem-dropdown,\n.media-header-filteritem:hover .filteritem-dropdown {\n  display: flex;\n  flex-direction: column;\n}\n.sortitem-dropdown-option,\n.filteritem-dropdown-option {\n  display: flex;\n  cursor: pointer;\n  align-items: center;\n  justify-content: space-between;\n  gap: 0.5rem;\n  font-weight: 400;\n  height: 2.75rem;\n  padding: 0.5rem 0.25rem 0.5rem 0.75rem;\n}\n.sortitem-dropdown-option span,\n.filteritem-dropdown-option span {\n  text-align: left;\n  flex: 1;\n}\n.sortitem-dropdown-option:hover,\n.filteritem-dropdown-option:hover {\n  background-color: var(--color-secondary-container);\n  color: var(--color-primary);\n}\n.media-container {\n  display: flex;\n  flex-direction: column;\n  overflow-y: auto;\n}\n@media (width < 765px) {\n  .media-container {\n    margin-bottom: 80px;\n  }\n}\n.text-center {\n  text-align: center;\n}\n.center {\n  margin: auto;\n  align-content: center;\n  min-height: 70vh;\n}\n.media-row {\n  display: grid;\n  grid-template-columns: repeat(auto-fill, minmax(min(180px, 100%), 1fr));\n  gap: 1rem;\n  padding: 1rem;\n}\n@media (width < 900px) {\n  .media-row {\n    grid-template-columns: repeat(auto-fill, minmax(min(120px, 100%), 1fr));\n    gap: 0.5rem;\n    padding: 0.5rem;\n  }\n}\n.media-card {\n  display: flex;\n  flex-direction: column;\n  transition: all 0.4s;\n  border-radius: 10px;\n  cursor: pointer;\n  position: relative;\n  overflow: hidden;\n  background-image: url("./media/poster-sm.png");\n  background-repeat: no-repeat;\n  background-size: cover;\n}\n.media-card label {\n  cursor: pointer;\n  display: flex;\n  flex-direction: column;\n}\n.media-card-checkbox {\n  position: absolute;\n  top: 0.5rem;\n  left: 0.5rem;\n  width: 1.5rem;\n  height: 1.5rem;\n  background-color: var(--color-surface-container-high);\n  outline: 2px solid var(--color-primary);\n}\n@media (width < 765px) {\n  .media-card-checkbox {\n    top: 0.25rem;\n    left: 0.25rem;\n    width: 1rem;\n    height: 1rem;\n  }\n}\n.media-card-checkbox:checked {\n  outline: none;\n  accent-color: var(--color-primary);\n}\n.media-card-checkbox:checked + label {\n  border: 4px solid var(--color-primary);\n  border-radius: 10px;\n}\n.media-card label p {\n  width: 100%;\n  text-align: center;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-primary);\n  padding: 0.5rem 0;\n  margin: 0;\n  white-space: nowrap;\n  overflow: hidden;\n  text-overflow: ellipsis;\n  border-radius: 0 0 6px 6px;\n}\n.animated-gradient {\n  animation: animateBg 2s linear infinite;\n  background-image:\n    linear-gradient(\n      135deg,\n      var(--color-surface-container-highest),\n      var(--color-surface-container-low),\n      var(--color-surface-container-highest),\n      var(--color-surface-container-low));\n  background-size: 100% 450%;\n}\n@keyframes animateBg {\n  0% {\n    background-position: 0% 100%;\n  }\n  100% {\n    background-position: 0% 0%;\n  }\n}\n.media-card img {\n  object-fit: cover;\n  overflow: hidden;\n  width: 100%;\n  aspect-ratio: 2/3;\n  border-radius: 6px 6px 0 0;\n}\n.media-card svg {\n  position: absolute;\n  top: 5px;\n  height: 24px;\n  width: 24px;\n}\n.media-card .monitored-icon,\n.media-card .downloaded-icon {\n  fill: var(--color-info);\n  right: 5px;\n}\n.media-card .success {\n  fill: var(--color-success);\n}\n.media-card h5 {\n  display: none;\n}\n.media-card:hover {\n  box-shadow: 0px 0px 10px 5px var(--color-outline);\n}\n.dialog-content {\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n  padding: 1rem;\n  min-width: max(25vw, min(300px, 80vw));\n}\n.dialog-content > * {\n  border-bottom: 1px solid var(--color-outline);\n}\n.dialog-title {\n  font-size: larger;\n  font-weight: 700;\n  border-bottom: none !important;\n  padding-bottom: 0.5rem;\n  margin: 1rem;\n}\n.delete-icon {\n  fill: var(--color-error);\n  width: 2rem;\n  height: 2rem;\n}\n.buttons-row {\n  display: block flex;\n  align-items: center;\n  justify-content: space-around;\n  padding: 1rem 0;\n}\n/*# sourceMappingURL=media.component.css.map */\n'] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(MediaComponent, { className: "MediaComponent", filePath: "src/app/media/media.component.ts", lineNumber: 32 });
})();

// src/app/media/routes.ts
var routes_default = [{ path: "", loadComponent: () => MediaComponent }];
export {
  routes_default as default
};
//# sourceMappingURL=chunk-KDSDJ3VX.js.map
