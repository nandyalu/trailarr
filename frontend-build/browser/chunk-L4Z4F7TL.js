import {
  ProfileService
} from "./chunk-J3HM2TW5.js";
import {
  FormsModule,
  NgControlStatus,
  NgModel,
  NgSelectOption,
  RequiredValidator,
  SelectControlValueAccessor,
  ɵNgSelectMultipleOption
} from "./chunk-BOQEVO5H.js";
import {
  Component,
  effect,
  inject,
  output,
  setClassMetadata,
  signal,
  viewChild,
  ɵsetClassDebugInfo,
  ɵɵadvance,
  ɵɵdefineComponent,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵgetCurrentView,
  ɵɵlistener,
  ɵɵproperty,
  ɵɵqueryAdvance,
  ɵɵrepeater,
  ɵɵrepeaterCreate,
  ɵɵrepeaterTrackByIdentity,
  ɵɵresetView,
  ɵɵrestoreView,
  ɵɵtext,
  ɵɵtextInterpolate,
  ɵɵtwoWayBindingSet,
  ɵɵtwoWayListener,
  ɵɵtwoWayProperty,
  ɵɵviewQuerySignal
} from "./chunk-FAGZ4ZSE.js";

// src/app/media/dialogs/profile-select-dialog/profile-select-dialog.component.ts
var _c0 = ["profileSelectDialog"];
function ProfileSelectDialogComponent_For_11_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "option", 5);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const profile_r2 = ctx.$implicit;
    \u0275\u0275property("value", profile_r2.id);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(profile_r2.customfilter.filter_name);
  }
}
var ProfileSelectDialogComponent = class _ProfileSelectDialogComponent {
  constructor() {
    this.profileService = inject(ProfileService);
    this.allProfiles = this.profileService.allProfiles.value;
    this.onSubmit = output();
    this.onClosed = output();
    this.selectedProfileID = signal(0);
    this.profileSelectDialog = viewChild.required("profileSelectDialog");
    this.showDialog = () => this.profileSelectDialog().nativeElement.showModal();
    this.closeDialog = () => this.profileSelectDialog().nativeElement.close();
    effect(() => {
      this.selectedProfileID.set(0);
    });
  }
  ngAfterViewInit() {
    this.showDialog();
  }
  onConfirm() {
    this.onSubmit.emit(this.selectedProfileID());
    this.closeDialog();
  }
  onCancel() {
    this.onClosed.emit();
    this.closeDialog();
  }
  static {
    this.\u0275fac = function ProfileSelectDialogComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _ProfileSelectDialogComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _ProfileSelectDialogComponent, selectors: [["app-profile-select-dialog"]], viewQuery: function ProfileSelectDialogComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuerySignal(ctx.profileSelectDialog, _c0, 5);
      }
      if (rf & 2) {
        \u0275\u0275queryAdvance();
      }
    }, outputs: { onSubmit: "onSubmit", onClosed: "onClosed" }, decls: 17, vars: 2, consts: [["profileSelectDialog", ""], [3, "close"], [1, "dialog-content", 3, "click"], ["for", "profile-select"], ["name", "profiles", "id", "profile-select", "required", "true", 3, "ngModelChange", "ngModel"], [3, "value"], [1, "buttons-row"], [1, "primary", 3, "click", "disabled"], [1, "danger", 3, "click"]], template: function ProfileSelectDialogComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275elementStart(0, "dialog", 1, 0);
        \u0275\u0275listener("close", function ProfileSelectDialogComponent_Template_dialog_close_0_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onCancel());
        });
        \u0275\u0275elementStart(2, "div", 2);
        \u0275\u0275listener("click", function ProfileSelectDialogComponent_Template_div_click_2_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(3, "h3");
        \u0275\u0275text(4, "Select Trailer Profile");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(5, "p");
        \u0275\u0275text(6, "Select a profile to use for searching/downloading");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(7, "label", 3);
        \u0275\u0275text(8, "Select a Profile:");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(9, "select", 4);
        \u0275\u0275twoWayListener("ngModelChange", function ProfileSelectDialogComponent_Template_select_ngModelChange_9_listener($event) {
          \u0275\u0275restoreView(_r1);
          \u0275\u0275twoWayBindingSet(ctx.selectedProfileID, $event) || (ctx.selectedProfileID = $event);
          return \u0275\u0275resetView($event);
        });
        \u0275\u0275repeaterCreate(10, ProfileSelectDialogComponent_For_11_Template, 2, 2, "option", 5, \u0275\u0275repeaterTrackByIdentity);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(12, "div", 6)(13, "button", 7);
        \u0275\u0275listener("click", function ProfileSelectDialogComponent_Template_button_click_13_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onConfirm());
        });
        \u0275\u0275text(14, "Confirm");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(15, "button", 8);
        \u0275\u0275listener("click", function ProfileSelectDialogComponent_Template_button_click_15_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onCancel());
        });
        \u0275\u0275text(16, "Cancel");
        \u0275\u0275elementEnd()()()();
      }
      if (rf & 2) {
        \u0275\u0275advance(9);
        \u0275\u0275twoWayProperty("ngModel", ctx.selectedProfileID);
        \u0275\u0275advance();
        \u0275\u0275repeater(ctx.allProfiles());
        \u0275\u0275advance(3);
        \u0275\u0275property("disabled", !ctx.selectedProfileID());
      }
    }, dependencies: [FormsModule, NgSelectOption, \u0275NgSelectMultipleOption, SelectControlValueAccessor, NgControlStatus, RequiredValidator, NgModel], styles: ["\n\n.dialog-content[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  gap: 0.5rem;\n  padding: 1rem;\n  min-width: max(25vw, min(300px, 80vw));\n}\nh3[_ngcontent-%COMP%] {\n  font-size: larger;\n  font-weight: 700;\n  margin: 1rem;\n}\nlabel[_ngcontent-%COMP%] {\n  font-size: 1rem;\n  color: var(--color-on-surface);\n  padding: 0 0.5rem;\n  transition: 0.5s;\n}\nselect[_ngcontent-%COMP%] {\n  min-width: 15rem;\n  height: 3rem;\n  margin: auto;\n  padding: 0.25rem 0.5rem;\n  font-family: inherit;\n  font-size: 1.25rem;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-tertiary);\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n}\n.ng-touched.ng-invalid[_ngcontent-%COMP%]:not(form):not(div) {\n  border: 2px solid var(--color-danger);\n}\n/*# sourceMappingURL=profile-select-dialog.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ProfileSelectDialogComponent, [{
    type: Component,
    args: [{ selector: "app-profile-select-dialog", imports: [FormsModule], template: '<dialog #profileSelectDialog (close)="onCancel()">\n  <div class="dialog-content" (click)="$event.stopPropagation()">\n    <h3>Select Trailer Profile</h3>\n    <p>Select a profile to use for searching/downloading</p>\n    <label for="profile-select">Select a Profile:</label>\n    <select name="profiles" id="profile-select" [(ngModel)]="selectedProfileID" required="true">\n      @for (profile of allProfiles(); track profile) {\n        <option [value]="profile.id">{{ profile.customfilter.filter_name }}</option>\n      }\n    </select>\n    <div class="buttons-row">\n      <button class="primary" [disabled]="!selectedProfileID()" (click)="onConfirm()">Confirm</button>\n      <button class="danger" (click)="onCancel()">Cancel</button>\n    </div>\n  </div>\n</dialog>\n', styles: ["/* src/app/media/dialogs/profile-select-dialog/profile-select-dialog.component.scss */\n.dialog-content {\n  display: flex;\n  flex-direction: column;\n  gap: 0.5rem;\n  padding: 1rem;\n  min-width: max(25vw, min(300px, 80vw));\n}\nh3 {\n  font-size: larger;\n  font-weight: 700;\n  margin: 1rem;\n}\nlabel {\n  font-size: 1rem;\n  color: var(--color-on-surface);\n  padding: 0 0.5rem;\n  transition: 0.5s;\n}\nselect {\n  min-width: 15rem;\n  height: 3rem;\n  margin: auto;\n  padding: 0.25rem 0.5rem;\n  font-family: inherit;\n  font-size: 1.25rem;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-tertiary);\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n}\n.ng-touched.ng-invalid:not(form):not(div) {\n  border: 2px solid var(--color-danger);\n}\n/*# sourceMappingURL=profile-select-dialog.component.css.map */\n"] }]
  }], () => [], null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(ProfileSelectDialogComponent, { className: "ProfileSelectDialogComponent", filePath: "src/app/media/dialogs/profile-select-dialog/profile-select-dialog.component.ts", lineNumber: 11 });
})();

export {
  ProfileSelectDialogComponent
};
//# sourceMappingURL=chunk-L4Z4F7TL.js.map
