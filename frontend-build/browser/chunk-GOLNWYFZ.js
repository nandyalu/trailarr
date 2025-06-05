import {
  RouteAbout,
  RouteAdd,
  RouteConnections,
  RouteEdit,
  RouteParamConnectionId,
  RouteParamProfileId,
  RouteProfiles,
  RouteSettings,
  RouteTrailer
} from "./chunk-6WR6ESSR.js";
import {
  AddCustomFilterDialogComponent
} from "./chunk-GVMLCJCM.js";
import {
  jsonEqual
} from "./chunk-GF5DKDDQ.js";
import {
  ProfileService
} from "./chunk-J3HM2TW5.js";
import {
  ActivatedRoute,
  ConnectionsService,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet
} from "./chunk-U5GO6X62.js";
import {
  WebsocketService
} from "./chunk-KIVIDEQ5.js";
import {
  DefaultValueAccessor,
  FormArray,
  FormArrayName,
  FormControl,
  FormControlName,
  FormGroup,
  FormGroupDirective,
  FormGroupName,
  FormsModule,
  MaxLengthValidator,
  MinLengthValidator,
  NgControlStatus,
  NgControlStatusGroup,
  NgForm,
  NgModel,
  RangeValueAccessor,
  ReactiveFormsModule,
  RequiredValidator,
  Validators,
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
  AsyncPipe,
  ChangeDetectionStrategy,
  CommonModule,
  Component,
  DatePipe,
  HttpClient,
  Injectable,
  Location,
  NgForOf,
  NgIf,
  Subject,
  UpperCasePipe,
  ViewChild,
  ViewContainerRef,
  __async,
  __spreadProps,
  __spreadValues,
  catchError,
  computed,
  distinctUntilChanged,
  effect,
  environment,
  httpResource,
  inject,
  input,
  map,
  model,
  of,
  output,
  setClassMetadata,
  shareReplay,
  signal,
  startWith,
  switchMap,
  tap,
  viewChild,
  ɵsetClassDebugInfo,
  ɵɵNgOnChangesFeature,
  ɵɵadvance,
  ɵɵattribute,
  ɵɵclassMapInterpolate1,
  ɵɵclassProp,
  ɵɵconditional,
  ɵɵdeclareLet,
  ɵɵdefineComponent,
  ɵɵdefineInjectable,
  ɵɵelement,
  ɵɵelementContainer,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵgetCurrentView,
  ɵɵlistener,
  ɵɵloadQuery,
  ɵɵnamespaceHTML,
  ɵɵnamespaceSVG,
  ɵɵnextContext,
  ɵɵpipe,
  ɵɵpipeBind1,
  ɵɵproperty,
  ɵɵpropertyInterpolate,
  ɵɵpureFunction2,
  ɵɵpureFunction3,
  ɵɵqueryAdvance,
  ɵɵqueryRefresh,
  ɵɵreadContextLet,
  ɵɵreference,
  ɵɵrepeater,
  ɵɵrepeaterCreate,
  ɵɵrepeaterTrackByIdentity,
  ɵɵrepeaterTrackByIndex,
  ɵɵresetView,
  ɵɵrestoreView,
  ɵɵsanitizeUrl,
  ɵɵstoreLet,
  ɵɵtemplate,
  ɵɵtemplateRefExtractor,
  ɵɵtext,
  ɵɵtextInterpolate,
  ɵɵtextInterpolate1,
  ɵɵtextInterpolate2,
  ɵɵtwoWayBindingSet,
  ɵɵtwoWayListener,
  ɵɵtwoWayProperty,
  ɵɵviewQuery,
  ɵɵviewQuerySignal
} from "./chunk-FAGZ4ZSE.js";

// src/app/services/settings.service.ts
var SettingsService = class _SettingsService {
  constructor() {
    this.http = inject(HttpClient);
    this.settingsUrl = environment.apiUrl + environment.settings;
    this.settingsResource = httpResource(() => this.settingsUrl);
    this.connectionsUrl = environment.apiUrl + environment.connections;
  }
  getSettings() {
    return this.http.get(this.settingsUrl);
  }
  getServerStats() {
    var serverStatsUrl = this.settingsUrl + "stats";
    return this.http.get(serverStatsUrl);
  }
  updateSetting(key, value) {
    const updateSettingUrl = this.settingsUrl + "update";
    if (typeof value === "string" && value === "")
      value = " ";
    const update_obj = {
      key,
      value
    };
    return this.http.put(updateSettingUrl, update_obj).pipe(catchError((error) => {
      let errorMessage = "";
      if (error.error instanceof ErrorEvent) {
        errorMessage = `Error: ${error.error.message}`;
      } else {
        errorMessage = `Error: ${error.status} ${error.error.detail}`;
      }
      return of(errorMessage);
    }));
  }
  updatePassword(currentPassword, newUsername, newPassword) {
    const updatePasswordUrl = this.settingsUrl + "updatelogin";
    const update_obj = {
      current_password: currentPassword,
      new_username: newUsername,
      new_password: newPassword
    };
    return this.http.put(updatePasswordUrl, update_obj).pipe(catchError((error) => {
      let errorMessage = "";
      if (error.error instanceof ErrorEvent) {
        errorMessage = `Error: ${error.error.message}`;
      } else {
        errorMessage = `Error: ${error.status} ${error.error.detail}`;
      }
      return of(errorMessage);
    }));
  }
  getConnection(id) {
    var connectionIdUrl = this.connectionsUrl + id;
    return this.http.get(connectionIdUrl).pipe(map((connection) => __spreadProps(__spreadValues({}, connection), {
      added_at: new Date(connection.added_at)
    })));
  }
  addConnection(connection) {
    return this.http.post(this.connectionsUrl, connection).pipe(catchError((error) => {
      let errorMessage = "";
      if (error.error instanceof ErrorEvent) {
        errorMessage = `Error: ${error.error.message}`;
      } else {
        errorMessage = `Error: ${error.status} ${error.error.detail}`;
      }
      return of(errorMessage);
    }));
  }
  testConnection(connection) {
    var testConnectionUrl = this.connectionsUrl + "test";
    return this.http.post(testConnectionUrl, connection).pipe(catchError((error) => {
      let errorMessage = "";
      if (error.error instanceof ErrorEvent) {
        errorMessage = `Error: ${error.error.message}`;
      } else {
        errorMessage = `Error: ${error.status} ${error.error.detail}`;
      }
      return of(errorMessage);
    }));
  }
  getRootFolders(connection) {
    var rootFoldersUrl = this.connectionsUrl + "rootfolders";
    return this.http.post(rootFoldersUrl, connection).pipe(catchError((error) => {
      let errorMessage = "";
      if (error.error instanceof ErrorEvent) {
        errorMessage = `Error: ${error.error.message}`;
      } else {
        errorMessage = `Error: ${error.status} ${error.error.detail}`;
      }
      return of(errorMessage);
    }));
  }
  updateConnection(connection) {
    var connectionIdUrl = this.connectionsUrl + connection.id;
    return this.http.put(connectionIdUrl, connection).pipe(catchError((error) => {
      let errorMessage = "";
      if (error.error instanceof ErrorEvent) {
        errorMessage = `Error: ${error.error.message}`;
      } else {
        errorMessage = `Error: ${error.status} ${error.error.detail}`;
      }
      return of(errorMessage);
    }));
  }
  static {
    this.\u0275fac = function SettingsService_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _SettingsService)();
    };
  }
  static {
    this.\u0275prov = /* @__PURE__ */ \u0275\u0275defineInjectable({ token: _SettingsService, factory: _SettingsService.\u0275fac, providedIn: "root" });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(SettingsService, [{
    type: Injectable,
    args: [{
      providedIn: "root"
    }]
  }], null, null);
})();

// src/app/settings/about/about.component.ts
var _c0 = ["passwordUpdateDialog"];
function AboutComponent_Conditional_110_ng_container_10_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function AboutComponent_Conditional_110_ng_container_24_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function AboutComponent_Conditional_110_p_27_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 34);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(2);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(ctx_r2.updateError);
  }
}
function AboutComponent_Conditional_110_p_28_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 35);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(2);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(ctx_r2.updateSuccess);
  }
}
function AboutComponent_Conditional_110_div_33_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "div", 36);
  }
}
function AboutComponent_Conditional_110_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "form", 19);
    \u0275\u0275listener("click", function AboutComponent_Conditional_110_Template_form_click_0_listener($event) {
      \u0275\u0275restoreView(_r2);
      return \u0275\u0275resetView($event.stopPropagation());
    });
    \u0275\u0275elementStart(1, "h2");
    \u0275\u0275text(2, "Update Login Credentials");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "div", 20)(4, "div", 21)(5, "input", 22, 3);
    \u0275\u0275twoWayListener("ngModelChange", function AboutComponent_Conditional_110_Template_input_ngModelChange_5_listener($event) {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext();
      \u0275\u0275twoWayBindingSet(ctx_r2.currentPassword, $event) || (ctx_r2.currentPassword = $event);
      return \u0275\u0275resetView($event);
    });
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(7, "label", 23);
    \u0275\u0275text(8, "Current Password");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(9, "i", 17);
    \u0275\u0275listener("click", function AboutComponent_Conditional_110_Template_i_click_9_listener() {
      \u0275\u0275restoreView(_r2);
      const currentPasswordInput_r4 = \u0275\u0275reference(6);
      const ctx_r2 = \u0275\u0275nextContext();
      ctx_r2.togglePasswordVisibility(currentPasswordInput_r4);
      return \u0275\u0275resetView(ctx_r2.currentPasswordVisible = !ctx_r2.currentPasswordVisible);
    });
    \u0275\u0275template(10, AboutComponent_Conditional_110_ng_container_10_Template, 1, 0, "ng-container", 24);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(11, "h3");
    \u0275\u0275text(12, "New Login");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(13, "div", 21)(14, "input", 25, 4);
    \u0275\u0275twoWayListener("ngModelChange", function AboutComponent_Conditional_110_Template_input_ngModelChange_14_listener($event) {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext();
      \u0275\u0275twoWayBindingSet(ctx_r2.newUsername, $event) || (ctx_r2.newUsername = $event);
      return \u0275\u0275resetView($event);
    });
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(16, "label", 26);
    \u0275\u0275text(17, "New Username");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(18, "div", 21)(19, "input", 27, 5);
    \u0275\u0275twoWayListener("ngModelChange", function AboutComponent_Conditional_110_Template_input_ngModelChange_19_listener($event) {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext();
      \u0275\u0275twoWayBindingSet(ctx_r2.newPassword, $event) || (ctx_r2.newPassword = $event);
      return \u0275\u0275resetView($event);
    });
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(21, "label", 28);
    \u0275\u0275text(22, "New Password ");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(23, "i", 17);
    \u0275\u0275listener("click", function AboutComponent_Conditional_110_Template_i_click_23_listener() {
      \u0275\u0275restoreView(_r2);
      const newPasswordInput_r5 = \u0275\u0275reference(20);
      const ctx_r2 = \u0275\u0275nextContext();
      ctx_r2.togglePasswordVisibility(newPasswordInput_r5);
      return \u0275\u0275resetView(ctx_r2.newPasswordVisible = !ctx_r2.newPasswordVisible);
    });
    \u0275\u0275template(24, AboutComponent_Conditional_110_ng_container_24_Template, 1, 0, "ng-container", 24);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(25, "span");
    \u0275\u0275text(26, "For updating only username/password, leave the other blank");
    \u0275\u0275elementEnd()();
    \u0275\u0275template(27, AboutComponent_Conditional_110_p_27_Template, 2, 1, "p", 29)(28, AboutComponent_Conditional_110_p_28_Template, 2, 1, "p", 30);
    \u0275\u0275elementStart(29, "button", 31);
    \u0275\u0275listener("click", function AboutComponent_Conditional_110_Template_button_click_29_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.onConfirmUpdate());
    });
    \u0275\u0275text(30, "Update");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(31, "button", 32);
    \u0275\u0275listener("click", function AboutComponent_Conditional_110_Template_button_click_31_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.closePwUpdateDialog());
    });
    \u0275\u0275text(32, "Cancel");
    \u0275\u0275elementEnd();
    \u0275\u0275template(33, AboutComponent_Conditional_110_div_33_Template, 1, 0, "div", 33);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext();
    const passwordVisible_r6 = \u0275\u0275reference(112);
    const passwordHidden_r7 = \u0275\u0275reference(114);
    \u0275\u0275advance(5);
    \u0275\u0275twoWayProperty("ngModel", ctx_r2.currentPassword);
    \u0275\u0275advance(5);
    \u0275\u0275property("ngIf", ctx_r2.currentPasswordVisible)("ngIfThen", passwordVisible_r6)("ngIfElse", passwordHidden_r7);
    \u0275\u0275advance(4);
    \u0275\u0275twoWayProperty("ngModel", ctx_r2.newUsername);
    \u0275\u0275advance(5);
    \u0275\u0275twoWayProperty("ngModel", ctx_r2.newPassword);
    \u0275\u0275advance(5);
    \u0275\u0275property("ngIf", ctx_r2.newPasswordVisible)("ngIfThen", passwordVisible_r6)("ngIfElse", passwordHidden_r7);
    \u0275\u0275advance(3);
    \u0275\u0275property("ngIf", ctx_r2.updateError);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx_r2.updateSuccess);
    \u0275\u0275advance();
    \u0275\u0275property("disabled", ctx_r2.getSubmitButtonState());
    \u0275\u0275advance(4);
    \u0275\u0275property("ngIf", ctx_r2.updateSuccess);
  }
}
function AboutComponent_ng_template_111_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 37);
    \u0275\u0275element(1, "path", 38);
    \u0275\u0275elementEnd();
  }
}
function AboutComponent_ng_template_113_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 37);
    \u0275\u0275element(1, "path", 39);
    \u0275\u0275elementEnd();
  }
}
var AboutComponent = class _AboutComponent {
  constructor() {
    this.settingsService = inject(SettingsService);
    this.websocketService = inject(WebsocketService);
    this.currentPassword = "";
    this.newUsername = "";
    this.newPassword = "";
    this.updateError = "";
    this.updateSuccess = "";
    this.currentPasswordVisible = false;
    this.newPasswordVisible = false;
    this.dialogOpen = false;
  }
  ngOnInit() {
    this.settingsService.getSettings().subscribe((settings) => this.settings = settings);
    this.settingsService.getServerStats().subscribe((serverStats) => this.serverStats = serverStats);
  }
  updatePassword() {
  }
  copyToClipboard(textToCopy) {
    return __async(this, null, function* () {
      if (!navigator.clipboard) {
        const tempInput = document.createElement("input");
        tempInput.value = textToCopy;
        document.body.appendChild(tempInput);
        tempInput.select();
        document.execCommand("copy");
        document.body.removeChild(tempInput);
        this.websocketService.showToast("Copied to clipboard!");
      } else {
        try {
          yield navigator.clipboard.writeText(textToCopy);
          this.websocketService.showToast("Copied to clipboard!");
        } catch (err) {
          this.websocketService.showToast("Error copying text to clipboard.", "Error");
          console.error("Failed to copy: ", err);
        }
      }
      return;
    });
  }
  clearPwUpdateFields() {
    this.currentPassword = "";
    this.newPassword = "";
    this.updateError = "";
    this.updateSuccess = "";
  }
  togglePasswordVisibility(input2) {
    input2.type = input2.type === "password" ? "text" : "password";
  }
  getSubmitButtonState() {
    if (!this.currentPassword) {
      return true;
    }
    let newLoginValid = false;
    if (this.newUsername.length > 0) {
      newLoginValid = true;
    }
    if (this.newPassword.length > 4) {
      newLoginValid = true;
    }
    return !newLoginValid;
  }
  showPwUpdateDialog() {
    this.clearPwUpdateFields();
    this.dialogOpen = true;
    this.passwordUpdateDialog.nativeElement.showModal();
  }
  closePwUpdateDialog() {
    this.clearPwUpdateFields();
    this.passwordUpdateDialog.nativeElement.close();
    this.dialogOpen = false;
  }
  onConfirmUpdate() {
    console.log("Updating password");
    this.updateError = "";
    this.updateSuccess = "";
    this.settingsService.updatePassword(this.currentPassword, this.newUsername, this.newPassword).subscribe((res) => {
      console.log(res);
      if (res.includes("Error")) {
        this.updateError = res;
      } else {
        this.updateSuccess = res;
        setTimeout(() => {
          this.closePwUpdateDialog();
        }, 3e3);
      }
    });
  }
  static {
    this.\u0275fac = function AboutComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _AboutComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _AboutComponent, selectors: [["app-about"]], viewQuery: function AboutComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuery(_c0, 5);
      }
      if (rf & 2) {
        let _t;
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.passwordUpdateDialog = _t.first);
      }
    }, decls: 115, vars: 18, consts: [["passwordUpdateDialog", ""], ["passwordVisible", ""], ["passwordHidden", ""], ["currentPasswordInput", ""], ["newUsernameInput", ""], ["newPasswordInput", ""], [1, "about-container"], [1, "about-section"], [1, "about-content"], ["href", "https://hub.docker.com/r/nandyalu/trailarr", "target", "_blank", 1, "update-available"], [1, "copy", 3, "click"], [1, "update-login", 3, "click"], ["href", "https://nandyalu.github.io/trailarr", "target", "_blank"], ["href", "https://discord.gg/KKPr5kQEzQ", "target", "_blank"], ["href", "https://github.com/nandyalu/trailarr", "target", "_blank"], ["href", "https://github.com/nandyalu/trailarr/issues", "target", "_blank"], ["href", "https://www.reddit.com/r/trailarr", "target", "_blank"], [3, "click"], [1, "dialog-content"], [1, "dialog-content", 3, "click"], [1, "text-input"], [1, "password-input"], ["id", "trailarr_current_password", "type", "password", "autocomplete", "current-password", "required", "", "tabindex", "1", 3, "ngModelChange", "ngModel"], ["for", "trailarr_current_password"], [4, "ngIf", "ngIfThen", "ngIfElse"], ["id", "trailarr_new_username", "type", "text", "autocomplete", "username", "required", "", "tabindex", "1", 3, "ngModelChange", "ngModel"], ["for", "trailarr_new_username"], ["id", "trailer_new_password", "type", "password", "autocomplete", "new-password", "required", "", "minlength", "5", "tabindex", "1", 3, "ngModelChange", "ngModel"], ["for", "trailer_new_password"], ["class", "update-error", 4, "ngIf"], ["class", "update-success", 4, "ngIf"], ["tabindex", "1", "type", "submit", 1, "primary", 3, "click", "disabled"], ["type", "reset", "tabindex", "2", 1, "secondary", 3, "click"], ["class", "close-progress", 4, "ngIf"], [1, "update-error"], [1, "update-success"], [1, "close-progress"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "fill", "#e8eaed"], ["d", "M480.12-330q70.88 0 120.38-49.62t49.5-120.5q0-70.88-49.62-120.38T479.88-670Q409-670 359.5-620.38T310-499.88q0 70.88 49.62 120.38t120.5 49.5Zm-.36-58q-46.76 0-79.26-32.74-32.5-32.73-32.5-79.5 0-46.76 32.74-79.26 32.73-32.5 79.5-32.5 46.76 0 79.26 32.74 32.5 32.73 32.5 79.5 0 46.76-32.74 79.26-32.73 32.5-79.5 32.5Zm.24 188q-146 0-264-83T40-500q58-134 176-217t264-83q146 0 264 83t176 217q-58 134-176 217t-264 83Zm0-300Zm-.17 240Q601-260 702.5-325.5 804-391 857-500q-53-109-154.33-174.5Q601.34-740 480.17-740T257.5-674.5Q156-609 102-500q54 109 155.33 174.5Q358.66-260 479.83-260Z"], ["d", "m629-419-44-44q26-71-27-118t-115-24l-44-44q17-11 38-16t43-5q71 0 120.5 49.5T650-500q0 22-5.5 43.5T629-419Zm129 129-40-40q49-36 85.5-80.5T857-500q-50-111-150-175.5T490-740q-42 0-86 8t-69 19l-46-47q35-16 89.5-28T485-800q143 0 261.5 81.5T920-500q-26 64-67 117t-95 93Zm58 226L648-229q-35 14-79 21.5t-89 7.5q-146 0-265-81.5T40-500q20-52 55.5-101.5T182-696L56-822l42-43 757 757-39 44ZM223-654q-37 27-71.5 71T102-500q51 111 153.5 175.5T488-260q33 0 65-4t48-12l-64-64q-11 5-27 7.5t-30 2.5q-70 0-120-49t-50-121q0-15 2.5-30t7.5-27l-97-97Zm305 142Zm-116 58Z"]], template: function AboutComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275elementStart(0, "div", 6)(1, "section", 7)(2, "h1");
        \u0275\u0275text(3, "About Trailarr");
        \u0275\u0275elementEnd();
        \u0275\u0275element(4, "hr");
        \u0275\u0275elementStart(5, "div", 8)(6, "span");
        \u0275\u0275text(7, "Version");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(8, "code");
        \u0275\u0275text(9);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(10, "a", 9);
        \u0275\u0275text(11);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(12, "div", 8)(13, "span");
        \u0275\u0275text(14, "Yt-dlp Version");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(15, "code");
        \u0275\u0275text(16);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(17, "div", 8)(18, "span");
        \u0275\u0275text(19, "API Key");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(20, "code", 10);
        \u0275\u0275listener("click", function AboutComponent_Template_code_click_20_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.copyToClipboard(ctx.settings.api_key));
        });
        \u0275\u0275text(21);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(22, "div", 8)(23, "span");
        \u0275\u0275text(24, "Appdata Folder");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(25, "code");
        \u0275\u0275text(26);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(27, "div", 8)(28, "span");
        \u0275\u0275text(29, "Server Started");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(30, "code");
        \u0275\u0275text(31);
        \u0275\u0275pipe(32, "timeago");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(33, "div", 8)(34, "span");
        \u0275\u0275text(35, "Timezone");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(36, "code");
        \u0275\u0275text(37);
        \u0275\u0275elementEnd()()();
        \u0275\u0275elementStart(38, "section", 7)(39, "h1");
        \u0275\u0275text(40, "Statistics");
        \u0275\u0275elementEnd();
        \u0275\u0275element(41, "hr");
        \u0275\u0275elementStart(42, "div", 8)(43, "span");
        \u0275\u0275text(44, "Movies");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(45, "code");
        \u0275\u0275text(46);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(47, "div", 8)(48, "span");
        \u0275\u0275text(49, "Movies Monitored");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(50, "code");
        \u0275\u0275text(51);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(52, "div", 8)(53, "span");
        \u0275\u0275text(54, "Series");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(55, "code");
        \u0275\u0275text(56);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(57, "div", 8)(58, "span");
        \u0275\u0275text(59, "Series Monitored");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(60, "code");
        \u0275\u0275text(61);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(62, "div", 8)(63, "span");
        \u0275\u0275text(64, "Trailers Downloaded");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(65, "code");
        \u0275\u0275text(66);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(67, "div", 8)(68, "span");
        \u0275\u0275text(69, "Trailers Detected");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(70, "code");
        \u0275\u0275text(71);
        \u0275\u0275elementEnd()()();
        \u0275\u0275elementStart(72, "section", 7)(73, "h1");
        \u0275\u0275text(74, "Login Credentials");
        \u0275\u0275elementEnd();
        \u0275\u0275element(75, "hr");
        \u0275\u0275elementStart(76, "div", 8)(77, "button", 11);
        \u0275\u0275listener("click", function AboutComponent_Template_button_click_77_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.showPwUpdateDialog());
        });
        \u0275\u0275text(78, "Update Login");
        \u0275\u0275elementEnd()()();
        \u0275\u0275elementStart(79, "section", 7)(80, "h1");
        \u0275\u0275text(81, "Getting Support");
        \u0275\u0275elementEnd();
        \u0275\u0275element(82, "hr");
        \u0275\u0275elementStart(83, "div", 8)(84, "span");
        \u0275\u0275text(85, "Documentation");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(86, "a", 12);
        \u0275\u0275text(87, "https://nandyalu.github.io/trailarr");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(88, "div", 8)(89, "span");
        \u0275\u0275text(90, "Discord");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(91, "a", 13);
        \u0275\u0275text(92, "https://discord.gg/KKPr5kQEzQ");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(93, "div", 8)(94, "span");
        \u0275\u0275text(95, "Github");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(96, "a", 14);
        \u0275\u0275text(97, "https://github.com/nandyalu/trailarr");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(98, "div", 8)(99, "span");
        \u0275\u0275text(100, "Issues");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(101, "a", 15);
        \u0275\u0275text(102, "https://github.com/nandyalu/trailarr/issues");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(103, "div", 8)(104, "span");
        \u0275\u0275text(105, "Reddit");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(106, "a", 16);
        \u0275\u0275text(107, "https://www.reddit.com/r/trailarr");
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(108, "dialog", 17, 0);
        \u0275\u0275listener("click", function AboutComponent_Template_dialog_click_108_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closePwUpdateDialog());
        });
        \u0275\u0275template(110, AboutComponent_Conditional_110_Template, 34, 13, "form", 18);
        \u0275\u0275elementEnd();
        \u0275\u0275template(111, AboutComponent_ng_template_111_Template, 2, 0, "ng-template", null, 1, \u0275\u0275templateRefExtractor)(113, AboutComponent_ng_template_113_Template, 2, 0, "ng-template", null, 2, \u0275\u0275templateRefExtractor);
      }
      if (rf & 2) {
        \u0275\u0275advance(9);
        \u0275\u0275textInterpolate(ctx.settings == null ? null : ctx.settings.version);
        \u0275\u0275advance();
        \u0275\u0275classProp("latest", !(ctx.settings == null ? null : ctx.settings.update_available));
        \u0275\u0275advance();
        \u0275\u0275textInterpolate((ctx.settings == null ? null : ctx.settings.update_available) ? "Update Available" : "Latest");
        \u0275\u0275advance(5);
        \u0275\u0275textInterpolate(ctx.settings == null ? null : ctx.settings.ytdlp_version);
        \u0275\u0275advance(5);
        \u0275\u0275textInterpolate(ctx.settings == null ? null : ctx.settings.api_key);
        \u0275\u0275advance(5);
        \u0275\u0275textInterpolate(ctx.settings == null ? null : ctx.settings.app_data_dir);
        \u0275\u0275advance(5);
        \u0275\u0275textInterpolate((ctx.settings == null ? null : ctx.settings.server_start_time) ? \u0275\u0275pipeBind1(32, 16, ctx.settings == null ? null : ctx.settings.server_start_time) : "Unknwon");
        \u0275\u0275advance(6);
        \u0275\u0275textInterpolate(ctx.settings == null ? null : ctx.settings.timezone);
        \u0275\u0275advance(9);
        \u0275\u0275textInterpolate(ctx.serverStats == null ? null : ctx.serverStats.movies_count);
        \u0275\u0275advance(5);
        \u0275\u0275textInterpolate(ctx.serverStats == null ? null : ctx.serverStats.movies_monitored);
        \u0275\u0275advance(5);
        \u0275\u0275textInterpolate(ctx.serverStats == null ? null : ctx.serverStats.series_count);
        \u0275\u0275advance(5);
        \u0275\u0275textInterpolate(ctx.serverStats == null ? null : ctx.serverStats.series_monitored);
        \u0275\u0275advance(5);
        \u0275\u0275textInterpolate(ctx.serverStats == null ? null : ctx.serverStats.trailers_downloaded);
        \u0275\u0275advance(5);
        \u0275\u0275textInterpolate(ctx.serverStats == null ? null : ctx.serverStats.trailers_detected);
        \u0275\u0275advance(39);
        \u0275\u0275conditional(ctx.dialogOpen ? 110 : -1);
      }
    }, dependencies: [TimeagoModule, TimeagoPipe, NgIf, FormsModule, \u0275NgNoValidate, DefaultValueAccessor, NgControlStatus, NgControlStatusGroup, RequiredValidator, MinLengthValidator, NgModel, NgForm], styles: ["\n\n.about-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n}\n.about-content[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  margin: 1.5rem 0.5rem;\n  gap: 1rem;\n}\n.about-content[_ngcontent-%COMP%]   label[_ngcontent-%COMP%], \n.about-content[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n  font-weight: bold;\n  text-align: left;\n  width: 40%;\n}\n.about-content[_ngcontent-%COMP%]    > [_ngcontent-%COMP%]:nth-child(2) {\n  text-decoration: none;\n  text-align: left;\n  margin: 0;\n  padding: 0.25rem;\n}\n.update-available[_ngcontent-%COMP%] {\n  background-color: var(--color-primary);\n  color: var(--color-on-primary);\n  border-radius: 5px;\n  border-radius: 1rem;\n  padding: 0.25rem 0.5rem;\n  font-style: italic;\n  width: auto !important;\n}\n.latest[_ngcontent-%COMP%] {\n  background-color: var(--color-tertiary);\n  color: var(--color-on-tertiary);\n}\n@media screen and (max-width: 768px) {\n  .about-content[_ngcontent-%COMP%] {\n    flex-direction: column;\n    align-items: flex-start;\n    gap: 0.25rem;\n  }\n  .about-content[_ngcontent-%COMP%]   label[_ngcontent-%COMP%] {\n    width: 100%;\n    font-weight: unset;\n    font-style: italic;\n    font-size: small;\n  }\n}\n.dialog-content[_ngcontent-%COMP%] {\n  min-width: 25vw;\n  padding: 1rem;\n  text-align: center;\n}\n.dialog-content[_ngcontent-%COMP%]   button[_ngcontent-%COMP%] {\n  margin: 1rem;\n}\n.dialog-content[_ngcontent-%COMP%]   .update-success[_ngcontent-%COMP%] {\n  font-weight: bolder;\n  color: var(--color-success);\n}\n.dialog-content[_ngcontent-%COMP%]   .update-error[_ngcontent-%COMP%] {\n  font-weight: bolder;\n  color: var(--color-warning);\n}\n.text-input[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  flex-wrap: wrap;\n  gap: 0.5rem;\n  justify-content: space-between;\n  margin: 1rem;\n  align-items: center;\n}\n.password-input[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  justify-content: space-between;\n  margin: 0.25rem;\n  align-items: center;\n  position: relative;\n}\n.password-input[_ngcontent-%COMP%]   label[_ngcontent-%COMP%] {\n  position: absolute;\n  transform: translateY(-50%);\n  top: 50%;\n  left: 1rem;\n  font-size: 1rem;\n  pointer-events: none;\n  color: var(--color-on-surface);\n  padding: 0 0.5rem;\n  transition: 0.5s;\n}\n.password-input[_ngcontent-%COMP%]   input[_ngcontent-%COMP%] {\n  min-width: 15rem;\n  height: 3rem;\n  padding: 0.25rem 0.5rem;\n  font-family: inherit;\n  font-size: 1.25rem;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-tertiary);\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n}\n.password-input[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]:focus    ~ label[_ngcontent-%COMP%], \n.password-input[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]:valid    ~ label[_ngcontent-%COMP%] {\n  top: 0;\n  background: var(--color-surface-container-high);\n  font-size: 0.8rem;\n}\ni[_ngcontent-%COMP%] {\n  position: absolute;\n  right: 0.5rem;\n  font-size: 0;\n}\nsvg[_ngcontent-%COMP%] {\n  width: 1.5rem;\n  height: 1.5rem;\n  fill: var(--color-secondary);\n}\n.close-progress[_ngcontent-%COMP%] {\n  width: 100%;\n  height: 0.25rem;\n  background-color: var(--color-success-text);\n  border-radius: 0.25rem;\n  animation: _ngcontent-%COMP%_closeProgress 3s linear 0s;\n}\n@keyframes _ngcontent-%COMP%_closeProgress {\n  0% {\n    width: 100%;\n  }\n  100% {\n    width: 0%;\n  }\n}\n/*# sourceMappingURL=about.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(AboutComponent, [{
    type: Component,
    args: [{ selector: "app-about", imports: [TimeagoModule, NgIf, FormsModule], template: `<!-- File: about.component.html -->
<div class="about-container">
  <section class="about-section">
    <h1>About Trailarr</h1>
    <hr />
    <div class="about-content">
      <span>Version</span>
      <code>{{ settings?.version }}</code>
      <a
        class="update-available"
        [class.latest]="!settings?.update_available"
        href="https://hub.docker.com/r/nandyalu/trailarr"
        target="_blank"
        >{{ settings?.update_available ? 'Update Available' : 'Latest' }}</a
      >
    </div>
    <div class="about-content">
      <span>Yt-dlp Version</span>
      <code>{{ settings?.ytdlp_version }}</code>
    </div>
    <div class="about-content">
      <span>API Key</span>
      <code class="copy" (click)="copyToClipboard(settings!.api_key)">{{ settings?.api_key }}</code>
    </div>
    <div class="about-content">
      <span>Appdata Folder</span>
      <code>{{ settings?.app_data_dir }}</code>
    </div>
    <div class="about-content">
      <span>Server Started</span>
      <code>{{ settings?.server_start_time ? (settings?.server_start_time | timeago) : 'Unknwon' }}</code>
    </div>
    <div class="about-content">
      <span>Timezone</span>
      <code>{{ settings?.timezone }}</code>
    </div>
  </section>
  <section class="about-section">
    <h1>Statistics</h1>
    <hr />
    <div class="about-content">
      <span>Movies</span>
      <code>{{ serverStats?.movies_count }}</code>
    </div>
    <div class="about-content">
      <span>Movies Monitored</span>
      <code>{{ serverStats?.movies_monitored }}</code>
    </div>
    <div class="about-content">
      <span>Series</span>
      <code>{{ serverStats?.series_count }}</code>
    </div>
    <div class="about-content">
      <span>Series Monitored</span>
      <code>{{ serverStats?.series_monitored }}</code>
    </div>
    <div class="about-content">
      <span>Trailers Downloaded</span>
      <code>{{ serverStats?.trailers_downloaded }}</code>
    </div>
    <div class="about-content">
      <span>Trailers Detected</span>
      <code>{{ serverStats?.trailers_detected }}</code>
    </div>
  </section>
  <section class="about-section">
    <h1>Login Credentials</h1>
    <hr />
    <div class="about-content">
      <button class="update-login" (click)="showPwUpdateDialog()">Update Login</button>
    </div>
  </section>
  <section class="about-section">
    <h1>Getting Support</h1>
    <hr />
    <div class="about-content">
      <span>Documentation</span>
      <a href="https://nandyalu.github.io/trailarr" target="_blank">https://nandyalu.github.io/trailarr</a>
    </div>
    <div class="about-content">
      <span>Discord</span>
      <a href="https://discord.gg/KKPr5kQEzQ" target="_blank">https://discord.gg/KKPr5kQEzQ</a>
    </div>
    <div class="about-content">
      <span>Github</span>
      <a href="https://github.com/nandyalu/trailarr" target="_blank">https://github.com/nandyalu/trailarr</a>
    </div>
    <div class="about-content">
      <span>Issues</span>
      <a href="https://github.com/nandyalu/trailarr/issues" target="_blank">https://github.com/nandyalu/trailarr/issues</a>
    </div>
    <div class="about-content">
      <span>Reddit</span>
      <a href="https://www.reddit.com/r/trailarr" target="_blank">https://www.reddit.com/r/trailarr</a>
    </div>
  </section>
</div>

<dialog #passwordUpdateDialog (click)="closePwUpdateDialog()">
  @if (dialogOpen) {
    <form class="dialog-content" (click)="$event.stopPropagation()">
      <h2>Update Login Credentials</h2>
      <div class="text-input">
        <!-- <h3>Current Login Password</h3> -->
        <div class="password-input">
          <input
            id="trailarr_current_password"
            type="password"
            [(ngModel)]="currentPassword"
            autocomplete="current-password"
            required
            tabindex="1"
            #currentPasswordInput
          />
          <label for="trailarr_current_password">Current Password</label>
          <i (click)="togglePasswordVisibility(currentPasswordInput); currentPasswordVisible = !currentPasswordVisible">
            <ng-container *ngIf="currentPasswordVisible; then passwordVisible; else passwordHidden"></ng-container>
          </i>
        </div>
        <h3>New Login</h3>
        <div class="password-input">
          <input
            id="trailarr_new_username"
            type="text"
            [(ngModel)]="newUsername"
            autocomplete="username"
            required
            tabindex="1"
            #newUsernameInput
          />
          <label for="trailarr_new_username">New Username</label>
        </div>
        <div class="password-input">
          <input
            id="trailer_new_password"
            type="password"
            [(ngModel)]="newPassword"
            autocomplete="new-password"
            required
            minlength="5"
            tabindex="1"
            #newPasswordInput
          />
          <label for="trailer_new_password">New Password </label>
          <i (click)="togglePasswordVisibility(newPasswordInput); newPasswordVisible = !newPasswordVisible">
            <ng-container *ngIf="newPasswordVisible; then passwordVisible; else passwordHidden"></ng-container>
          </i>
        </div>
        <span>For updating only username/password, leave the other blank</span>
      </div>
      <p class="update-error" *ngIf="updateError">{{ updateError }}</p>
      <p class="update-success" *ngIf="updateSuccess">{{ updateSuccess }}</p>
      <button class="primary" (click)="onConfirmUpdate()" tabindex="1" type="submit" [disabled]="getSubmitButtonState()">Update</button>
      <button class="secondary" (click)="closePwUpdateDialog()" type="reset" tabindex="2">Cancel</button>
      <div class="close-progress" *ngIf="updateSuccess"></div>
    </form>
  }
</dialog>

<ng-template #passwordVisible>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" fill="#e8eaed">
    <!-- Visible Icon -->
    <path
      d="M480.12-330q70.88 0 120.38-49.62t49.5-120.5q0-70.88-49.62-120.38T479.88-670Q409-670 359.5-620.38T310-499.88q0 70.88 49.62 120.38t120.5 49.5Zm-.36-58q-46.76 0-79.26-32.74-32.5-32.73-32.5-79.5 0-46.76 32.74-79.26 32.73-32.5 79.5-32.5 46.76 0 79.26 32.74 32.5 32.73 32.5 79.5 0 46.76-32.74 79.26-32.73 32.5-79.5 32.5Zm.24 188q-146 0-264-83T40-500q58-134 176-217t264-83q146 0 264 83t176 217q-58 134-176 217t-264 83Zm0-300Zm-.17 240Q601-260 702.5-325.5 804-391 857-500q-53-109-154.33-174.5Q601.34-740 480.17-740T257.5-674.5Q156-609 102-500q54 109 155.33 174.5Q358.66-260 479.83-260Z"
    />
  </svg>
</ng-template>

<ng-template #passwordHidden>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" fill="#e8eaed">
    <!-- Hidden Icon -->
    <path
      d="m629-419-44-44q26-71-27-118t-115-24l-44-44q17-11 38-16t43-5q71 0 120.5 49.5T650-500q0 22-5.5 43.5T629-419Zm129 129-40-40q49-36 85.5-80.5T857-500q-50-111-150-175.5T490-740q-42 0-86 8t-69 19l-46-47q35-16 89.5-28T485-800q143 0 261.5 81.5T920-500q-26 64-67 117t-95 93Zm58 226L648-229q-35 14-79 21.5t-89 7.5q-146 0-265-81.5T40-500q20-52 55.5-101.5T182-696L56-822l42-43 757 757-39 44ZM223-654q-37 27-71.5 71T102-500q51 111 153.5 175.5T488-260q33 0 65-4t48-12l-64-64q-11 5-27 7.5t-30 2.5q-70 0-120-49t-50-121q0-15 2.5-30t7.5-27l-97-97Zm305 142Zm-116 58Z"
    />
  </svg>
</ng-template>
`, styles: ["/* src/app/settings/about/about.component.scss */\n.about-container {\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n}\n.about-content {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  margin: 1.5rem 0.5rem;\n  gap: 1rem;\n}\n.about-content label,\n.about-content span {\n  font-weight: bold;\n  text-align: left;\n  width: 40%;\n}\n.about-content > :nth-child(2) {\n  text-decoration: none;\n  text-align: left;\n  margin: 0;\n  padding: 0.25rem;\n}\n.update-available {\n  background-color: var(--color-primary);\n  color: var(--color-on-primary);\n  border-radius: 5px;\n  border-radius: 1rem;\n  padding: 0.25rem 0.5rem;\n  font-style: italic;\n  width: auto !important;\n}\n.latest {\n  background-color: var(--color-tertiary);\n  color: var(--color-on-tertiary);\n}\n@media screen and (max-width: 768px) {\n  .about-content {\n    flex-direction: column;\n    align-items: flex-start;\n    gap: 0.25rem;\n  }\n  .about-content label {\n    width: 100%;\n    font-weight: unset;\n    font-style: italic;\n    font-size: small;\n  }\n}\n.dialog-content {\n  min-width: 25vw;\n  padding: 1rem;\n  text-align: center;\n}\n.dialog-content button {\n  margin: 1rem;\n}\n.dialog-content .update-success {\n  font-weight: bolder;\n  color: var(--color-success);\n}\n.dialog-content .update-error {\n  font-weight: bolder;\n  color: var(--color-warning);\n}\n.text-input {\n  display: flex;\n  flex-direction: column;\n  flex-wrap: wrap;\n  gap: 0.5rem;\n  justify-content: space-between;\n  margin: 1rem;\n  align-items: center;\n}\n.password-input {\n  display: flex;\n  flex-direction: row;\n  justify-content: space-between;\n  margin: 0.25rem;\n  align-items: center;\n  position: relative;\n}\n.password-input label {\n  position: absolute;\n  transform: translateY(-50%);\n  top: 50%;\n  left: 1rem;\n  font-size: 1rem;\n  pointer-events: none;\n  color: var(--color-on-surface);\n  padding: 0 0.5rem;\n  transition: 0.5s;\n}\n.password-input input {\n  min-width: 15rem;\n  height: 3rem;\n  padding: 0.25rem 0.5rem;\n  font-family: inherit;\n  font-size: 1.25rem;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-tertiary);\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n}\n.password-input input:focus ~ label,\n.password-input input:valid ~ label {\n  top: 0;\n  background: var(--color-surface-container-high);\n  font-size: 0.8rem;\n}\ni {\n  position: absolute;\n  right: 0.5rem;\n  font-size: 0;\n}\nsvg {\n  width: 1.5rem;\n  height: 1.5rem;\n  fill: var(--color-secondary);\n}\n.close-progress {\n  width: 100%;\n  height: 0.25rem;\n  background-color: var(--color-success-text);\n  border-radius: 0.25rem;\n  animation: closeProgress 3s linear 0s;\n}\n@keyframes closeProgress {\n  0% {\n    width: 100%;\n  }\n  100% {\n    width: 0%;\n  }\n}\n/*# sourceMappingURL=about.component.css.map */\n"] }]
  }], null, { passwordUpdateDialog: [{
    type: ViewChild,
    args: ["passwordUpdateDialog"]
  }] });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(AboutComponent, { className: "AboutComponent", filePath: "src/app/settings/about/about.component.ts", lineNumber: 15 });
})();

// src/app/settings/connections/add-connection/add-connection.component.ts
var _c02 = ["cancelDialog"];
function AddConnectionComponent_p_9_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 32);
    \u0275\u0275text(1, "Server Name is required! Minimum 3 characters");
    \u0275\u0275elementEnd();
  }
}
function AddConnectionComponent_div_15_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 33);
    \u0275\u0275listener("click", function AddConnectionComponent_div_15_Template_div_click_0_listener() {
      const option_r3 = \u0275\u0275restoreView(_r2).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setArrType(option_r3));
    })("keydown.enter", function AddConnectionComponent_div_15_Template_div_keydown_enter_0_listener() {
      const option_r3 = \u0275\u0275restoreView(_r2).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setArrType(option_r3));
    })("keydown.space", function AddConnectionComponent_div_15_Template_div_keydown_space_0_listener() {
      const option_r3 = \u0275\u0275restoreView(_r2).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setArrType(option_r3));
    });
    \u0275\u0275text(1);
    \u0275\u0275pipe(2, "uppercase");
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const option_r3 = ctx.$implicit;
    const ctx_r3 = \u0275\u0275nextContext();
    \u0275\u0275classProp("selected", option_r3 === ctx_r3.addConnectionForm.value.arrType);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", \u0275\u0275pipeBind1(2, 3, option_r3), " ");
  }
}
function AddConnectionComponent_div_20_Template(rf, ctx) {
  if (rf & 1) {
    const _r5 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 34);
    \u0275\u0275listener("click", function AddConnectionComponent_div_20_Template_div_click_0_listener() {
      const option_r6 = \u0275\u0275restoreView(_r5).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setMonitorType(option_r6));
    })("keydown.enter", function AddConnectionComponent_div_20_Template_div_keydown_enter_0_listener() {
      const option_r6 = \u0275\u0275restoreView(_r5).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setMonitorType(option_r6));
    })("keydown.space", function AddConnectionComponent_div_20_Template_div_keydown_space_0_listener() {
      const option_r6 = \u0275\u0275restoreView(_r5).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setMonitorType(option_r6));
    });
    \u0275\u0275text(1);
    \u0275\u0275pipe(2, "uppercase");
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const option_r6 = ctx.$implicit;
    const ctx_r3 = \u0275\u0275nextContext();
    \u0275\u0275classProp("selected", option_r6 === ctx_r3.addConnectionForm.value.monitorType);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", \u0275\u0275pipeBind1(2, 3, option_r6), " ");
  }
}
function AddConnectionComponent_p_25_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 32);
    \u0275\u0275text(1, "Server URL is invalid!");
    \u0275\u0275elementEnd();
  }
}
function AddConnectionComponent_p_30_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 32);
    \u0275\u0275text(1, "APIKey is invalid!");
    \u0275\u0275elementEnd();
  }
}
function AddConnectionComponent_div_35_Template(rf, ctx) {
  if (rf & 1) {
    const _r7 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 35)(1, "div", 3)(2, "label", 36);
    \u0275\u0275text(3, "Path From");
    \u0275\u0275elementEnd();
    \u0275\u0275element(4, "input", 37);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(5, "div", 3)(6, "label", 38);
    \u0275\u0275text(7, "Path To");
    \u0275\u0275elementEnd();
    \u0275\u0275element(8, "input", 39);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(9, "button", 40);
    \u0275\u0275listener("click", function AddConnectionComponent_div_35_Template_button_click_9_listener() {
      const i_r8 = \u0275\u0275restoreView(_r7).index;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.removePathMapping(i_r8));
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(10, "svg", 20);
    \u0275\u0275element(11, "path", 24);
    \u0275\u0275elementEnd()()();
  }
  if (rf & 2) {
    const i_r8 = ctx.index;
    \u0275\u0275property("formGroupName", i_r8);
  }
}
function AddConnectionComponent_p_53_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p");
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r3 = \u0275\u0275nextContext();
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(ctx_r3.addConnResult);
  }
}
var AddConnectionComponent = class _AddConnectionComponent {
  constructor() {
    this._location = inject(Location);
    this.settingsService = inject(SettingsService);
    this.arrOptions = ["radarr", "sonarr"];
    this.monitorOptions = ["missing", "new", "none", "sync"];
    this.name = new FormControl("", [Validators.required, Validators.minLength(3)]);
    this.url = new FormControl("", [Validators.required, Validators.pattern("https?://.*"), Validators.minLength(10)]);
    this.apiKey = new FormControl("", [
      Validators.required,
      Validators.pattern("^[a-zA-Z0-9]*$"),
      Validators.minLength(32),
      Validators.maxLength(50)
    ]);
    this.addConnectionForm = new FormGroup({
      name: this.name,
      arrType: new FormControl("radarr"),
      monitorType: new FormControl("new"),
      url: this.url,
      apiKey: this.apiKey,
      path_mappings: new FormArray([])
    });
    this.addConnResult = "";
  }
  setArrType(selectedArrType) {
    this.addConnectionForm.patchValue({ arrType: selectedArrType });
    this.addConnectionForm.markAsTouched();
    this.addConnectionForm.markAsDirty();
  }
  setMonitorType(selectedMonitorType) {
    this.addConnectionForm.patchValue({ monitorType: selectedMonitorType });
    this.addConnectionForm.markAsTouched();
    this.addConnectionForm.markAsDirty();
  }
  get pathMappings() {
    return this.addConnectionForm.get("path_mappings");
  }
  addPathMapping() {
    const pathMappingGroup = new FormGroup({
      path_from: new FormControl("", Validators.required),
      path_to: new FormControl("", Validators.required)
    });
    this.pathMappings.push(pathMappingGroup);
    this.addConnectionForm.markAsTouched();
    this.addConnectionForm.markAsDirty();
  }
  removePathMapping(index) {
    this.pathMappings.removeAt(index);
    this.addConnectionForm.markAsTouched();
    this.addConnectionForm.markAsDirty();
  }
  showCancelDialog() {
    this.cancelDialog.nativeElement.showModal();
  }
  closeCancelDialog() {
    this.cancelDialog.nativeElement.close();
  }
  onCancel() {
    if (this.addConnectionForm.dirty) {
      this.showCancelDialog();
    } else {
      this._location.back();
    }
  }
  onConfirmCancel() {
    this.showCancelDialog();
    this._location.back();
  }
  onSubmit() {
    if (this.addConnectionForm.invalid) {
      return;
    }
    const newConnection = {
      name: this.addConnectionForm.value.name || "",
      arr_type: this.addConnectionForm.value.arrType || "",
      url: this.addConnectionForm.value.url || "",
      api_key: this.addConnectionForm.value.apiKey || "",
      monitor: this.addConnectionForm.value.monitorType || "",
      path_mappings: this.addConnectionForm.value.path_mappings || []
    };
    this.settingsService.addConnection(newConnection).subscribe((result) => {
      this.addConnResult = result;
      if (result.toLowerCase().includes("version")) {
        setTimeout(() => {
          this._location.back();
        }, 3e3);
      }
    });
  }
  static {
    this.\u0275fac = function AddConnectionComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _AddConnectionComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _AddConnectionComponent, selectors: [["app-add-connection"]], viewQuery: function AddConnectionComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuery(_c02, 5);
      }
      if (rf & 2) {
        let _t;
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.cancelDialog = _t.first);
      }
    }, decls: 65, vars: 9, consts: [["cancelDialog", ""], [1, "form-container"], [3, "formGroup"], [1, "input-group"], ["for", "name"], ["id", "name", "type", "text", "formControlName", "name", "placeholder", "Connection Name", "autocomplete", "off", "autocapitalize", "words", "tabindex", "1", "oninput", "this.value = this.value.charAt(0).toUpperCase() + this.value.slice(1)"], ["class", "invalid-text", 4, "ngIf"], [1, "d-row"], [1, "option-container"], ["id", "arrtype", 1, "options-bar"], ["class", "option", "tabindex", "2", 3, "selected", "click", "keydown.enter", "keydown.space", 4, "ngFor", "ngForOf"], ["id", "monitorType", 1, "options-bar"], ["class", "option", "tabindex", "3", 3, "selected", "click", "keydown.enter", "keydown.space", 4, "ngFor", "ngForOf"], ["for", "url"], ["id", "url", "type", "url", "formControlName", "url", "placeholder", "Server URL Ex: http://192.168.0.15:6969", "tabindex", "4", "autocomplete", "off"], ["for", "apiKey"], ["id", "apiKey", "type", "text", "formControlName", "apiKey", "placeholder", "APIKEY", "tabindex", "5", "autocomplete", "off"], ["formArrayName", "path_mappings"], ["class", "d-row", 3, "formGroupName", 4, "ngFor", "ngForOf"], ["id", "cancel", "tabindex", "10", 1, "animated-button", "tertiary", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z"], [1, "text"], ["id", "cancel", "tabindex", "11", 1, "animated-button", "secondary", 3, "click"], ["d", "m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z"], ["id", "submit", "type", "submit", "tabindex", "12", 1, "animated-button", "primary", 3, "click", "disabled"], ["d", "M840-680v480q0 33-23.5 56.5T760-120H200q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h480l160 160Zm-80 34L646-760H200v560h560v-446ZM480-240q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35ZM240-560h360v-160H240v160Zm-40-86v446-560 114Z"], [4, "ngIf"], [3, "click"], [1, "dialog-content", 3, "click"], ["tabindex", "2", 1, "secondary", 3, "click"], ["tabindex", "1", 1, "primary", 3, "click"], [1, "invalid-text"], ["tabindex", "2", 1, "option", 3, "click", "keydown.enter", "keydown.space"], ["tabindex", "3", 1, "option", 3, "click", "keydown.enter", "keydown.space"], [1, "d-row", 3, "formGroupName"], ["for", "path_from"], ["id", "path_from", "type", "text", "formControlName", "path_from", "placeholder", "Arr Internal Path", "tabindex", "6", "autocomplete", "off"], ["for", "path_to"], ["id", "path_to", "type", "text", "formControlName", "path_to", "placeholder", "Trailarr Internal Path", "tabindex", "6", "autocomplete", "off"], ["id", "remove", "name", "Remove Path Mapping", "tabindex", "6", 1, "icononly-button", "tertiary", 3, "click"]], template: function AddConnectionComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275elementStart(0, "div", 1)(1, "h2");
        \u0275\u0275text(2, "Add Connection:");
        \u0275\u0275elementEnd();
        \u0275\u0275element(3, "hr");
        \u0275\u0275elementStart(4, "form", 2)(5, "div", 3)(6, "label", 4);
        \u0275\u0275text(7, "Connection Name");
        \u0275\u0275elementEnd();
        \u0275\u0275element(8, "input", 5);
        \u0275\u0275template(9, AddConnectionComponent_p_9_Template, 2, 0, "p", 6);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(10, "div", 7)(11, "div", 8)(12, "span");
        \u0275\u0275text(13, "Arr Type: ");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(14, "div", 9);
        \u0275\u0275template(15, AddConnectionComponent_div_15_Template, 3, 5, "div", 10);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(16, "div", 8)(17, "span");
        \u0275\u0275text(18, "Monitor Type: ");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(19, "div", 11);
        \u0275\u0275template(20, AddConnectionComponent_div_20_Template, 3, 5, "div", 12);
        \u0275\u0275elementEnd()()();
        \u0275\u0275elementStart(21, "div", 3)(22, "label", 13);
        \u0275\u0275text(23, "Server URL");
        \u0275\u0275elementEnd();
        \u0275\u0275element(24, "input", 14);
        \u0275\u0275template(25, AddConnectionComponent_p_25_Template, 2, 0, "p", 6);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(26, "div", 3)(27, "label", 15);
        \u0275\u0275text(28, "API Key");
        \u0275\u0275elementEnd();
        \u0275\u0275element(29, "input", 16);
        \u0275\u0275template(30, AddConnectionComponent_p_30_Template, 2, 0, "p", 6);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(31, "h3");
        \u0275\u0275text(32, "Path Mappings:");
        \u0275\u0275elementEnd();
        \u0275\u0275element(33, "hr");
        \u0275\u0275elementStart(34, "div", 17);
        \u0275\u0275template(35, AddConnectionComponent_div_35_Template, 12, 1, "div", 18);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(36, "div", 7)(37, "button", 19);
        \u0275\u0275listener("click", function AddConnectionComponent_Template_button_click_37_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.addPathMapping());
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(38, "svg", 20);
        \u0275\u0275element(39, "path", 21);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(40, "span", 22);
        \u0275\u0275text(41, "Add Path Mapping");
        \u0275\u0275elementEnd()()();
        \u0275\u0275elementStart(42, "div", 7)(43, "button", 23);
        \u0275\u0275listener("click", function AddConnectionComponent_Template_button_click_43_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onCancel());
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(44, "svg", 20);
        \u0275\u0275element(45, "path", 24);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(46, "span", 22);
        \u0275\u0275text(47, "Cancel");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(48, "button", 25);
        \u0275\u0275listener("click", function AddConnectionComponent_Template_button_click_48_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onSubmit());
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(49, "svg", 20);
        \u0275\u0275element(50, "path", 26);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(51, "span", 22);
        \u0275\u0275text(52, "submit");
        \u0275\u0275elementEnd()()();
        \u0275\u0275template(53, AddConnectionComponent_p_53_Template, 2, 1, "p", 27);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(54, "dialog", 28, 0);
        \u0275\u0275listener("click", function AddConnectionComponent_Template_dialog_click_54_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeCancelDialog());
        });
        \u0275\u0275elementStart(56, "div", 29);
        \u0275\u0275listener("click", function AddConnectionComponent_Template_div_click_56_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(57, "h2");
        \u0275\u0275text(58, "Unsaved Changes");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(59, "p");
        \u0275\u0275text(60, "Canges will be lost. Are you sure you want to cancel?");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(61, "button", 30);
        \u0275\u0275listener("click", function AddConnectionComponent_Template_button_click_61_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onConfirmCancel());
        });
        \u0275\u0275text(62, "Yes");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(63, "button", 31);
        \u0275\u0275listener("click", function AddConnectionComponent_Template_button_click_63_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeCancelDialog());
        });
        \u0275\u0275text(64, "No");
        \u0275\u0275elementEnd()()();
      }
      if (rf & 2) {
        \u0275\u0275advance(4);
        \u0275\u0275property("formGroup", ctx.addConnectionForm);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngIf", ctx.name.invalid && ctx.name.touched);
        \u0275\u0275advance(6);
        \u0275\u0275property("ngForOf", ctx.arrOptions);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngForOf", ctx.monitorOptions);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngIf", ctx.url.invalid && ctx.url.touched);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngIf", ctx.apiKey.invalid && ctx.apiKey.touched);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngForOf", ctx.pathMappings.controls);
        \u0275\u0275advance(13);
        \u0275\u0275property("disabled", !ctx.addConnectionForm.valid);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngIf", ctx.addConnResult);
      }
    }, dependencies: [ReactiveFormsModule, \u0275NgNoValidate, DefaultValueAccessor, NgControlStatus, NgControlStatusGroup, FormGroupDirective, FormControlName, FormGroupName, FormArrayName, FormsModule, NgForOf, NgIf, UpperCasePipe], styles: ["\n\n.form-container[_ngcontent-%COMP%] {\n  width: 100%;\n  border: 2px solid var(--color-outline);\n  padding: 24px;\n  display: flex;\n  flex-direction: column;\n  box-sizing: border-box;\n  position: relative;\n  border-radius: 16px;\n  background-color: var(--color-surface-container);\n  transition-property: opacity;\n  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);\n  transition-duration: 0.15s;\n}\n.form-container[_ngcontent-%COMP%]   form[_ngcontent-%COMP%] {\n  display: block;\n  padding: 0;\n  border: var(--color-outline);\n  border-radius: 8px;\n}\n.input-group[_ngcontent-%COMP%] {\n  flex-grow: 1;\n  display: flex;\n  flex-direction: column;\n  gap: 2px;\n  margin-bottom: 1rem;\n}\n.input-group[_ngcontent-%COMP%]   label[_ngcontent-%COMP%] {\n  margin-right: 10px;\n  display: block;\n  margin-bottom: 5px;\n}\n.input-group[_ngcontent-%COMP%]   input[_ngcontent-%COMP%] {\n  width: auto;\n  padding: 12px;\n  font-family: inherit;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  border: 2px solid var(--color-outline);\n  border-radius: 8px;\n}\ninput.ng-touched.ng-invalid[_ngcontent-%COMP%] {\n  border: 2px solid var(--color-error);\n  opacity: 0.6;\n  background-color: var(--color-error-container);\n  color: var(--color-on-error-container);\n  font-weight: 700;\n}\n.input-group[_ngcontent-%COMP%]   .invalid-text[_ngcontent-%COMP%] {\n  color: var(--color-error);\n}\n.d-row[_ngcontent-%COMP%] {\n  display: flex;\n  gap: 1rem;\n  flex-wrap: wrap;\n  margin-bottom: 1rem;\n  justify-content: space-around;\n  align-items: center;\n}\n.option-container[_ngcontent-%COMP%] {\n  display: flex;\n  align-items: center;\n  margin: 1rem 0 0;\n}\n.option-container[_ngcontent-%COMP%]   label[_ngcontent-%COMP%], \n.option-container[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n  padding: 10px;\n  padding-left: 0;\n  display: block;\n  margin-right: 10px;\n  background-color: var(--color-surface-container);\n}\n.option-container[_ngcontent-%COMP%]   .options-bar[_ngcontent-%COMP%] {\n  display: flex;\n  background-color: var(--color-surface-container-high);\n  border-radius: 10px;\n  border: 0.5px solid var(--color-outline);\n}\n.option-container[_ngcontent-%COMP%]   .option[_ngcontent-%COMP%] {\n  padding: 10px;\n  cursor: pointer;\n  border-radius: 10px;\n  transition: 0.3s ease;\n}\n.option-container[_ngcontent-%COMP%]   .selected[_ngcontent-%COMP%] {\n  background-color: var(--color-tertiary-container);\n  font-weight: 600;\n  color: var(--color-on-tertiary-container);\n}\n.dialog-content[_ngcontent-%COMP%] {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog[_ngcontent-%COMP%]::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content[_ngcontent-%COMP%]   button[_ngcontent-%COMP%] {\n  margin: 10px;\n}\n/*# sourceMappingURL=add-connection.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(AddConnectionComponent, [{
    type: Component,
    args: [{ selector: "app-add-connection", imports: [ReactiveFormsModule, FormsModule, NgForOf, NgIf, UpperCasePipe], template: '<div class="form-container">\n  <h2>Add Connection:</h2>\n  <hr />\n  <form [formGroup]="addConnectionForm">\n    <div class="input-group">\n      <label for="name">Connection Name</label>\n      <input\n        id="name"\n        type="text"\n        formControlName="name"\n        placeholder="Connection Name"\n        autocomplete="off"\n        autocapitalize="words"\n        tabindex="1"\n        oninput="this.value = this.value.charAt(0).toUpperCase() + this.value.slice(1)"\n      />\n      <p *ngIf="name.invalid && name.touched" class="invalid-text">Server Name is required! Minimum 3 characters</p>\n    </div>\n\n    <div class="d-row">\n      <div class="option-container">\n        <span>Arr Type: </span>\n        <div id="arrtype" class="options-bar">\n          <div\n            *ngFor="let option of arrOptions"\n            class="option"\n            tabindex="2"\n            [class.selected]="option === addConnectionForm.value.arrType"\n            (click)="setArrType(option)"\n            (keydown.enter)="setArrType(option)"\n            (keydown.space)="setArrType(option)"\n          >\n            {{ option | uppercase }}\n          </div>\n        </div>\n      </div>\n\n      <div class="option-container">\n        <span>Monitor Type: </span>\n        <div id="monitorType" class="options-bar">\n          <div\n            *ngFor="let option of monitorOptions"\n            class="option"\n            tabindex="3"\n            [class.selected]="option === addConnectionForm.value.monitorType"\n            (click)="setMonitorType(option)"\n            (keydown.enter)="setMonitorType(option)"\n            (keydown.space)="setMonitorType(option)"\n          >\n            {{ option | uppercase }}\n          </div>\n        </div>\n      </div>\n    </div>\n\n    <div class="input-group">\n      <label for="url">Server URL</label>\n      <input\n        id="url"\n        type="url"\n        formControlName="url"\n        placeholder="Server URL Ex: http://192.168.0.15:6969"\n        tabindex="4"\n        autocomplete="off"\n      />\n      <p *ngIf="url.invalid && url.touched" class="invalid-text">Server URL is invalid!</p>\n    </div>\n\n    <div class="input-group">\n      <label for="apiKey">API Key</label>\n      <input id="apiKey" type="text" formControlName="apiKey" placeholder="APIKEY" tabindex="5" autocomplete="off" />\n      <p *ngIf="apiKey.invalid && apiKey.touched" class="invalid-text">APIKey is invalid!</p>\n    </div>\n    <h3>Path Mappings:</h3>\n    <hr />\n    <div formArrayName="path_mappings">\n      <div *ngFor="let path_mapping of pathMappings.controls; let i = index" [formGroupName]="i" class="d-row">\n        <div class="input-group">\n          <label for="path_from">Path From</label>\n          <input id="path_from" type="text" formControlName="path_from" placeholder="Arr Internal Path" tabindex="6" autocomplete="off" />\n        </div>\n        <div class="input-group">\n          <label for="path_to">Path To</label>\n          <input id="path_to" type="text" formControlName="path_to" placeholder="Trailarr Internal Path" tabindex="6" autocomplete="off" />\n        </div>\n        <button class="icononly-button tertiary" id="remove" name="Remove Path Mapping" tabindex="6" (click)="removePathMapping(i)">\n          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n            <path d="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z" />\n          </svg>\n          <!-- <span class="text">Remove</span> -->\n        </button>\n      </div>\n    </div>\n    <div class="d-row">\n      <button class="animated-button tertiary" id="cancel" tabindex="10" (click)="addPathMapping()">\n        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n          <path d="M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z" />\n        </svg>\n        <span class="text">Add Path Mapping</span>\n      </button>\n    </div>\n    <div class="d-row">\n      <button class="animated-button secondary" id="cancel" tabindex="11" (click)="onCancel()">\n        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n          <path d="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z" />\n        </svg>\n        <span class="text">Cancel</span>\n      </button>\n\n      <button\n        class="animated-button primary"\n        id="submit"\n        type="submit"\n        tabindex="12"\n        [disabled]="!addConnectionForm.valid"\n        (click)="onSubmit()"\n      >\n        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n          <path\n            d="M840-680v480q0 33-23.5 56.5T760-120H200q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h480l160 160Zm-80 34L646-760H200v560h560v-446ZM480-240q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35ZM240-560h360v-160H240v160Zm-40-86v446-560 114Z"\n          />\n        </svg>\n        <span class="text">submit</span>\n      </button>\n    </div>\n    <p *ngIf="addConnResult">{{ addConnResult }}</p>\n  </form>\n</div>\n<dialog #cancelDialog (click)="closeCancelDialog()">\n  <div class="dialog-content" (click)="$event.stopPropagation()">\n    <h2>Unsaved Changes</h2>\n    <p>Canges will be lost. Are you sure you want to cancel?</p>\n    <button class="secondary" (click)="onConfirmCancel()" tabindex="2">Yes</button>\n    <button class="primary" (click)="closeCancelDialog()" tabindex="1">No</button>\n  </div>\n</dialog>\n', styles: ["/* src/app/settings/connections/add-connection/add-connection.component.scss */\n.form-container {\n  width: 100%;\n  border: 2px solid var(--color-outline);\n  padding: 24px;\n  display: flex;\n  flex-direction: column;\n  box-sizing: border-box;\n  position: relative;\n  border-radius: 16px;\n  background-color: var(--color-surface-container);\n  transition-property: opacity;\n  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);\n  transition-duration: 0.15s;\n}\n.form-container form {\n  display: block;\n  padding: 0;\n  border: var(--color-outline);\n  border-radius: 8px;\n}\n.input-group {\n  flex-grow: 1;\n  display: flex;\n  flex-direction: column;\n  gap: 2px;\n  margin-bottom: 1rem;\n}\n.input-group label {\n  margin-right: 10px;\n  display: block;\n  margin-bottom: 5px;\n}\n.input-group input {\n  width: auto;\n  padding: 12px;\n  font-family: inherit;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  border: 2px solid var(--color-outline);\n  border-radius: 8px;\n}\ninput.ng-touched.ng-invalid {\n  border: 2px solid var(--color-error);\n  opacity: 0.6;\n  background-color: var(--color-error-container);\n  color: var(--color-on-error-container);\n  font-weight: 700;\n}\n.input-group .invalid-text {\n  color: var(--color-error);\n}\n.d-row {\n  display: flex;\n  gap: 1rem;\n  flex-wrap: wrap;\n  margin-bottom: 1rem;\n  justify-content: space-around;\n  align-items: center;\n}\n.option-container {\n  display: flex;\n  align-items: center;\n  margin: 1rem 0 0;\n}\n.option-container label,\n.option-container span {\n  padding: 10px;\n  padding-left: 0;\n  display: block;\n  margin-right: 10px;\n  background-color: var(--color-surface-container);\n}\n.option-container .options-bar {\n  display: flex;\n  background-color: var(--color-surface-container-high);\n  border-radius: 10px;\n  border: 0.5px solid var(--color-outline);\n}\n.option-container .option {\n  padding: 10px;\n  cursor: pointer;\n  border-radius: 10px;\n  transition: 0.3s ease;\n}\n.option-container .selected {\n  background-color: var(--color-tertiary-container);\n  font-weight: 600;\n  color: var(--color-on-tertiary-container);\n}\n.dialog-content {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content button {\n  margin: 10px;\n}\n/*# sourceMappingURL=add-connection.component.css.map */\n"] }]
  }], null, { cancelDialog: [{
    type: ViewChild,
    args: ["cancelDialog"]
  }] });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(AddConnectionComponent, { className: "AddConnectionComponent", filePath: "src/app/settings/connections/add-connection/add-connection.component.ts", lineNumber: 13 });
})();

// src/app/settings/connections/edit-connection/edit-connection.component.ts
var _c03 = ["cancelDialog"];
function EditConnectionComponent_p_9_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 32);
    \u0275\u0275text(1, "Server Name is required! Minimum 3 characters");
    \u0275\u0275elementEnd();
  }
}
function EditConnectionComponent_div_15_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 33);
    \u0275\u0275listener("click", function EditConnectionComponent_div_15_Template_div_click_0_listener() {
      const option_r3 = \u0275\u0275restoreView(_r2).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setArrType(option_r3));
    })("keydown.enter", function EditConnectionComponent_div_15_Template_div_keydown_enter_0_listener() {
      const option_r3 = \u0275\u0275restoreView(_r2).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setArrType(option_r3));
    })("keydown.space", function EditConnectionComponent_div_15_Template_div_keydown_space_0_listener() {
      const option_r3 = \u0275\u0275restoreView(_r2).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setArrType(option_r3));
    });
    \u0275\u0275text(1);
    \u0275\u0275pipe(2, "uppercase");
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const option_r3 = ctx.$implicit;
    const ctx_r3 = \u0275\u0275nextContext();
    \u0275\u0275classProp("selected", option_r3 === ctx_r3.editConnectionForm.value.arrType);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", \u0275\u0275pipeBind1(2, 3, option_r3), " ");
  }
}
function EditConnectionComponent_div_20_Template(rf, ctx) {
  if (rf & 1) {
    const _r5 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 34);
    \u0275\u0275listener("click", function EditConnectionComponent_div_20_Template_div_click_0_listener() {
      const option_r6 = \u0275\u0275restoreView(_r5).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setMonitorType(option_r6));
    })("keydown.enter", function EditConnectionComponent_div_20_Template_div_keydown_enter_0_listener() {
      const option_r6 = \u0275\u0275restoreView(_r5).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setMonitorType(option_r6));
    })("keydown.space", function EditConnectionComponent_div_20_Template_div_keydown_space_0_listener() {
      const option_r6 = \u0275\u0275restoreView(_r5).$implicit;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.setMonitorType(option_r6));
    });
    \u0275\u0275text(1);
    \u0275\u0275pipe(2, "uppercase");
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const option_r6 = ctx.$implicit;
    const ctx_r3 = \u0275\u0275nextContext();
    \u0275\u0275classProp("selected", option_r6 === ctx_r3.editConnectionForm.value.monitorType);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", \u0275\u0275pipeBind1(2, 3, option_r6), " ");
  }
}
function EditConnectionComponent_p_25_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 32);
    \u0275\u0275text(1, "Server URL is invalid!");
    \u0275\u0275elementEnd();
  }
}
function EditConnectionComponent_p_30_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 32);
    \u0275\u0275text(1, "APIKey is invalid!");
    \u0275\u0275elementEnd();
  }
}
function EditConnectionComponent_div_35_Template(rf, ctx) {
  if (rf & 1) {
    const _r7 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 35)(1, "div", 3)(2, "label", 36);
    \u0275\u0275text(3, "Path From");
    \u0275\u0275elementEnd();
    \u0275\u0275element(4, "input", 37);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(5, "div", 3)(6, "label", 38);
    \u0275\u0275text(7, "Path To");
    \u0275\u0275elementEnd();
    \u0275\u0275element(8, "input", 39);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(9, "button", 40);
    \u0275\u0275listener("click", function EditConnectionComponent_div_35_Template_button_click_9_listener() {
      const i_r8 = \u0275\u0275restoreView(_r7).index;
      const ctx_r3 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r3.removePathMapping(i_r8));
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(10, "svg", 20);
    \u0275\u0275element(11, "path", 24);
    \u0275\u0275elementEnd()()();
  }
  if (rf & 2) {
    const i_r8 = ctx.index;
    \u0275\u0275property("formGroupName", i_r8);
  }
}
function EditConnectionComponent_p_53_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p");
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r3 = \u0275\u0275nextContext();
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(ctx_r3.addConnResult);
  }
}
var EditConnectionComponent = class _EditConnectionComponent {
  constructor() {
    this._location = inject(Location);
    this.route = inject(ActivatedRoute);
    this.settingsService = inject(SettingsService);
    this.connectionId = 0;
    this.arrOptions = ["radarr", "sonarr"];
    this.monitorOptions = ["missing", "new", "none", "sync"];
    this.name = new FormControl("", [Validators.required, Validators.minLength(3)]);
    this.url = new FormControl("", [Validators.required, Validators.pattern("https?://.*"), Validators.minLength(10)]);
    this.apiKey = new FormControl("", [Validators.required, Validators.minLength(32), Validators.maxLength(50)]);
    this.editConnectionForm = new FormGroup({
      name: this.name,
      arrType: new FormControl("radarr"),
      monitorType: new FormControl("new"),
      url: this.url,
      apiKey: this.apiKey,
      path_mappings: new FormArray([])
    });
    this.addConnResult = "";
  }
  ngOnInit() {
    this.route.params.subscribe((params) => {
      this.connectionId = params[RouteParamConnectionId];
      this.settingsService.getConnection(this.connectionId).subscribe((conn) => {
        this.editConnectionForm.patchValue({
          name: conn.name,
          arrType: conn.arr_type,
          monitorType: conn.monitor,
          url: conn.url,
          apiKey: conn.api_key
        });
        this.pathMappings.clear();
        conn.path_mappings.forEach((mapping) => {
          this.addPathMapping(mapping, false);
        });
      });
    });
  }
  setArrType(selectedArrType) {
    this.editConnectionForm.patchValue({ arrType: selectedArrType });
    this.editConnectionForm.markAsTouched();
    this.editConnectionForm.markAsDirty();
  }
  setMonitorType(selectedMonitorType) {
    this.editConnectionForm.patchValue({ monitorType: selectedMonitorType });
    this.editConnectionForm.markAsTouched();
    this.editConnectionForm.markAsDirty();
  }
  get pathMappings() {
    return this.editConnectionForm.get("path_mappings");
  }
  addPathMapping(path_mapping = null, markAsTouched = true) {
    if (!path_mapping) {
      path_mapping = { id: null, connection_id: null, path_from: "", path_to: "" };
    }
    const pathMappingGroup = new FormGroup({
      id: new FormControl(path_mapping.id),
      connection_id: new FormControl(path_mapping.connection_id),
      path_from: new FormControl(path_mapping.path_from, Validators.required),
      path_to: new FormControl(path_mapping.path_to, Validators.required)
    });
    this.pathMappings.push(pathMappingGroup);
    if (markAsTouched) {
      this.editConnectionForm.markAsTouched();
      this.editConnectionForm.markAsDirty();
    }
  }
  removePathMapping(index) {
    this.pathMappings.removeAt(index);
    this.editConnectionForm.markAsTouched();
    this.editConnectionForm.markAsDirty();
  }
  showCancelDialog() {
    this.cancelDialog.nativeElement.showModal();
  }
  closeCancelDialog() {
    this.cancelDialog.nativeElement.close();
  }
  onCancel() {
    if (this.editConnectionForm.dirty) {
      this.showCancelDialog();
    } else {
      this._location.back();
    }
  }
  onConfirmCancel() {
    this.showCancelDialog();
    this._location.back();
  }
  onSubmit() {
    if (this.editConnectionForm.invalid) {
      return;
    }
    const updatedConnection = {
      id: this.connectionId,
      name: this.editConnectionForm.value.name || "",
      arr_type: this.editConnectionForm.value.arrType || "",
      url: this.editConnectionForm.value.url || "",
      api_key: this.editConnectionForm.value.apiKey || "",
      monitor: this.editConnectionForm.value.monitorType || "",
      path_mappings: this.editConnectionForm.value.path_mappings || []
    };
    this.settingsService.updateConnection(updatedConnection).subscribe((result) => {
      this.addConnResult = result;
      if (result.toLowerCase().includes("success")) {
        setTimeout(() => {
          this._location.back();
        }, 2e3);
      }
    });
  }
  static {
    this.\u0275fac = function EditConnectionComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _EditConnectionComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _EditConnectionComponent, selectors: [["app-edit-connection"]], viewQuery: function EditConnectionComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuery(_c03, 5);
      }
      if (rf & 2) {
        let _t;
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.cancelDialog = _t.first);
      }
    }, decls: 65, vars: 9, consts: [["cancelDialog", ""], [1, "form-container"], [3, "formGroup"], [1, "input-group"], ["for", "name"], ["id", "name", "type", "text", "formControlName", "name", "placeholder", "Connection Name", "autocomplete", "off", "autocapitalize", "words", "tabindex", "1", "oninput", "this.value = this.value.charAt(0).toUpperCase() + this.value.slice(1)"], ["class", "invalid-text", 4, "ngIf"], [1, "d-row"], [1, "option-container"], ["id", "arrtype", 1, "options-bar"], ["class", "option", "tabindex", "2", 3, "selected", "click", "keydown.enter", "keydown.space", 4, "ngFor", "ngForOf"], ["id", "monitorType", 1, "options-bar"], ["class", "option", "tabindex", "3", 3, "selected", "click", "keydown.enter", "keydown.space", 4, "ngFor", "ngForOf"], ["for", "url"], ["id", "url", "type", "url", "formControlName", "url", "placeholder", "Server URL Ex: http://192.168.0.15:6969", "tabindex", "4", "autocomplete", "off"], ["for", "apiKey"], ["id", "apiKey", "type", "text", "formControlName", "apiKey", "placeholder", "APIKEY", "tabindex", "5", "autocomplete", "off"], ["formArrayName", "path_mappings"], ["class", "d-row", 3, "formGroupName", 4, "ngFor", "ngForOf"], ["id", "add-path-mapping", "tabindex", "10", 1, "animated-button", "tertiary", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z"], [1, "text"], ["id", "cancel", "tabindex", "6", 1, "animated-button", "secondary", 3, "click"], ["d", "m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z"], ["id", "submit", "type", "submit", "tabindex", "7", 1, "animated-button", "primary", 3, "click", "disabled"], ["d", "M840-680v480q0 33-23.5 56.5T760-120H200q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h480l160 160Zm-80 34L646-760H200v560h560v-446ZM480-240q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35ZM240-560h360v-160H240v160Zm-40-86v446-560 114Z"], [4, "ngIf"], [3, "click"], [1, "dialog-content", 3, "click"], ["tabindex", "2", 1, "secondary", 3, "click"], ["tabindex", "1", 1, "primary", 3, "click"], [1, "invalid-text"], ["tabindex", "2", 1, "option", 3, "click", "keydown.enter", "keydown.space"], ["tabindex", "3", 1, "option", 3, "click", "keydown.enter", "keydown.space"], [1, "d-row", 3, "formGroupName"], ["for", "path_from"], ["id", "path_from", "type", "text", "formControlName", "path_from", "placeholder", "Arr Internal Path", "tabindex", "6", "autocomplete", "off"], ["for", "path_to"], ["id", "path_to", "type", "text", "formControlName", "path_to", "placeholder", "Trailarr Internal Path", "tabindex", "6", "autocomplete", "off"], ["id", "remove", "name", "Remove Path Mapping", "tabindex", "6", 1, "icononly-button", "tertiary", 3, "click"]], template: function EditConnectionComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275elementStart(0, "div", 1)(1, "h2");
        \u0275\u0275text(2, "Edit Connection:");
        \u0275\u0275elementEnd();
        \u0275\u0275element(3, "hr");
        \u0275\u0275elementStart(4, "form", 2)(5, "div", 3)(6, "label", 4);
        \u0275\u0275text(7, "Connection Name");
        \u0275\u0275elementEnd();
        \u0275\u0275element(8, "input", 5);
        \u0275\u0275template(9, EditConnectionComponent_p_9_Template, 2, 0, "p", 6);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(10, "div", 7)(11, "div", 8)(12, "span");
        \u0275\u0275text(13, "Arr Type: ");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(14, "div", 9);
        \u0275\u0275template(15, EditConnectionComponent_div_15_Template, 3, 5, "div", 10);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(16, "div", 8)(17, "span");
        \u0275\u0275text(18, "Monitor Type: ");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(19, "div", 11);
        \u0275\u0275template(20, EditConnectionComponent_div_20_Template, 3, 5, "div", 12);
        \u0275\u0275elementEnd()()();
        \u0275\u0275elementStart(21, "div", 3)(22, "label", 13);
        \u0275\u0275text(23, "Server URL");
        \u0275\u0275elementEnd();
        \u0275\u0275element(24, "input", 14);
        \u0275\u0275template(25, EditConnectionComponent_p_25_Template, 2, 0, "p", 6);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(26, "div", 3)(27, "label", 15);
        \u0275\u0275text(28, "API Key");
        \u0275\u0275elementEnd();
        \u0275\u0275element(29, "input", 16);
        \u0275\u0275template(30, EditConnectionComponent_p_30_Template, 2, 0, "p", 6);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(31, "h3");
        \u0275\u0275text(32, "Path Mappings:");
        \u0275\u0275elementEnd();
        \u0275\u0275element(33, "hr");
        \u0275\u0275elementStart(34, "div", 17);
        \u0275\u0275template(35, EditConnectionComponent_div_35_Template, 12, 1, "div", 18);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(36, "div", 7)(37, "button", 19);
        \u0275\u0275listener("click", function EditConnectionComponent_Template_button_click_37_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.addPathMapping());
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(38, "svg", 20);
        \u0275\u0275element(39, "path", 21);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(40, "span", 22);
        \u0275\u0275text(41, "Add Path Mapping");
        \u0275\u0275elementEnd()()();
        \u0275\u0275elementStart(42, "div", 7)(43, "button", 23);
        \u0275\u0275listener("click", function EditConnectionComponent_Template_button_click_43_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onCancel());
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(44, "svg", 20);
        \u0275\u0275element(45, "path", 24);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(46, "span", 22);
        \u0275\u0275text(47, "Cancel");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(48, "button", 25);
        \u0275\u0275listener("click", function EditConnectionComponent_Template_button_click_48_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onSubmit());
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(49, "svg", 20);
        \u0275\u0275element(50, "path", 26);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(51, "span", 22);
        \u0275\u0275text(52, "submit");
        \u0275\u0275elementEnd()()();
        \u0275\u0275template(53, EditConnectionComponent_p_53_Template, 2, 1, "p", 27);
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(54, "dialog", 28, 0);
        \u0275\u0275listener("click", function EditConnectionComponent_Template_dialog_click_54_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeCancelDialog());
        });
        \u0275\u0275elementStart(56, "div", 29);
        \u0275\u0275listener("click", function EditConnectionComponent_Template_div_click_56_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(57, "h2");
        \u0275\u0275text(58, "Unsaved Changes");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(59, "p");
        \u0275\u0275text(60, "Canges will be lost. Are you sure you want to cancel?");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(61, "button", 30);
        \u0275\u0275listener("click", function EditConnectionComponent_Template_button_click_61_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onConfirmCancel());
        });
        \u0275\u0275text(62, "Yes");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(63, "button", 31);
        \u0275\u0275listener("click", function EditConnectionComponent_Template_button_click_63_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeCancelDialog());
        });
        \u0275\u0275text(64, "No");
        \u0275\u0275elementEnd()()();
      }
      if (rf & 2) {
        \u0275\u0275advance(4);
        \u0275\u0275property("formGroup", ctx.editConnectionForm);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngIf", ctx.name.invalid && ctx.name.touched);
        \u0275\u0275advance(6);
        \u0275\u0275property("ngForOf", ctx.arrOptions);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngForOf", ctx.monitorOptions);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngIf", ctx.url.invalid && ctx.url.touched);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngIf", ctx.apiKey.invalid && ctx.apiKey.touched);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngForOf", ctx.pathMappings.controls);
        \u0275\u0275advance(13);
        \u0275\u0275property("disabled", !ctx.editConnectionForm.valid || ctx.editConnectionForm.untouched);
        \u0275\u0275advance(5);
        \u0275\u0275property("ngIf", ctx.addConnResult);
      }
    }, dependencies: [ReactiveFormsModule, \u0275NgNoValidate, DefaultValueAccessor, NgControlStatus, NgControlStatusGroup, FormGroupDirective, FormControlName, FormGroupName, FormArrayName, NgForOf, NgIf, UpperCasePipe], styles: ["\n\n.form-container[_ngcontent-%COMP%] {\n  width: 100%;\n  border: 2px solid var(--color-outline);\n  padding: 24px;\n  display: flex;\n  flex-direction: column;\n  box-sizing: border-box;\n  position: relative;\n  border-radius: 16px;\n  background-color: var(--color-surface-container);\n  transition-property: opacity;\n  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);\n  transition-duration: 0.15s;\n}\n.form-container[_ngcontent-%COMP%]   form[_ngcontent-%COMP%] {\n  display: block;\n  padding: 0;\n  border: var(--color-outline);\n  border-radius: 8px;\n}\n.input-group[_ngcontent-%COMP%] {\n  flex-grow: 1;\n  display: flex;\n  flex-direction: column;\n  gap: 2px;\n  margin-bottom: 1rem;\n}\n.input-group[_ngcontent-%COMP%]   label[_ngcontent-%COMP%] {\n  margin-right: 10px;\n  display: block;\n  margin-bottom: 5px;\n}\n.input-group[_ngcontent-%COMP%]   input[_ngcontent-%COMP%] {\n  width: auto;\n  padding: 12px;\n  font-family: inherit;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  border: 2px solid var(--color-outline);\n  border-radius: 8px;\n}\ninput.ng-touched.ng-invalid[_ngcontent-%COMP%] {\n  border: 2px solid var(--color-error);\n  opacity: 0.6;\n  background-color: var(--color-error-container);\n  color: var(--color-on-error-container);\n  font-weight: 700;\n}\n.input-group[_ngcontent-%COMP%]   .invalid-text[_ngcontent-%COMP%] {\n  color: var(--color-error);\n}\n.d-row[_ngcontent-%COMP%] {\n  display: flex;\n  gap: 1rem;\n  flex-wrap: wrap;\n  margin-bottom: 1rem;\n  justify-content: space-around;\n  align-items: center;\n}\n.option-container[_ngcontent-%COMP%] {\n  display: flex;\n  align-items: center;\n  margin-bottom: 1rem 0 0 0;\n}\n.option-container[_ngcontent-%COMP%]   label[_ngcontent-%COMP%], \n.option-container[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n  padding: 10px;\n  padding-left: 0;\n  display: block;\n  margin-right: 10px;\n  background-color: var(--color-surface-container);\n}\n.option-container[_ngcontent-%COMP%]   .options-bar[_ngcontent-%COMP%] {\n  display: flex;\n  background-color: var(--color-surface-container-high);\n  border-radius: 10px;\n  border: 0.5px solid var(--color-outline);\n}\n.option-container[_ngcontent-%COMP%]   .option[_ngcontent-%COMP%] {\n  padding: 10px;\n  cursor: pointer;\n  border-radius: 10px;\n  transition: 0.3s ease;\n}\n.option-container[_ngcontent-%COMP%]   .selected[_ngcontent-%COMP%] {\n  background-color: var(--color-tertiary-container);\n  font-weight: 600;\n  color: var(--color-on-tertiary-container);\n}\n.dialog-content[_ngcontent-%COMP%] {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog[_ngcontent-%COMP%]::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content[_ngcontent-%COMP%]   button[_ngcontent-%COMP%] {\n  margin: 10px;\n}\n/*# sourceMappingURL=edit-connection.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(EditConnectionComponent, [{
    type: Component,
    args: [{ selector: "app-edit-connection", imports: [ReactiveFormsModule, NgForOf, NgIf, UpperCasePipe], template: '<div class="form-container">\n  <h2>Edit Connection:</h2>\n  <hr />\n  <form [formGroup]="editConnectionForm">\n    <div class="input-group">\n      <label for="name">Connection Name</label>\n      <input\n        id="name"\n        type="text"\n        formControlName="name"\n        placeholder="Connection Name"\n        autocomplete="off"\n        autocapitalize="words"\n        tabindex="1"\n        oninput="this.value = this.value.charAt(0).toUpperCase() + this.value.slice(1)"\n      />\n      <p *ngIf="name.invalid && name.touched" class="invalid-text">Server Name is required! Minimum 3 characters</p>\n    </div>\n    <div class="d-row">\n      <div class="option-container">\n        <span>Arr Type: </span>\n        <div id="arrtype" class="options-bar">\n          <div\n            *ngFor="let option of arrOptions"\n            class="option"\n            tabindex="2"\n            [class.selected]="option === editConnectionForm.value.arrType"\n            (click)="setArrType(option)"\n            (keydown.enter)="setArrType(option)"\n            (keydown.space)="setArrType(option)"\n          >\n            {{ option | uppercase }}\n          </div>\n        </div>\n      </div>\n      <div class="option-container">\n        <span>Monitor Type: </span>\n        <div id="monitorType" class="options-bar">\n          <div\n            *ngFor="let option of monitorOptions"\n            class="option"\n            tabindex="3"\n            [class.selected]="option === editConnectionForm.value.monitorType"\n            (click)="setMonitorType(option)"\n            (keydown.enter)="setMonitorType(option)"\n            (keydown.space)="setMonitorType(option)"\n          >\n            {{ option | uppercase }}\n          </div>\n        </div>\n      </div>\n    </div>\n    <div class="input-group">\n      <label for="url">Server URL</label>\n      <input\n        id="url"\n        type="url"\n        formControlName="url"\n        placeholder="Server URL Ex: http://192.168.0.15:6969"\n        tabindex="4"\n        autocomplete="off"\n      />\n      <p *ngIf="url.invalid && url.touched" class="invalid-text">Server URL is invalid!</p>\n    </div>\n    <div class="input-group">\n      <label for="apiKey">API Key</label>\n      <input id="apiKey" type="text" formControlName="apiKey" placeholder="APIKEY" tabindex="5" autocomplete="off" />\n      <p *ngIf="apiKey.invalid && apiKey.touched" class="invalid-text">APIKey is invalid!</p>\n    </div>\n    <h3>Path Mappings:</h3>\n    <hr />\n    <div formArrayName="path_mappings">\n      <div *ngFor="let path_mapping of pathMappings.controls; let i = index" [formGroupName]="i" class="d-row">\n        <div class="input-group">\n          <label for="path_from">Path From</label>\n          <input id="path_from" type="text" formControlName="path_from" placeholder="Arr Internal Path" tabindex="6" autocomplete="off" />\n        </div>\n        <div class="input-group">\n          <label for="path_to">Path To</label>\n          <input id="path_to" type="text" formControlName="path_to" placeholder="Trailarr Internal Path" tabindex="6" autocomplete="off" />\n        </div>\n        <button class="icononly-button tertiary" id="remove" name="Remove Path Mapping" tabindex="6" (click)="removePathMapping(i)">\n          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n            <path d="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z" />\n          </svg>\n          <!-- <span class="text">Remove</span> -->\n        </button>\n      </div>\n    </div>\n    <div class="d-row">\n      <button class="animated-button tertiary" id="add-path-mapping" tabindex="10" (click)="addPathMapping()">\n        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n          <path d="M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z" />\n        </svg>\n        <span class="text">Add Path Mapping</span>\n      </button>\n    </div>\n    <div class="d-row">\n      <button class="animated-button secondary" id="cancel" tabindex="6" (click)="onCancel()">\n        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n          <path d="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z" />\n        </svg>\n        <span class="text">Cancel</span>\n      </button>\n      <button\n        class="animated-button primary"\n        id="submit"\n        type="submit"\n        tabindex="7"\n        [disabled]="!editConnectionForm.valid || editConnectionForm.untouched"\n        (click)="onSubmit()"\n      >\n        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n          <path\n            d="M840-680v480q0 33-23.5 56.5T760-120H200q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h480l160 160Zm-80 34L646-760H200v560h560v-446ZM480-240q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35ZM240-560h360v-160H240v160Zm-40-86v446-560 114Z"\n          />\n        </svg>\n        <span class="text">submit</span>\n      </button>\n    </div>\n    <p *ngIf="addConnResult">{{ addConnResult }}</p>\n  </form>\n</div>\n<dialog #cancelDialog (click)="closeCancelDialog()">\n  <div class="dialog-content" (click)="$event.stopPropagation()">\n    <h2>Unsaved Changes</h2>\n    <p>Canges will be lost. Are you sure you want to cancel?</p>\n    <button class="secondary" (click)="onConfirmCancel()" tabindex="2">Yes</button>\n    <button class="primary" (click)="closeCancelDialog()" tabindex="1">No</button>\n  </div>\n</dialog>\n', styles: ["/* src/app/settings/connections/edit-connection/edit-connection.component.scss */\n.form-container {\n  width: 100%;\n  border: 2px solid var(--color-outline);\n  padding: 24px;\n  display: flex;\n  flex-direction: column;\n  box-sizing: border-box;\n  position: relative;\n  border-radius: 16px;\n  background-color: var(--color-surface-container);\n  transition-property: opacity;\n  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);\n  transition-duration: 0.15s;\n}\n.form-container form {\n  display: block;\n  padding: 0;\n  border: var(--color-outline);\n  border-radius: 8px;\n}\n.input-group {\n  flex-grow: 1;\n  display: flex;\n  flex-direction: column;\n  gap: 2px;\n  margin-bottom: 1rem;\n}\n.input-group label {\n  margin-right: 10px;\n  display: block;\n  margin-bottom: 5px;\n}\n.input-group input {\n  width: auto;\n  padding: 12px;\n  font-family: inherit;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  border: 2px solid var(--color-outline);\n  border-radius: 8px;\n}\ninput.ng-touched.ng-invalid {\n  border: 2px solid var(--color-error);\n  opacity: 0.6;\n  background-color: var(--color-error-container);\n  color: var(--color-on-error-container);\n  font-weight: 700;\n}\n.input-group .invalid-text {\n  color: var(--color-error);\n}\n.d-row {\n  display: flex;\n  gap: 1rem;\n  flex-wrap: wrap;\n  margin-bottom: 1rem;\n  justify-content: space-around;\n  align-items: center;\n}\n.option-container {\n  display: flex;\n  align-items: center;\n  margin-bottom: 1rem 0 0 0;\n}\n.option-container label,\n.option-container span {\n  padding: 10px;\n  padding-left: 0;\n  display: block;\n  margin-right: 10px;\n  background-color: var(--color-surface-container);\n}\n.option-container .options-bar {\n  display: flex;\n  background-color: var(--color-surface-container-high);\n  border-radius: 10px;\n  border: 0.5px solid var(--color-outline);\n}\n.option-container .option {\n  padding: 10px;\n  cursor: pointer;\n  border-radius: 10px;\n  transition: 0.3s ease;\n}\n.option-container .selected {\n  background-color: var(--color-tertiary-container);\n  font-weight: 600;\n  color: var(--color-on-tertiary-container);\n}\n.dialog-content {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content button {\n  margin: 10px;\n}\n/*# sourceMappingURL=edit-connection.component.css.map */\n"] }]
  }], null, { cancelDialog: [{
    type: ViewChild,
    args: ["cancelDialog"]
  }] });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(EditConnectionComponent, { className: "EditConnectionComponent", filePath: "src/app/settings/connections/edit-connection/edit-connection.component.ts", lineNumber: 15 });
})();

// src/app/settings/connections/show-connections/show-connections.component.ts
var _c04 = ["deleteConnectionDialog"];
var _c1 = (a0, a1) => [a0, a1];
var _c2 = (a0, a1, a2) => ["/", a0, a1, a2];
function ShowConnectionsComponent_Conditional_16_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 6);
  }
}
function ShowConnectionsComponent_Conditional_17_Conditional_3_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p");
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext(2);
    \u0275\u0275classMapInterpolate1("result-", ctx_r1.resultType, "");
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(ctx_r1.resultMessage);
  }
}
function ShowConnectionsComponent_Conditional_17_Conditional_4_For_2_Case_13_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "img", 17);
  }
}
function ShowConnectionsComponent_Conditional_17_Conditional_4_For_2_Case_14_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "img", 18);
  }
}
function ShowConnectionsComponent_Conditional_17_Conditional_4_For_2_Template(rf, ctx) {
  if (rf & 1) {
    const _r3 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 13)(1, "h3", 14);
    \u0275\u0275text(2);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "div", 15)(4, "p");
    \u0275\u0275text(5);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(6, "p");
    \u0275\u0275text(7);
    \u0275\u0275pipe(8, "uppercase");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(9, "p");
    \u0275\u0275text(10);
    \u0275\u0275pipe(11, "date");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(12, "a", 16);
    \u0275\u0275template(13, ShowConnectionsComponent_Conditional_17_Conditional_4_For_2_Case_13_Template, 1, 0, "img", 17)(14, ShowConnectionsComponent_Conditional_17_Conditional_4_For_2_Case_14_Template, 1, 0, "img", 18);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(15, "div", 19)(16, "button", 20);
    \u0275\u0275listener("click", function ShowConnectionsComponent_Conditional_17_Conditional_4_For_2_Template_button_click_16_listener() {
      const connection_r4 = \u0275\u0275restoreView(_r3).$implicit;
      const ctx_r1 = \u0275\u0275nextContext(3);
      ctx_r1.selectedId = connection_r4.id;
      return \u0275\u0275resetView(ctx_r1.showDeleteDialog());
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(17, "svg", 8);
    \u0275\u0275element(18, "path", 21);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(19, "span", 10);
    \u0275\u0275text(20, "Delete");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(21, "button", 22);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(22, "svg", 8);
    \u0275\u0275element(23, "path", 23);
    \u0275\u0275elementEnd();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(24, "span", 10);
    \u0275\u0275text(25, "Edit");
    \u0275\u0275elementEnd()()()();
  }
  if (rf & 2) {
    let tmp_19_0;
    const connection_r4 = ctx.$implicit;
    const ctx_r1 = \u0275\u0275nextContext(3);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(connection_r4.name);
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate1("Address: ", connection_r4.url, "");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1("Monitor: ", \u0275\u0275pipeBind1(8, 7, connection_r4.monitor), "");
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate1("Added: ", \u0275\u0275pipeBind1(11, 9, connection_r4.added_at), "");
    \u0275\u0275advance(2);
    \u0275\u0275propertyInterpolate("href", connection_r4.url, \u0275\u0275sanitizeUrl);
    \u0275\u0275advance();
    \u0275\u0275conditional((tmp_19_0 = connection_r4.arr_type) === "radarr" ? 13 : tmp_19_0 === "sonarr" ? 14 : -1);
    \u0275\u0275advance(8);
    \u0275\u0275property("routerLink", \u0275\u0275pureFunction2(11, _c1, ctx_r1.RouteEdit, connection_r4.id));
  }
}
function ShowConnectionsComponent_Conditional_17_Conditional_4_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 12);
    \u0275\u0275repeaterCreate(1, ShowConnectionsComponent_Conditional_17_Conditional_4_For_2_Template, 26, 14, "div", 13, \u0275\u0275repeaterTrackByIndex);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    \u0275\u0275nextContext(2);
    const connections_r5 = \u0275\u0275readContextLet(0);
    \u0275\u0275advance();
    \u0275\u0275repeater(connections_r5);
  }
}
function ShowConnectionsComponent_Conditional_17_Conditional_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 6)(1, "div", 24);
    \u0275\u0275text(2, "Add New!");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "p", 25);
    \u0275\u0275text(4, `I'm all alone here!. Click the "ADD" button to add some Radarr/Sonarr instances to let the magic happen!`);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext(2);
    \u0275\u0275advance();
    \u0275\u0275property("routerLink", \u0275\u0275pureFunction3(1, _c2, ctx_r1.RouteSettings, ctx_r1.RouteConnections, ctx_r1.RouteAdd));
  }
}
function ShowConnectionsComponent_Conditional_17_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "h2");
    \u0275\u0275text(1, "Connections");
    \u0275\u0275elementEnd();
    \u0275\u0275element(2, "hr");
    \u0275\u0275template(3, ShowConnectionsComponent_Conditional_17_Conditional_3_Template, 2, 4, "p", 11)(4, ShowConnectionsComponent_Conditional_17_Conditional_4_Template, 3, 0, "div", 12)(5, ShowConnectionsComponent_Conditional_17_Conditional_5_Template, 5, 5, "div", 6);
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext();
    const connections_r5 = \u0275\u0275readContextLet(0);
    \u0275\u0275advance(3);
    \u0275\u0275conditional(ctx_r1.resultMessage ? 3 : -1);
    \u0275\u0275advance();
    \u0275\u0275conditional(connections_r5 && connections_r5.length > 0 ? 4 : 5);
  }
}
var ShowConnectionsComponent = class _ShowConnectionsComponent {
  constructor() {
    this.connectionsService = inject(ConnectionsService);
    this.isLoading = signal(true);
    this.triggerReload$ = new Subject();
    this.resultMessage = "";
    this.resultType = "";
    this.selectedId = 0;
    this.RouteAdd = RouteAdd;
    this.RouteConnections = RouteConnections;
    this.RouteEdit = RouteEdit;
    this.RouteSettings = RouteSettings;
    this.dialog = viewChild("deleteConnectionDialog");
    this.connections$ = this.triggerReload$.pipe(startWith("meh"), tap(() => this.isLoading.set(true)), switchMap(() => this.connectionsService.getConnectionsApiV1ConnectionsGet().pipe(catchError((err) => {
      console.log("Failed to load connections.", err);
      return of([]);
    }))), tap(() => this.isLoading.set(false)), distinctUntilChanged(jsonEqual), shareReplay({ refCount: true, bufferSize: 1 }));
    this.closeDeleteDialog = () => this.dialog()?.nativeElement.close();
    this.showDeleteDialog = () => this.dialog()?.nativeElement.showModal();
  }
  ngOnDestroy() {
    this.triggerReload$.complete();
  }
  onConfirmDelete() {
    this.closeDeleteDialog();
    this.connectionsService.deleteConnectionApiV1ConnectionsConnectionIdDelete({ connection_id: this.selectedId }).pipe(catchError((error) => {
      let errorMessage = "";
      if (error.error instanceof ErrorEvent) {
        errorMessage = `Error: ${error.error.message}`;
      } else {
        errorMessage = `Error: ${error.status} ${error.error.detail}`;
      }
      return of(errorMessage);
    })).subscribe((res) => {
      this.resultType = "error";
      if (res.toLowerCase().includes("success")) {
        this.resultType = "success";
      }
      this.resultMessage = res;
      this.triggerReload$.next();
      setTimeout(() => {
        this.resultMessage = "";
      }, 3e3);
    });
  }
  static {
    this.\u0275fac = function ShowConnectionsComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _ShowConnectionsComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _ShowConnectionsComponent, selectors: [["app-show-connections"]], viewQuery: function ShowConnectionsComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuerySignal(ctx.dialog, _c04, 5);
      }
      if (rf & 2) {
        \u0275\u0275queryAdvance();
      }
    }, decls: 23, vars: 5, consts: [["deleteConnectionDialog", ""], [3, "click"], [1, "dialog-content", 3, "click"], ["tabindex", "2", 1, "danger", 3, "click"], ["tabindex", "1", 1, "secondary", 3, "click"], [1, "sett-conn-container"], [1, "center"], [1, "animated-button", "top-right-button", 3, "routerLink"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z"], [1, "text"], [3, "class"], [1, "connection-container"], [1, "connection-card"], [1, "title"], [1, "content"], ["target", "_blank", 1, "link-image", 3, "href"], ["src", "assets/radarr_128.png"], ["src", "assets/sonarr_128.png"], [1, "buttons"], [1, "animated-button", "secondary", 3, "click"], ["d", "M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"], [1, "animated-button", "primary", 3, "routerLink"], ["d", "M200-200h57l391-391-57-57-391 391v57Zm-80 80v-170l528-527q12-11 26.5-17t30.5-6q16 0 31 6t26 18l55 56q12 11 17.5 26t5.5 30q0 16-5.5 30.5T817-647L290-120H120Zm640-584-56-56 56 56Zm-141 85-28-29 57 57-29-28Z"], [1, "all-empty-card", "center", 3, "routerLink"], [1, "text-primary"]], template: function ShowConnectionsComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275declareLet(0);
        \u0275\u0275pipe(1, "async");
        \u0275\u0275elementStart(2, "dialog", 1, 0);
        \u0275\u0275listener("click", function ShowConnectionsComponent_Template_dialog_click_2_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeDeleteDialog());
        });
        \u0275\u0275elementStart(4, "div", 2);
        \u0275\u0275listener("click", function ShowConnectionsComponent_Template_div_click_4_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(5, "h2");
        \u0275\u0275text(6, "Delete Connection");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(7, "p");
        \u0275\u0275text(8, "This will Delete the connection and no longer monitor its Media");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(9, "p");
        \u0275\u0275text(10, "Delete the connection?");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(11, "button", 3);
        \u0275\u0275listener("click", function ShowConnectionsComponent_Template_button_click_11_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onConfirmDelete());
        });
        \u0275\u0275text(12, "Delete");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(13, "button", 4);
        \u0275\u0275listener("click", function ShowConnectionsComponent_Template_button_click_13_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeDeleteDialog());
        });
        \u0275\u0275text(14, "Cancel");
        \u0275\u0275elementEnd()()();
        \u0275\u0275elementStart(15, "div", 5);
        \u0275\u0275template(16, ShowConnectionsComponent_Conditional_16_Template, 1, 0, "app-load-indicator", 6)(17, ShowConnectionsComponent_Conditional_17_Template, 6, 2);
        \u0275\u0275elementStart(18, "button", 7);
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(19, "svg", 8);
        \u0275\u0275element(20, "path", 9);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(21, "span", 10);
        \u0275\u0275text(22, "Add New");
        \u0275\u0275elementEnd()()();
      }
      if (rf & 2) {
        \u0275\u0275storeLet(\u0275\u0275pipeBind1(1, 2, ctx.connections$));
        \u0275\u0275advance(16);
        \u0275\u0275conditional(ctx.isLoading() ? 16 : 17);
        \u0275\u0275advance(2);
        \u0275\u0275property("routerLink", ctx.RouteAdd);
      }
    }, dependencies: [CommonModule, AsyncPipe, UpperCasePipe, DatePipe, LoadIndicatorComponent, RouterLink], styles: ["\n\n.sett-conn-container[_ngcontent-%COMP%] {\n  height: 100%;\n  width: 100%;\n  display: flex;\n  flex-direction: column;\n  position: relative;\n  gap: 12px;\n}\n.top-right-button[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 0;\n  right: 0;\n  margin: 10px;\n}\n.center[_ngcontent-%COMP%] {\n  margin: auto;\n}\n.result-success[_ngcontent-%COMP%] {\n  padding: 10px;\n  display: block;\n  border-radius: 4px;\n  color: var(--color-success-text);\n  background-color: var(--color-success);\n}\n.result-error[_ngcontent-%COMP%] {\n  padding: 10px;\n  display: block;\n  border-radius: 4px;\n  color: var(--color-error-text);\n  background-color: var(--color-error);\n}\n.connection-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  flex-wrap: wrap;\n  gap: 1rem;\n}\n.connection-card[_ngcontent-%COMP%] {\n  display: grid;\n  grid-template-rows: auto 1fr auto;\n  grid-template-columns: 1fr auto;\n  gap: 10px;\n  max-width: 500px;\n  padding: 12px;\n  border: 2px solid var(--color-outline);\n  border-radius: 8px;\n  background-color: var(--color-surface-container);\n  color: var(--color-on-surface);\n}\n.connection-card[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%] {\n  grid-row: 1;\n  grid-column: 1/span 2;\n  color: var(--color-primary);\n  text-align: center;\n}\n.connection-card[_ngcontent-%COMP%]   .content[_ngcontent-%COMP%] {\n  grid-row: 2;\n  grid-column: 1;\n}\n.connection-card[_ngcontent-%COMP%]   .link-image[_ngcontent-%COMP%] {\n  grid-row: 2;\n  grid-column: 2;\n  width: auto;\n}\n.connection-card[_ngcontent-%COMP%]   .buttons[_ngcontent-%COMP%] {\n  grid-row: 3;\n  grid-column: 1/span 2;\n  display: flex;\n  justify-content: space-between;\n}\n.dialog-content[_ngcontent-%COMP%] {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog[_ngcontent-%COMP%]::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content[_ngcontent-%COMP%]   button[_ngcontent-%COMP%] {\n  margin: 10px;\n}\n/*# sourceMappingURL=show-connections.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ShowConnectionsComponent, [{
    type: Component,
    args: [{ selector: "app-show-connections", imports: [CommonModule, LoadIndicatorComponent, RouterLink], template: `@let connections = connections$ | async;

<dialog #deleteConnectionDialog (click)="closeDeleteDialog()">
  <div class="dialog-content" (click)="$event.stopPropagation()">
    <h2>Delete Connection</h2>
    <p>This will Delete the connection and no longer monitor its Media</p>
    <p>Delete the connection?</p>
    <button class="danger" (click)="onConfirmDelete()" tabindex="2">Delete</button>
    <button class="secondary" (click)="closeDeleteDialog()" tabindex="1">Cancel</button>
  </div>
</dialog>

<div class="sett-conn-container">
  @if (isLoading()) {
    <app-load-indicator class="center" />
  } @else {
    <h2>Connections</h2>
    <hr />

    @if (resultMessage) {
      <p class="result-{{ resultType }}">{{ resultMessage }}</p>
    }

    @if (connections && connections.length > 0) {
      <div class="connection-container">
        @for (connection of connections; track $index) {
          <div class="connection-card">
            <h3 class="title">{{ connection.name }}</h3>
            <div class="content">
              <p>Address: {{ connection.url }}</p>
              <p>Monitor: {{ connection.monitor | uppercase }}</p>
              <p>Added: {{ connection.added_at | date }}</p>
            </div>
            <a class="link-image" target="_blank" href="{{ connection.url }}">
              @switch (connection.arr_type) {
                @case ('radarr') {
                  <img src="assets/radarr_128.png" />
                }
                @case ('sonarr') {
                  <img src="assets/sonarr_128.png" />
                }
              }
            </a>
            <div class="buttons">
              <button class="animated-button secondary" (click)="selectedId = connection.id; showDeleteDialog()">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
                  <path
                    d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"
                  />
                </svg>
                <span class="text">Delete</span>
              </button>
              <button class="animated-button primary" [routerLink]="[RouteEdit, connection.id]">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
                  <path
                    d="M200-200h57l391-391-57-57-391 391v57Zm-80 80v-170l528-527q12-11 26.5-17t30.5-6q16 0 31 6t26 18l55 56q12 11 17.5 26t5.5 30q0 16-5.5 30.5T817-647L290-120H120Zm640-584-56-56 56 56Zm-141 85-28-29 57 57-29-28Z"
                  />
                </svg>
                <span class="text">Edit</span>
              </button>
            </div>
          </div>
        }
      </div>
    } @else {
      <div class="center">
        <div class="all-empty-card center" [routerLink]="['/', RouteSettings, RouteConnections, RouteAdd]">Add New!</div>
        <p class="text-primary">I'm all alone here!. Click the "ADD" button to add some Radarr/Sonarr instances to let the magic happen!</p>
      </div>
    }
  }
  <button class="animated-button top-right-button" [routerLink]="RouteAdd">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
      <path d="M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z" />
    </svg>
    <span class="text">Add New</span>
  </button>
</div>
`, styles: ["/* src/app/settings/connections/show-connections/show-connections.component.scss */\n.sett-conn-container {\n  height: 100%;\n  width: 100%;\n  display: flex;\n  flex-direction: column;\n  position: relative;\n  gap: 12px;\n}\n.top-right-button {\n  position: absolute;\n  top: 0;\n  right: 0;\n  margin: 10px;\n}\n.center {\n  margin: auto;\n}\n.result-success {\n  padding: 10px;\n  display: block;\n  border-radius: 4px;\n  color: var(--color-success-text);\n  background-color: var(--color-success);\n}\n.result-error {\n  padding: 10px;\n  display: block;\n  border-radius: 4px;\n  color: var(--color-error-text);\n  background-color: var(--color-error);\n}\n.connection-container {\n  display: flex;\n  flex-direction: row;\n  flex-wrap: wrap;\n  gap: 1rem;\n}\n.connection-card {\n  display: grid;\n  grid-template-rows: auto 1fr auto;\n  grid-template-columns: 1fr auto;\n  gap: 10px;\n  max-width: 500px;\n  padding: 12px;\n  border: 2px solid var(--color-outline);\n  border-radius: 8px;\n  background-color: var(--color-surface-container);\n  color: var(--color-on-surface);\n}\n.connection-card .title {\n  grid-row: 1;\n  grid-column: 1/span 2;\n  color: var(--color-primary);\n  text-align: center;\n}\n.connection-card .content {\n  grid-row: 2;\n  grid-column: 1;\n}\n.connection-card .link-image {\n  grid-row: 2;\n  grid-column: 2;\n  width: auto;\n}\n.connection-card .buttons {\n  grid-row: 3;\n  grid-column: 1/span 2;\n  display: flex;\n  justify-content: space-between;\n}\n.dialog-content {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content button {\n  margin: 10px;\n}\n/*# sourceMappingURL=show-connections.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(ShowConnectionsComponent, { className: "ShowConnectionsComponent", filePath: "src/app/settings/connections/show-connections/show-connections.component.ts", lineNumber: 16 });
})();

// src/app/settings/profiles/settings/options-setting/options-setting.component.ts
function OptionsSettingComponent_Conditional_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "small");
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = \u0275\u0275nextContext();
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(ctx_r0.descriptionExtra());
  }
}
function OptionsSettingComponent_For_8_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "label", 3)(1, "input", 4);
    \u0275\u0275listener("change", function OptionsSettingComponent_For_8_Template_input_change_1_listener() {
      const option_r3 = \u0275\u0275restoreView(_r2).$implicit;
      const ctx_r0 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r0.onOptionClick(option_r3));
    });
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(2, "span", 5);
    \u0275\u0275text(3);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const option_r3 = ctx.$implicit;
    const ctx_r0 = \u0275\u0275nextContext();
    \u0275\u0275classProp("option__selected", option_r3 === ctx_r0.selectedOption());
    \u0275\u0275advance();
    \u0275\u0275property("id", ctx_r0.inputId + "_" + option_r3)("name", ctx_r0.inputId)("value", option_r3)("checked", option_r3 === ctx_r0.selectedOption());
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(option_r3);
  }
}
var OptionsSettingComponent = class _OptionsSettingComponent {
  constructor() {
    this.inputId = "options-setting-" + Math.random().toString(36).substring(2, 10);
    this.name = input.required();
    this.description = input("");
    this.descriptionExtra = input("");
    this.options = input.required();
    this.selectedOption = input("", { transform: String });
    this.optionChange = output();
  }
  onOptionClick(option) {
    this.optionChange.emit(option);
  }
  static {
    this.\u0275fac = function OptionsSettingComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _OptionsSettingComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _OptionsSettingComponent, selectors: [["app-options-setting"]], inputs: { name: [1, "name"], description: [1, "description"], descriptionExtra: [1, "descriptionExtra"], options: [1, "options"], selectedOption: [1, "selectedOption"] }, outputs: { optionChange: "optionChange" }, decls: 9, vars: 5, consts: [[1, "content-label", 3, "id"], ["role", "radiogroup", 1, "options-bar"], [1, "option-label", 3, "option__selected"], [1, "option-label"], ["type", "radio", 3, "change", "id", "name", "value", "checked"], [1, "option-name"]], template: function OptionsSettingComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "div", 0)(1, "span");
        \u0275\u0275text(2);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(3, "small");
        \u0275\u0275text(4);
        \u0275\u0275elementEnd();
        \u0275\u0275template(5, OptionsSettingComponent_Conditional_5_Template, 2, 1, "small");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(6, "div", 1);
        \u0275\u0275repeaterCreate(7, OptionsSettingComponent_For_8_Template, 4, 7, "label", 2, \u0275\u0275repeaterTrackByIdentity);
        \u0275\u0275elementEnd();
      }
      if (rf & 2) {
        \u0275\u0275property("id", ctx.inputId + "_label");
        \u0275\u0275advance(2);
        \u0275\u0275textInterpolate(ctx.name());
        \u0275\u0275advance(2);
        \u0275\u0275textInterpolate(ctx.description());
        \u0275\u0275advance();
        \u0275\u0275conditional(ctx.descriptionExtra() ? 5 : -1);
        \u0275\u0275advance();
        \u0275\u0275attribute("aria-labelledby", ctx.inputId + "_label");
        \u0275\u0275advance();
        \u0275\u0275repeater(ctx.options());
      }
    }, styles: ["\n\n[_nghost-%COMP%] {\n  display: grid;\n  grid-template-columns: 3fr 2fr;\n  justify-items: start;\n  align-items: center;\n  margin: 1.5rem 0.5rem;\n  gap: 1rem;\n}\n@container (width < 40rem) {\n  [_nghost-%COMP%] {\n    grid-template-columns: 1fr;\n  }\n}\n.content-label[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  text-align: left;\n  gap: 0.5rem;\n  width: 100%;\n}\nlabel[_ngcontent-%COMP%], \nspan[_ngcontent-%COMP%] {\n  font-weight: bold;\n  text-wrap: nowrap;\n}\nsvg[_ngcontent-%COMP%] {\n  width: 1.5rem;\n  height: 1.5rem;\n  cursor: pointer;\n}\n.options-bar[_ngcontent-%COMP%] {\n  padding: 0.25rem;\n  display: flex;\n  background-color: var(--color-surface-container-high);\n  border-radius: 10px;\n  border: 0.5px solid var(--color-outline);\n}\n.option-label[_ngcontent-%COMP%] {\n  padding: 10px;\n  cursor: pointer;\n  border-radius: 10px;\n  transition: 0.3s ease;\n  flex: 1 1 auto;\n  text-align: center;\n}\n.option-label[_ngcontent-%COMP%]:has(input:focus-visible) {\n  outline: -webkit-focus-ring-color auto 1px;\n}\n.option-name[_ngcontent-%COMP%] {\n  border-radius: 10px;\n  border: none;\n  transition: all 0.15s ease-in-out;\n}\n.option__selected[_ngcontent-%COMP%] {\n  background-color: var(--color-tertiary-container);\n  font-weight: 600;\n  color: var(--color-on-tertiary-container);\n  transition: 0.3s ease;\n}\ninput[_ngcontent-%COMP%] {\n  clip: rect(0 0 0 0);\n  clip-path: inset(100%);\n  width: 1px;\n  height: 1px;\n  overflow: hidden;\n  position: absolute;\n  white-space: nowrap;\n}\n/*# sourceMappingURL=options-setting.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(OptionsSettingComponent, [{
    type: Component,
    args: [{ selector: "app-options-setting", imports: [], template: `<div class="content-label" [id]="inputId + '_label'">
  <span>{{ name() }}</span>
  <small>{{ description() }}</small>
  @if (descriptionExtra()) {
    <small>{{ descriptionExtra() }}</small>
  }
</div>
<div class="options-bar" role="radiogroup" [attr.aria-labelledby]="inputId + '_label'">
  @for (option of options(); track option) {
    <label class="option-label" [class.option__selected]="option === selectedOption()">
      <input
        type="radio"
        [id]="inputId + '_' + option"
        [name]="inputId"
        [value]="option"
        [checked]="option === selectedOption()"
        (change)="onOptionClick(option)"
      />
      <span class="option-name">{{ option }}</span>
    </label>
  }
</div>
`, styles: ["/* src/app/settings/profiles/settings/options-setting/options-setting.component.scss */\n:host {\n  display: grid;\n  grid-template-columns: 3fr 2fr;\n  justify-items: start;\n  align-items: center;\n  margin: 1.5rem 0.5rem;\n  gap: 1rem;\n}\n@container (width < 40rem) {\n  :host {\n    grid-template-columns: 1fr;\n  }\n}\n.content-label {\n  display: flex;\n  flex-direction: column;\n  text-align: left;\n  gap: 0.5rem;\n  width: 100%;\n}\nlabel,\nspan {\n  font-weight: bold;\n  text-wrap: nowrap;\n}\nsvg {\n  width: 1.5rem;\n  height: 1.5rem;\n  cursor: pointer;\n}\n.options-bar {\n  padding: 0.25rem;\n  display: flex;\n  background-color: var(--color-surface-container-high);\n  border-radius: 10px;\n  border: 0.5px solid var(--color-outline);\n}\n.option-label {\n  padding: 10px;\n  cursor: pointer;\n  border-radius: 10px;\n  transition: 0.3s ease;\n  flex: 1 1 auto;\n  text-align: center;\n}\n.option-label:has(input:focus-visible) {\n  outline: -webkit-focus-ring-color auto 1px;\n}\n.option-name {\n  border-radius: 10px;\n  border: none;\n  transition: all 0.15s ease-in-out;\n}\n.option__selected {\n  background-color: var(--color-tertiary-container);\n  font-weight: 600;\n  color: var(--color-on-tertiary-container);\n  transition: 0.3s ease;\n}\ninput {\n  clip: rect(0 0 0 0);\n  clip-path: inset(100%);\n  width: 1px;\n  height: 1px;\n  overflow: hidden;\n  position: absolute;\n  white-space: nowrap;\n}\n/*# sourceMappingURL=options-setting.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(OptionsSettingComponent, { className: "OptionsSettingComponent", filePath: "src/app/settings/profiles/settings/options-setting/options-setting.component.ts", lineNumber: 9 });
})();

// src/app/settings/profiles/settings/range-setting/range-setting.component.ts
function RangeSettingComponent_Conditional_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "small");
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = \u0275\u0275nextContext();
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(ctx_r0.descriptionExtra());
  }
}
function RangeSettingComponent_Conditional_10_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "button", 5);
    \u0275\u0275listener("click", function RangeSettingComponent_Conditional_10_Template_button_click_0_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r0 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r0.resetValue());
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 6);
    \u0275\u0275element(2, "path", 7);
    \u0275\u0275elementEnd()();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(3, "button", 8);
    \u0275\u0275listener("click", function RangeSettingComponent_Conditional_10_Template_button_click_3_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r0 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r0.onSubmitValue());
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(4, "svg", 6);
    \u0275\u0275element(5, "path", 9);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const ctx_r0 = \u0275\u0275nextContext();
    \u0275\u0275property("id", ctx_r0.inputId + "reset")("title", "Reset " + ctx_r0.name());
    \u0275\u0275advance(3);
    \u0275\u0275property("id", ctx_r0.inputId + "update")("title", "Update " + ctx_r0.name());
  }
}
var RangeSettingComponent = class _RangeSettingComponent {
  constructor() {
    this.inputId = "range-setting-" + Math.random().toString(36).substring(2, 10);
    this.name = input.required();
    this.description = input("");
    this.descriptionExtra = input("");
    this.value = model.required();
    this.minValue = input(0);
    this.maxValue = input(150);
    this.stepValue = input(5);
    this.disabled = input(false);
    this.oldValue = signal("");
    this.onSubmit = output();
  }
  ngOnInit() {
    this.oldValue.set(this.value());
  }
  resetValue() {
    this.value.set(this.oldValue());
  }
  onSubmitValue() {
    let submitValue = this.value();
    submitValue = submitValue.toString().trim();
    this.onSubmit.emit(submitValue);
    this.oldValue.set(submitValue);
  }
  static {
    this.\u0275fac = function RangeSettingComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _RangeSettingComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _RangeSettingComponent, selectors: [["app-range-setting"]], inputs: { name: [1, "name"], description: [1, "description"], descriptionExtra: [1, "descriptionExtra"], value: [1, "value"], minValue: [1, "minValue"], maxValue: [1, "maxValue"], stepValue: [1, "stepValue"], disabled: [1, "disabled"] }, outputs: { value: "valueChange", onSubmit: "onSubmit" }, decls: 11, vars: 14, consts: [[1, "content-label"], [3, "for"], [1, "content-input"], ["type", "range", 3, "ngModelChange", "id", "disabled", "ngModel", "min", "max", "step"], [1, "content-input__value"], [1, "secondary", "icononly-button", 3, "click", "id", "title"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M263-179.67v-84h317.67q65 0 110.83-45.5t45.83-110.5q0-64.33-45.83-110.16-45.83-45.84-110.83-45.84H297.33l104 104-58.66 57.34-204-203 204-204 58.66 57.66-104 104H580q99.67 0 170.5 70.17t70.83 169.83q0 100.34-70.83 170.17-70.83 69.83-170.5 69.83H263Z"], [1, "primary", "icononly-button", 3, "click", "id", "title"], ["d", "M378-235 142-471l52-52 184 184 388-388 52 52-440 440Z"]], template: function RangeSettingComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "div", 0)(1, "label", 1);
        \u0275\u0275text(2);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(3, "small");
        \u0275\u0275text(4);
        \u0275\u0275elementEnd();
        \u0275\u0275template(5, RangeSettingComponent_Conditional_5_Template, 2, 1, "small");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(6, "div", 2)(7, "input", 3);
        \u0275\u0275twoWayListener("ngModelChange", function RangeSettingComponent_Template_input_ngModelChange_7_listener($event) {
          \u0275\u0275twoWayBindingSet(ctx.value, $event) || (ctx.value = $event);
          return $event;
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(8, "span", 4);
        \u0275\u0275text(9);
        \u0275\u0275elementEnd();
        \u0275\u0275template(10, RangeSettingComponent_Conditional_10_Template, 6, 4);
        \u0275\u0275elementEnd();
      }
      if (rf & 2) {
        \u0275\u0275advance();
        \u0275\u0275property("for", ctx.inputId);
        \u0275\u0275advance();
        \u0275\u0275textInterpolate(ctx.name());
        \u0275\u0275advance(2);
        \u0275\u0275textInterpolate(ctx.description());
        \u0275\u0275advance();
        \u0275\u0275conditional(ctx.descriptionExtra() ? 5 : -1);
        \u0275\u0275advance(2);
        \u0275\u0275classProp("input__disabled", ctx.disabled());
        \u0275\u0275property("id", ctx.inputId)("disabled", ctx.disabled());
        \u0275\u0275twoWayProperty("ngModel", ctx.value);
        \u0275\u0275property("min", ctx.minValue())("max", ctx.maxValue())("step", ctx.stepValue());
        \u0275\u0275advance(2);
        \u0275\u0275textInterpolate(ctx.value());
        \u0275\u0275advance();
        \u0275\u0275conditional(ctx.value() != ctx.oldValue() && !ctx.disabled() ? 10 : -1);
      }
    }, dependencies: [FormsModule, DefaultValueAccessor, RangeValueAccessor, NgControlStatus, NgModel], styles: ["\n\n[_nghost-%COMP%] {\n  display: grid;\n  grid-template-columns: 3fr 2fr;\n  justify-items: start;\n  align-items: center;\n  margin: 1.5rem 0.5rem;\n  gap: 1rem;\n}\n@container (width < 40rem) {\n  [_nghost-%COMP%] {\n    grid-template-columns: 1fr;\n  }\n}\n.content-label[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  text-align: left;\n  gap: 0.5rem;\n  width: 100%;\n}\nlabel[_ngcontent-%COMP%], \nspan[_ngcontent-%COMP%] {\n  font-weight: bold;\n  text-wrap: nowrap;\n}\nsvg[_ngcontent-%COMP%] {\n  width: 1.5rem;\n  height: 1.5rem;\n  cursor: pointer;\n}\nbutton[_ngcontent-%COMP%] {\n  width: 2.5rem;\n  height: 2.5rem;\n}\n@container (width < 40rem) {\n  button[_ngcontent-%COMP%] {\n    width: 2rem;\n    height: 2rem;\n  }\n}\n.content-input[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  gap: 0.5rem;\n  width: 100%;\n  max-width: 100%;\n  overflow: hidden;\n}\ninput[_ngcontent-%COMP%] {\n  width: 15vw;\n  max-width: 25rem;\n  height: 3rem;\n  padding: 0.25rem;\n  text-align: center;\n  font-family: inherit;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n}\n@container (width < 40rem) {\n  input[_ngcontent-%COMP%] {\n    flex: 1;\n    width: auto;\n    max-width: 50vw;\n    height: 2rem;\n  }\n}\n.content-input__value[_ngcontent-%COMP%] {\n  text-align: center;\n  align-self: center;\n  width: 3ch;\n}\n.input__disabled[_ngcontent-%COMP%] {\n  background-color: var(--color-surface-container-low);\n  cursor: not-allowed;\n  text-decoration: line-through 2px var(--color-danger);\n}\n/*# sourceMappingURL=range-setting.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(RangeSettingComponent, [{
    type: Component,
    args: [{ selector: "app-range-setting", imports: [FormsModule], template: `<div class="content-label">
  <label [for]="inputId">{{ name() }}</label>
  <small>{{ description() }}</small>
  @if (descriptionExtra()) {
    <small>{{ descriptionExtra() }}</small>
  }
</div>
<div class="content-input">
  <input
    [id]="inputId"
    type="range"
    [class.input__disabled]="disabled()"
    [disabled]="disabled()"
    [(ngModel)]="value"
    [min]="minValue()"
    [max]="maxValue()"
    [step]="stepValue()"
  />
  <span class="content-input__value">{{ value() }}</span>
  @if (value() != oldValue() && !disabled()) {
    <button class="secondary icononly-button" [id]="inputId + 'reset'" [title]="'Reset ' + name()" (click)="resetValue()">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
        <path
          d="M263-179.67v-84h317.67q65 0 110.83-45.5t45.83-110.5q0-64.33-45.83-110.16-45.83-45.84-110.83-45.84H297.33l104 104-58.66 57.34-204-203 204-204 58.66 57.66-104 104H580q99.67 0 170.5 70.17t70.83 169.83q0 100.34-70.83 170.17-70.83 69.83-170.5 69.83H263Z"
        />
      </svg>
    </button>
    <button class="primary icononly-button" [id]="inputId + 'update'" [title]="'Update ' + name()" (click)="onSubmitValue()">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
        <path d="M378-235 142-471l52-52 184 184 388-388 52 52-440 440Z" />
      </svg>
    </button>
  }
</div>
`, styles: ["/* src/app/settings/profiles/settings/range-setting/range-setting.component.scss */\n:host {\n  display: grid;\n  grid-template-columns: 3fr 2fr;\n  justify-items: start;\n  align-items: center;\n  margin: 1.5rem 0.5rem;\n  gap: 1rem;\n}\n@container (width < 40rem) {\n  :host {\n    grid-template-columns: 1fr;\n  }\n}\n.content-label {\n  display: flex;\n  flex-direction: column;\n  text-align: left;\n  gap: 0.5rem;\n  width: 100%;\n}\nlabel,\nspan {\n  font-weight: bold;\n  text-wrap: nowrap;\n}\nsvg {\n  width: 1.5rem;\n  height: 1.5rem;\n  cursor: pointer;\n}\nbutton {\n  width: 2.5rem;\n  height: 2.5rem;\n}\n@container (width < 40rem) {\n  button {\n    width: 2rem;\n    height: 2rem;\n  }\n}\n.content-input {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  gap: 0.5rem;\n  width: 100%;\n  max-width: 100%;\n  overflow: hidden;\n}\ninput {\n  width: 15vw;\n  max-width: 25rem;\n  height: 3rem;\n  padding: 0.25rem;\n  text-align: center;\n  font-family: inherit;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n}\n@container (width < 40rem) {\n  input {\n    flex: 1;\n    width: auto;\n    max-width: 50vw;\n    height: 2rem;\n  }\n}\n.content-input__value {\n  text-align: center;\n  align-self: center;\n  width: 3ch;\n}\n.input__disabled {\n  background-color: var(--color-surface-container-low);\n  cursor: not-allowed;\n  text-decoration: line-through 2px var(--color-danger);\n}\n/*# sourceMappingURL=range-setting.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(RangeSettingComponent, { className: "RangeSettingComponent", filePath: "src/app/settings/profiles/settings/range-setting/range-setting.component.ts", lineNumber: 10 });
})();

// src/app/settings/profiles/settings/text-setting/text-setting.component.ts
function TextSettingComponent_Conditional_6_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "small");
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = \u0275\u0275nextContext();
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(ctx_r0.descriptionExtra());
  }
}
function TextSettingComponent_Conditional_9_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "button", 5);
    \u0275\u0275listener("click", function TextSettingComponent_Conditional_9_Template_button_click_0_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r0 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r0.resetValue());
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 6);
    \u0275\u0275element(2, "path", 7);
    \u0275\u0275elementEnd()();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(3, "button", 8);
    \u0275\u0275listener("click", function TextSettingComponent_Conditional_9_Template_button_click_3_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r0 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r0.onSubmitValue());
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(4, "svg", 6);
    \u0275\u0275element(5, "path", 9);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const ctx_r0 = \u0275\u0275nextContext();
    \u0275\u0275property("id", ctx_r0.inputId + "reset")("title", "Reset " + ctx_r0.name());
    \u0275\u0275advance(3);
    \u0275\u0275property("id", ctx_r0.inputId + "update")("title", "Update " + ctx_r0.name());
  }
}
var TextSettingComponent = class _TextSettingComponent {
  constructor() {
    this.inputId = "text-setting-" + Math.random().toString(36).substring(2, 10);
    this.name = input.required();
    this.description = input("");
    this.descriptionExtra = input("");
    this.isNumberType = input.required();
    this.isLongInput = input.required();
    this.placeholder = input("");
    this.value = model.required();
    this.minLength = input(0);
    this.maxLength = input(150);
    this.autocomplete = input("off");
    this.disabled = input(false);
    this.oldValue = signal("");
    this.onSubmit = output();
  }
  // ngOnInit() {
  //   this.oldValue.set(this.value());
  // }
  ngOnChanges() {
    this.oldValue.set(this.value());
  }
  resetValue() {
    this.value.set(this.oldValue());
  }
  onSubmitValue() {
    let submitValue = this.value();
    submitValue = submitValue.toString().trim();
    this.onSubmit.emit(submitValue);
    this.oldValue.set(submitValue);
  }
  static {
    this.\u0275fac = function TextSettingComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _TextSettingComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _TextSettingComponent, selectors: [["app-text-setting"]], inputs: { name: [1, "name"], description: [1, "description"], descriptionExtra: [1, "descriptionExtra"], isNumberType: [1, "isNumberType"], isLongInput: [1, "isLongInput"], placeholder: [1, "placeholder"], value: [1, "value"], minLength: [1, "minLength"], maxLength: [1, "maxLength"], autocomplete: [1, "autocomplete"], disabled: [1, "disabled"] }, outputs: { value: "valueChange", onSubmit: "onSubmit" }, features: [\u0275\u0275NgOnChangesFeature], decls: 10, vars: 17, consts: [[1, "content"], [1, "content-label"], [3, "for"], [1, "content-input"], [3, "ngModelChange", "id", "type", "disabled", "ngModel", "minlength", "maxlength", "placeholder", "autocomplete"], [1, "secondary", "icononly-button", 3, "click", "id", "title"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M263-179.67v-84h317.67q65 0 110.83-45.5t45.83-110.5q0-64.33-45.83-110.16-45.83-45.84-110.83-45.84H297.33l104 104-58.66 57.34-204-203 204-204 58.66 57.66-104 104H580q99.67 0 170.5 70.17t70.83 169.83q0 100.34-70.83 170.17-70.83 69.83-170.5 69.83H263Z"], [1, "primary", "icononly-button", 3, "click", "id", "title"], ["d", "M378-235 142-471l52-52 184 184 388-388 52 52-440 440Z"]], template: function TextSettingComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "div", 0)(1, "div", 1)(2, "label", 2);
        \u0275\u0275text(3);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(4, "small");
        \u0275\u0275text(5);
        \u0275\u0275elementEnd();
        \u0275\u0275template(6, TextSettingComponent_Conditional_6_Template, 2, 1, "small");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(7, "div", 3)(8, "input", 4);
        \u0275\u0275twoWayListener("ngModelChange", function TextSettingComponent_Template_input_ngModelChange_8_listener($event) {
          \u0275\u0275twoWayBindingSet(ctx.value, $event) || (ctx.value = $event);
          return $event;
        });
        \u0275\u0275elementEnd();
        \u0275\u0275template(9, TextSettingComponent_Conditional_9_Template, 6, 4);
        \u0275\u0275elementEnd()();
      }
      if (rf & 2) {
        \u0275\u0275advance(2);
        \u0275\u0275property("for", ctx.inputId);
        \u0275\u0275advance();
        \u0275\u0275textInterpolate(ctx.name());
        \u0275\u0275advance(2);
        \u0275\u0275textInterpolate(ctx.description());
        \u0275\u0275advance();
        \u0275\u0275conditional(ctx.descriptionExtra() ? 6 : -1);
        \u0275\u0275advance(2);
        \u0275\u0275classProp("input__long", ctx.isLongInput())("input__disabled", ctx.disabled());
        \u0275\u0275property("id", ctx.inputId)("type", ctx.isNumberType() ? "number" : "text")("disabled", ctx.disabled());
        \u0275\u0275twoWayProperty("ngModel", ctx.value);
        \u0275\u0275property("minlength", ctx.minLength())("maxlength", ctx.maxLength())("placeholder", ctx.placeholder())("autocomplete", ctx.autocomplete());
        \u0275\u0275advance();
        \u0275\u0275conditional(ctx.value() != ctx.oldValue() && !ctx.disabled() ? 9 : -1);
      }
    }, dependencies: [FormsModule, DefaultValueAccessor, NgControlStatus, MinLengthValidator, MaxLengthValidator, NgModel], styles: ["\n\n[_nghost-%COMP%] {\n  display: contents;\n}\n.content[_ngcontent-%COMP%] {\n  display: grid;\n  grid-template-columns: 3fr 2fr;\n  justify-items: start;\n  align-items: center;\n  margin: 1.5rem 0.5rem;\n  gap: 1rem;\n}\n@container (width < 40rem) {\n  .content[_ngcontent-%COMP%] {\n    grid-template-columns: 1fr;\n  }\n}\n.content-label[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  text-align: left;\n  gap: 0.5rem;\n  width: 100%;\n}\nlabel[_ngcontent-%COMP%], \nspan[_ngcontent-%COMP%] {\n  font-weight: bold;\n  text-wrap: nowrap;\n}\nsvg[_ngcontent-%COMP%] {\n  width: 1.5rem;\n  height: 1.5rem;\n  cursor: pointer;\n}\nbutton[_ngcontent-%COMP%] {\n  width: 2.5rem;\n  height: 2.5rem;\n}\n@container (width < 40rem) {\n  button[_ngcontent-%COMP%] {\n    width: 2rem;\n    height: 2rem;\n  }\n}\n.content-input[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  gap: 0.5rem;\n  width: 100%;\n  max-width: 100%;\n  overflow: hidden;\n}\ninput[_ngcontent-%COMP%] {\n  width: 5rem;\n  height: 3rem;\n  padding: 0.25rem;\n  text-align: center;\n  font-family: inherit;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n}\n.input__long[_ngcontent-%COMP%] {\n  width: auto;\n  flex: 1;\n  max-width: calc(100% - 6rem);\n  field-sizing: content;\n  font-size: larger;\n}\n@container (width < 40rem) {\n  .input__long[_ngcontent-%COMP%] {\n    width: auto;\n    max-width: none;\n  }\n}\n.input__disabled[_ngcontent-%COMP%] {\n  background-color: var(--color-surface-container-low);\n  cursor: not-allowed;\n  text-decoration: line-through 2px var(--color-danger);\n}\n/*# sourceMappingURL=text-setting.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(TextSettingComponent, [{
    type: Component,
    args: [{ selector: "app-text-setting", imports: [FormsModule], template: `<div class="content">
  <div class="content-label">
    <label [for]="inputId">{{ name() }}</label>
    <small>{{ description() }}</small>
    @if (descriptionExtra()) {
      <small>{{ descriptionExtra() }}</small>
    }
  </div>
  <div class="content-input">
    <input
      [id]="inputId"
      [type]="isNumberType() ? 'number' : 'text'"
      [class.input__long]="isLongInput()"
      [class.input__disabled]="disabled()"
      [disabled]="disabled()"
      [(ngModel)]="value"
      [minlength]="minLength()"
      [maxlength]="maxLength()"
      [placeholder]="placeholder()"
      [autocomplete]="autocomplete()"
    />
    @if (value() != oldValue() && !disabled()) {
      <button class="secondary icononly-button" [id]="inputId + 'reset'" [title]="'Reset ' + name()" (click)="resetValue()">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
          <path
            d="M263-179.67v-84h317.67q65 0 110.83-45.5t45.83-110.5q0-64.33-45.83-110.16-45.83-45.84-110.83-45.84H297.33l104 104-58.66 57.34-204-203 204-204 58.66 57.66-104 104H580q99.67 0 170.5 70.17t70.83 169.83q0 100.34-70.83 170.17-70.83 69.83-170.5 69.83H263Z"
          />
        </svg>
      </button>
      <button class="primary icononly-button" [id]="inputId + 'update'" [title]="'Update ' + name()" (click)="onSubmitValue()">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
          <path d="M378-235 142-471l52-52 184 184 388-388 52 52-440 440Z" />
        </svg>
      </button>
    }
  </div>
</div>
`, styles: ["/* src/app/settings/profiles/settings/text-setting/text-setting.component.scss */\n:host {\n  display: contents;\n}\n.content {\n  display: grid;\n  grid-template-columns: 3fr 2fr;\n  justify-items: start;\n  align-items: center;\n  margin: 1.5rem 0.5rem;\n  gap: 1rem;\n}\n@container (width < 40rem) {\n  .content {\n    grid-template-columns: 1fr;\n  }\n}\n.content-label {\n  display: flex;\n  flex-direction: column;\n  text-align: left;\n  gap: 0.5rem;\n  width: 100%;\n}\nlabel,\nspan {\n  font-weight: bold;\n  text-wrap: nowrap;\n}\nsvg {\n  width: 1.5rem;\n  height: 1.5rem;\n  cursor: pointer;\n}\nbutton {\n  width: 2.5rem;\n  height: 2.5rem;\n}\n@container (width < 40rem) {\n  button {\n    width: 2rem;\n    height: 2rem;\n  }\n}\n.content-input {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  gap: 0.5rem;\n  width: 100%;\n  max-width: 100%;\n  overflow: hidden;\n}\ninput {\n  width: 5rem;\n  height: 3rem;\n  padding: 0.25rem;\n  text-align: center;\n  font-family: inherit;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n}\n.input__long {\n  width: auto;\n  flex: 1;\n  max-width: calc(100% - 6rem);\n  field-sizing: content;\n  font-size: larger;\n}\n@container (width < 40rem) {\n  .input__long {\n    width: auto;\n    max-width: none;\n  }\n}\n.input__disabled {\n  background-color: var(--color-surface-container-low);\n  cursor: not-allowed;\n  text-decoration: line-through 2px var(--color-danger);\n}\n/*# sourceMappingURL=text-setting.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(TextSettingComponent, { className: "TextSettingComponent", filePath: "src/app/settings/profiles/settings/text-setting/text-setting.component.ts", lineNumber: 10 });
})();

// src/app/settings/profiles/edit-profile/edit-profile.component.ts
var _c05 = ["deleteProfileDialog"];
function EditProfileComponent_Conditional_74_For_11_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "tr")(1, "td");
    \u0275\u0275text(2);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "td");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(5, "td");
    \u0275\u0275text(6);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const filter_r2 = ctx.$implicit;
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(filter_r2.filter_by);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(filter_r2.filter_condition);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(filter_r2.filter_value);
  }
}
function EditProfileComponent_Conditional_74_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "table", 28)(1, "thead")(2, "tr")(3, "th");
    \u0275\u0275text(4, "Column");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(5, "th");
    \u0275\u0275text(6, "Condition");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(7, "th");
    \u0275\u0275text(8, "Value");
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(9, "tbody");
    \u0275\u0275repeaterCreate(10, EditProfileComponent_Conditional_74_For_11_Template, 7, 3, "tr", null, \u0275\u0275repeaterTrackByIdentity);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    let tmp_2_0;
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275advance(10);
    \u0275\u0275repeater((tmp_2_0 = ctx_r2.profile()) == null ? null : tmp_2_0.customfilter == null ? null : tmp_2_0.customfilter.filters);
  }
}
function EditProfileComponent_Conditional_75_ng_template_0_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p");
    \u0275\u0275text(1, "No filters defined for this profile.");
    \u0275\u0275elementEnd();
  }
}
function EditProfileComponent_Conditional_75_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, EditProfileComponent_Conditional_75_ng_template_0_Template, 2, 0, "ng-template", null, 1, \u0275\u0275templateRefExtractor);
  }
}
var EditProfileComponent = class _EditProfileComponent {
  constructor() {
    this.viewContainerRef = inject(ViewContainerRef);
    this.router = inject(Router);
    this.profileId = input(0, {
      transform: (value) => {
        const num = Number(value);
        return isNaN(num) ? 0 : num;
      }
    });
    this.profileService = inject(ProfileService);
    this.profile = this.profileService.selectedProfile;
    this.minLimitMax = computed(() => {
      let _profile = this.profile();
      if (_profile && _profile.max_duration) {
        return _profile.max_duration - 60;
      }
      return 540;
    });
    this.maxLimitMin = computed(() => {
      let _profile = this.profile();
      if (_profile && _profile.min_duration) {
        return _profile.min_duration + 60;
      }
      return 90;
    });
    this.trueFalseOptions = ["true", "false"];
    this.fileFormatOptions = ["mkv", "mp4", "webm"];
    this.audioFormatOptions = ["aac", "ac3", "eac3", "flac", "opus", "copy"];
    this.videoFormatOptions = ["h264", "h265", "vp8", "vp9", "av1", "copy"];
    this.videoResolutionOptions = ["360", "480", "720", "1080", "1440", "2160"];
    this.subtitleFormatOptions = ["srt", "vtt"];
    this.isLoading = false;
    this.updateResults = [];
    this.profileName = "";
    this.videoResolution = 1080;
    this.subtitlesLanguage = "en";
    this.fileName = "";
    this.excludeWords = "";
    this.minDuration = 30;
    this.maxDuration = 600;
    this.searchQuery = "";
    this.emptyCustomFilter = {
      id: null,
      filter_name: "",
      filter_type: "TRAILER",
      filters: []
    };
    this.customFilter = computed(() => {
      let _profile = this.profile();
      if (_profile && _profile.customfilter) {
        return _profile.customfilter;
      }
      return this.emptyCustomFilter;
    });
    this.deleteDialog = viewChild.required("deleteProfileDialog");
    this.closeDeleteDialog = () => this.deleteDialog().nativeElement.close();
    this.showDeleteDialog = () => this.deleteDialog().nativeElement.showModal();
    effect(() => {
      let id = this.profileId();
      this.profileService.selectedProfileId.set(id);
      if (id <= 0) {
        this.openFilterDialog();
      } else {
      }
    });
  }
  openFilterDialog() {
    const dialogRef = this.viewContainerRef.createComponent(AddCustomFilterDialogComponent);
    dialogRef.setInput("customFilter", this.customFilter());
    dialogRef.setInput("filterType", "TRAILER");
    dialogRef.instance.dialogClosed.subscribe((emitValue) => {
      if (emitValue !== -1) {
        this.profileService.allProfiles.reload();
      }
      dialogRef.destroy();
    });
  }
  onConfirmDelete() {
    this.closeDeleteDialog();
    this.profileService.deleteProfile(this.profileId());
    this.router.navigate(["/settings/profiles"]);
  }
  static {
    this.\u0275fac = function EditProfileComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _EditProfileComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _EditProfileComponent, selectors: [["app-edit-profile"]], viewQuery: function EditProfileComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuerySignal(ctx.deleteDialog, _c05, 5);
      }
      if (rf & 2) {
        \u0275\u0275queryAdvance();
      }
    }, inputs: { profileId: [1, "profileId"] }, decls: 91, vars: 85, consts: [["deleteProfileDialog", ""], ["noFilters", ""], [1, "icon-button", "danger", "top-right-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M259.09-114.02q-28.45 0-48.41-19.89-19.96-19.89-19.96-48.24v-565.94h-45.07v-68.13h198.28v-34.3h271.9v34.3h198.52v68.13h-45.07v565.94q0 27.6-20.33 47.86-20.34 20.27-48.04 20.27H259.09Zm441.82-634.07H259.09v565.94h441.82v-565.94ZM363.89-266.24h64.07v-399h-64.07v399Zm168.15 0h64.31v-399h-64.31v399ZM259.09-748.09v565.94-565.94Z"], [1, "text"], ["open", ""], [1, "setting-group"], ["name", "Profile Enabled", "description", "Enable or disable this profile", 3, "optionChange", "options", "selectedOption"], ["name", "File Format", "description", "Final file format(extension) of the trailer file.", 3, "optionChange", "options", "selectedOption"], ["name", "File Name", "description", "File name to use for downloaded trailers.", 3, "onSubmit", "isNumberType", "isLongInput", "placeholder", "autocomplete", "minLength", "maxLength", "value", "disabled"], ["name", "Folder Enabled", "description", "Save trailer file in a seperate folder inside Media folder.", 3, "optionChange", "options", "selectedOption"], ["name", "Folder Name", "description", "Name of the folder to save trailer file.", 3, "onSubmit", "isNumberType", "isLongInput", "placeholder", "autocomplete", "minLength", "maxLength", "value", "disabled"], ["name", "Embed Metadata", "description", "Embed info from YouTube video in the trailer file.", 3, "optionChange", "options", "selectedOption"], ["name", "Remove Silence", "description", "Detect and remove silence (3s+, 30dB) from the end of the trailer file.", 3, "optionChange", "options", "selectedOption"], ["name", "Audio Format", "description", "Final audio format(codec) of the trailer file.", 3, "optionChange", "options", "selectedOption"], ["name", "Audio Volume Level", "description", "Volume level of the audio in the trailer file. Value less than 100 will reduce the loudness and viceversa!", "descriptionExtra", "Default is 100 (Full Volume). Minimum is 1. Maximum is 200.", 3, "onSubmit", "minValue", "maxValue", "stepValue", "value", "disabled"], ["name", "Video Format", "description", "Final video format(codec) of the trailer file.", 3, "optionChange", "options", "selectedOption"], ["name", "Video Resolution", "description", "Resolution of the trailer video file.", 3, "optionChange", "options", "selectedOption"], ["name", "Subtitles Enabled", "description", "Enable or disable subtitle download for this profile.", 3, "optionChange", "options", "selectedOption"], ["name", "Subtitles Format", "description", "Final subtitle format of the trailer file.", 3, "optionChange", "options", "selectedOption"], ["name", "Subtitles Language", "description", "Language of the subtitle to download. Use 2-letter ISO language code.", 3, "onSubmit", "isNumberType", "isLongInput", "placeholder", "autocomplete", "minLength", "maxLength", "value", "disabled"], ["name", "Search Query", "description", "Query to use when searching for trailers on YouTube.", 3, "onSubmit", "isNumberType", "isLongInput", "placeholder", "autocomplete", "minLength", "maxLength", "value", "disabled"], ["name", "Min Duration", "description", "Minimum video duration (in seconds) to consider while searching.", "descriptionExtra", "Default is 30. Minimum is 30. Should be atmost `Maximum Duration - 60`.", 3, "onSubmit", "minValue", "maxValue", "value", "disabled"], ["name", "Max Duration", "description", "Maximum video duration (in seconds) to consider while searching.", "descriptionExtra", "Default is 600. Maximum is 600. Should be atleast `Minimum Duration + 60`.", 3, "onSubmit", "minValue", "maxValue", "value", "disabled"], ["name", "Always Search", "description", "Enable this to always search for trailers, ignoring the youtube id received from Radarr.", 3, "optionChange", "options", "selectedOption"], ["name", "Include Words in Title", "description", "Download a video only if certain words exist in video title. Comma-separated list.", "descriptionExtra", "Eg: 'trailer, official'", 3, "onSubmit", "isNumberType", "isLongInput", "placeholder", "autocomplete", "minLength", "maxLength", "value", "disabled"], ["name", "Exclude Words in Title", "description", "Exclude downloading a video if certain words exist in video title. Comma-separated list.", "descriptionExtra", "Eg: 'teaser, behind the scenes, review, comment'", 3, "onSubmit", "isNumberType", "isLongInput", "placeholder", "autocomplete", "minLength", "maxLength", "value", "disabled"], [1, "filter-details"], [1, "primary", "filters-button", 3, "click"], [3, "click"], [1, "dialog-content", 3, "click"], ["tabindex", "2", 1, "danger", 3, "click"], ["tabindex", "1", 1, "secondary", 3, "click"]], template: function EditProfileComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275elementStart(0, "h2");
        \u0275\u0275text(1);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(2, "button", 2);
        \u0275\u0275listener("click", function EditProfileComponent_Template_button_click_2_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.showDeleteDialog());
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(3, "svg", 3);
        \u0275\u0275element(4, "path", 4);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(5, "span", 5);
        \u0275\u0275text(6, "Delete");
        \u0275\u0275elementEnd()();
        \u0275\u0275element(7, "hr");
        \u0275\u0275elementStart(8, "section")(9, "details", 6)(10, "summary");
        \u0275\u0275text(11, "General");
        \u0275\u0275elementEnd();
        \u0275\u0275element(12, "hr");
        \u0275\u0275elementStart(13, "div", 7)(14, "app-options-setting", 8);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_14_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("enabled", $event));
        });
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(15, "section")(16, "details", 6)(17, "summary");
        \u0275\u0275text(18, "File");
        \u0275\u0275elementEnd();
        \u0275\u0275element(19, "hr");
        \u0275\u0275elementStart(20, "div", 7)(21, "app-options-setting", 9);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_21_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("file_format", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(22, "app-text-setting", 10);
        \u0275\u0275listener("onSubmit", function EditProfileComponent_Template_app_text_setting_onSubmit_22_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("file_name", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(23, "app-options-setting", 11);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_23_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("folder_enabled", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(24, "app-text-setting", 12);
        \u0275\u0275listener("onSubmit", function EditProfileComponent_Template_app_text_setting_onSubmit_24_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("folder_name", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(25, "app-options-setting", 13);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_25_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("embed_metadata", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(26, "app-options-setting", 14);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_26_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("remove_silence", $event));
        });
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(27, "section")(28, "details", 6)(29, "summary");
        \u0275\u0275text(30, "Audio");
        \u0275\u0275elementEnd();
        \u0275\u0275element(31, "hr");
        \u0275\u0275elementStart(32, "div", 7)(33, "app-options-setting", 15);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_33_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("audio_format", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(34, "app-range-setting", 16);
        \u0275\u0275listener("onSubmit", function EditProfileComponent_Template_app_range_setting_onSubmit_34_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("audio_volume_level", $event));
        });
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(35, "section")(36, "details", 6)(37, "summary");
        \u0275\u0275text(38, "Video");
        \u0275\u0275elementEnd();
        \u0275\u0275element(39, "hr");
        \u0275\u0275elementStart(40, "div", 7)(41, "app-options-setting", 17);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_41_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("video_format", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(42, "app-options-setting", 18);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_42_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("video_resolution", $event));
        });
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(43, "section")(44, "details", 6)(45, "summary");
        \u0275\u0275text(46, "Subtitle");
        \u0275\u0275elementEnd();
        \u0275\u0275element(47, "hr");
        \u0275\u0275elementStart(48, "div", 7)(49, "app-options-setting", 19);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_49_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("subtitles_enabled", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(50, "app-options-setting", 20);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_50_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("subtitles_format", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(51, "app-text-setting", 21);
        \u0275\u0275listener("onSubmit", function EditProfileComponent_Template_app_text_setting_onSubmit_51_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("subtitles_language", $event));
        });
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(52, "section")(53, "details", 6)(54, "summary");
        \u0275\u0275text(55, "Search");
        \u0275\u0275elementEnd();
        \u0275\u0275element(56, "hr");
        \u0275\u0275elementStart(57, "div", 7)(58, "app-text-setting", 22);
        \u0275\u0275listener("onSubmit", function EditProfileComponent_Template_app_text_setting_onSubmit_58_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("search_query", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(59, "app-range-setting", 23);
        \u0275\u0275listener("onSubmit", function EditProfileComponent_Template_app_range_setting_onSubmit_59_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("min_duration", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(60, "app-range-setting", 24);
        \u0275\u0275listener("onSubmit", function EditProfileComponent_Template_app_range_setting_onSubmit_60_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("max_duration", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(61, "app-options-setting", 25);
        \u0275\u0275listener("optionChange", function EditProfileComponent_Template_app_options_setting_optionChange_61_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("always_search", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(62, "app-text-setting", 26);
        \u0275\u0275listener("onSubmit", function EditProfileComponent_Template_app_text_setting_onSubmit_62_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("include_words", $event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(63, "app-text-setting", 27);
        \u0275\u0275listener("onSubmit", function EditProfileComponent_Template_app_text_setting_onSubmit_63_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.profileService.updateSetting("exclude_words", $event));
        });
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(64, "section")(65, "details", 6)(66, "summary");
        \u0275\u0275text(67, "Filters");
        \u0275\u0275elementEnd();
        \u0275\u0275element(68, "hr");
        \u0275\u0275elementStart(69, "div", 7)(70, "p");
        \u0275\u0275text(71, "Filters are conditions that media must meet. This profile is used only when all conditions match.");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(72, "small");
        \u0275\u0275text(73, "Think of filters as rules; if a movie or show matches all the rules, this profile will be used.");
        \u0275\u0275elementEnd();
        \u0275\u0275template(74, EditProfileComponent_Conditional_74_Template, 12, 0, "table", 28)(75, EditProfileComponent_Conditional_75_Template, 2, 0);
        \u0275\u0275elementStart(76, "button", 29);
        \u0275\u0275listener("click", function EditProfileComponent_Template_button_click_76_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.openFilterDialog());
        });
        \u0275\u0275text(77, "Add/Edit Filters");
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(78, "dialog", 30, 0);
        \u0275\u0275listener("click", function EditProfileComponent_Template_dialog_click_78_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeDeleteDialog());
        });
        \u0275\u0275elementStart(80, "div", 31);
        \u0275\u0275listener("click", function EditProfileComponent_Template_div_click_80_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(81, "h2");
        \u0275\u0275text(82, "Delete Profile");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(83, "p");
        \u0275\u0275text(84, "This will Delete the profile and no longer use it for downloads");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(85, "p");
        \u0275\u0275text(86, "Delete the profile?");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(87, "button", 32);
        \u0275\u0275listener("click", function EditProfileComponent_Template_button_click_87_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onConfirmDelete());
        });
        \u0275\u0275text(88, "Delete");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(89, "button", 33);
        \u0275\u0275listener("click", function EditProfileComponent_Template_button_click_89_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeDeleteDialog());
        });
        \u0275\u0275text(90, "Cancel");
        \u0275\u0275elementEnd()()();
      }
      if (rf & 2) {
        let tmp_1_0;
        let tmp_3_0;
        let tmp_5_0;
        let tmp_12_0;
        let tmp_15_0;
        let tmp_22_0;
        let tmp_23_0;
        let tmp_25_0;
        let tmp_27_0;
        let tmp_29_0;
        let tmp_33_0;
        let tmp_36_0;
        let tmp_38_0;
        let tmp_40_0;
        let tmp_42_0;
        let tmp_49_0;
        let tmp_50_0;
        let tmp_57_0;
        let tmp_61_0;
        let tmp_65_0;
        let tmp_68_0;
        let tmp_75_0;
        let tmp_83_0;
        let tmp_85_0;
        \u0275\u0275advance();
        \u0275\u0275textInterpolate1("Profile: ", (tmp_1_0 = ctx.profile()) == null ? null : tmp_1_0.customfilter == null ? null : tmp_1_0.customfilter.filter_name, "");
        \u0275\u0275advance(13);
        \u0275\u0275property("options", ctx.trueFalseOptions)("selectedOption", (tmp_3_0 = ctx.profile()) == null ? null : tmp_3_0.enabled);
        \u0275\u0275advance(7);
        \u0275\u0275property("options", ctx.fileFormatOptions)("selectedOption", (tmp_5_0 = ctx.profile()) == null ? null : tmp_5_0.file_format);
        \u0275\u0275advance();
        \u0275\u0275property("isNumberType", false)("isLongInput", true)("placeholder", "File Name")("autocomplete", "off")("minLength", 1)("maxLength", 50)("value", (tmp_12_0 = (tmp_12_0 = ctx.profile()) == null ? null : tmp_12_0.file_name) !== null && tmp_12_0 !== void 0 ? tmp_12_0 : "")("disabled", false);
        \u0275\u0275advance();
        \u0275\u0275property("options", ctx.trueFalseOptions)("selectedOption", (tmp_15_0 = ctx.profile()) == null ? null : tmp_15_0.folder_enabled);
        \u0275\u0275advance();
        \u0275\u0275property("isNumberType", false)("isLongInput", true)("placeholder", "Folder Name")("autocomplete", "off")("minLength", 1)("maxLength", 50)("value", (tmp_22_0 = (tmp_22_0 = ctx.profile()) == null ? null : tmp_22_0.folder_name) !== null && tmp_22_0 !== void 0 ? tmp_22_0 : "")("disabled", !((tmp_23_0 = ctx.profile()) == null ? null : tmp_23_0.folder_enabled));
        \u0275\u0275advance();
        \u0275\u0275property("options", ctx.trueFalseOptions)("selectedOption", (tmp_25_0 = ctx.profile()) == null ? null : tmp_25_0.embed_metadata);
        \u0275\u0275advance();
        \u0275\u0275property("options", ctx.trueFalseOptions)("selectedOption", (tmp_27_0 = ctx.profile()) == null ? null : tmp_27_0.remove_silence);
        \u0275\u0275advance(7);
        \u0275\u0275property("options", ctx.audioFormatOptions)("selectedOption", (tmp_29_0 = ctx.profile()) == null ? null : tmp_29_0.audio_format);
        \u0275\u0275advance();
        \u0275\u0275property("minValue", 1)("maxValue", 200)("stepValue", 1)("value", (tmp_33_0 = (tmp_33_0 = ctx.profile()) == null ? null : tmp_33_0.audio_volume_level) !== null && tmp_33_0 !== void 0 ? tmp_33_0 : 100)("disabled", false);
        \u0275\u0275advance(7);
        \u0275\u0275property("options", ctx.videoFormatOptions)("selectedOption", (tmp_36_0 = ctx.profile()) == null ? null : tmp_36_0.video_format);
        \u0275\u0275advance();
        \u0275\u0275property("options", ctx.videoResolutionOptions)("selectedOption", (tmp_38_0 = ctx.profile()) == null ? null : tmp_38_0.video_resolution);
        \u0275\u0275advance(7);
        \u0275\u0275property("options", ctx.trueFalseOptions)("selectedOption", (tmp_40_0 = ctx.profile()) == null ? null : tmp_40_0.subtitles_enabled);
        \u0275\u0275advance();
        \u0275\u0275property("options", ctx.subtitleFormatOptions)("selectedOption", (tmp_42_0 = ctx.profile()) == null ? null : tmp_42_0.subtitles_format);
        \u0275\u0275advance();
        \u0275\u0275property("isNumberType", false)("isLongInput", false)("placeholder", "Subtitles Language")("autocomplete", "off")("minLength", 2)("maxLength", 2)("value", (tmp_49_0 = (tmp_49_0 = ctx.profile()) == null ? null : tmp_49_0.subtitles_language) !== null && tmp_49_0 !== void 0 ? tmp_49_0 : "en")("disabled", !((tmp_50_0 = ctx.profile()) == null ? null : tmp_50_0.subtitles_enabled));
        \u0275\u0275advance(7);
        \u0275\u0275property("isNumberType", false)("isLongInput", true)("placeholder", "Search Query")("autocomplete", "off")("minLength", 10)("maxLength", 100)("value", (tmp_57_0 = (tmp_57_0 = ctx.profile()) == null ? null : tmp_57_0.search_query) !== null && tmp_57_0 !== void 0 ? tmp_57_0 : "")("disabled", false);
        \u0275\u0275advance();
        \u0275\u0275property("minValue", 30)("maxValue", ctx.minLimitMax())("value", (tmp_61_0 = (tmp_61_0 = ctx.profile()) == null ? null : tmp_61_0.min_duration) !== null && tmp_61_0 !== void 0 ? tmp_61_0 : 30)("disabled", false);
        \u0275\u0275advance();
        \u0275\u0275property("minValue", ctx.maxLimitMin())("maxValue", 600)("value", (tmp_65_0 = (tmp_65_0 = ctx.profile()) == null ? null : tmp_65_0.max_duration) !== null && tmp_65_0 !== void 0 ? tmp_65_0 : 600)("disabled", false);
        \u0275\u0275advance();
        \u0275\u0275property("options", ctx.trueFalseOptions)("selectedOption", (tmp_68_0 = ctx.profile()) == null ? null : tmp_68_0.always_search);
        \u0275\u0275advance();
        \u0275\u0275property("isNumberType", false)("isLongInput", true)("placeholder", "Include Words")("autocomplete", "off")("minLength", 0)("maxLength", 100)("value", (tmp_75_0 = (tmp_75_0 = ctx.profile()) == null ? null : tmp_75_0.include_words) !== null && tmp_75_0 !== void 0 ? tmp_75_0 : "")("disabled", false);
        \u0275\u0275advance();
        \u0275\u0275property("isNumberType", false)("isLongInput", true)("placeholder", "Exclude Words List")("autocomplete", "off")("minLength", 0)("maxLength", 100)("value", (tmp_83_0 = (tmp_83_0 = ctx.profile()) == null ? null : tmp_83_0.exclude_words) !== null && tmp_83_0 !== void 0 ? tmp_83_0 : "")("disabled", false);
        \u0275\u0275advance(11);
        \u0275\u0275conditional(((tmp_85_0 = ctx.profile()) == null ? null : tmp_85_0.customfilter == null ? null : tmp_85_0.customfilter.filters == null ? null : tmp_85_0.customfilter.filters.length) ? 74 : 75);
      }
    }, dependencies: [FormsModule, OptionsSettingComponent, TextSettingComponent, RangeSettingComponent], styles: ["\n\n[_nghost-%COMP%] {\n  position: relative;\n}\n.top-right-button[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 0;\n  right: 0;\n  margin: 10px;\n}\ndetails[_ngcontent-%COMP%] {\n  margin: 0.5rem 0;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  background-color: var(--color-surface-container);\n}\nsummary[_ngcontent-%COMP%] {\n  padding: 1rem;\n  font-weight: bold;\n  cursor: pointer;\n  color: var(--color-primary);\n  white-space: nowrap;\n  overflow: hidden;\n  text-overflow: ellipsis;\n  max-width: calc(100vw - 260px);\n}\n@media (width < 1100px) {\n  summary[_ngcontent-%COMP%] {\n    max-width: calc(100vw - 100px);\n  }\n}\n@media (width < 765px) {\n  summary[_ngcontent-%COMP%] {\n    max-width: calc(100vw - 50px);\n  }\n}\n.setting-group[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  margin: 0 0.5rem;\n  container-type: inline-size;\n}\ntable[_ngcontent-%COMP%] {\n  text-align: center;\n  margin: 1.5rem auto 1rem;\n  padding: 1rem;\n  width: clamp(300px, 50vw, 800px);\n  border-collapse: collapse;\n  border: 2px solid var(--color-outline);\n  font-family: sans-serif;\n  font-size: 0.8rem;\n  letter-spacing: 1px;\n}\nthead[_ngcontent-%COMP%], \ntfoot[_ngcontent-%COMP%] {\n  background-color: var(--color-secondary-container);\n}\nth[_ngcontent-%COMP%], \ntd[_ngcontent-%COMP%] {\n  border: 1px solid var(--color-outline);\n  padding: 8px 10px;\n}\ntd[_ngcontent-%COMP%]:last-of-type {\n  text-align: center;\n}\ntbody[_ngcontent-%COMP%]    > tr[_ngcontent-%COMP%]:nth-of-type(even) {\n  background-color: var(--color-surface-container-high);\n}\n.filters-button[_ngcontent-%COMP%] {\n  width: auto;\n  margin: 1rem auto;\n}\n.dialog-content[_ngcontent-%COMP%] {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog[_ngcontent-%COMP%]::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content[_ngcontent-%COMP%]   button[_ngcontent-%COMP%] {\n  margin: 10px;\n}\n/*# sourceMappingURL=edit-profile.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(EditProfileComponent, [{
    type: Component,
    args: [{ selector: "app-edit-profile", imports: [FormsModule, OptionsSettingComponent, TextSettingComponent, RangeSettingComponent], template: `<h2>Profile: {{ profile()?.customfilter?.filter_name }}</h2>
<button class="icon-button danger top-right-button" (click)="showDeleteDialog()">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
    <path
      d="M259.09-114.02q-28.45 0-48.41-19.89-19.96-19.89-19.96-48.24v-565.94h-45.07v-68.13h198.28v-34.3h271.9v34.3h198.52v68.13h-45.07v565.94q0 27.6-20.33 47.86-20.34 20.27-48.04 20.27H259.09Zm441.82-634.07H259.09v565.94h441.82v-565.94ZM363.89-266.24h64.07v-399h-64.07v399Zm168.15 0h64.31v-399h-64.31v399ZM259.09-748.09v565.94-565.94Z"
    />
  </svg>
  <span class="text">Delete</span>
</button>
<hr />
<!-- General Settings -->
<section>
  <details open>
    <summary>General</summary>
    <hr />
    <div class="setting-group">
      <app-options-setting
        name="Profile Enabled"
        description="Enable or disable this profile"
        [options]="trueFalseOptions"
        [selectedOption]="profile()?.enabled"
        (optionChange)="profileService.updateSetting('enabled', $event)"
      />
    </div>
  </details>
</section>
<!-- File Settings -->
<section>
  <details open>
    <summary>File</summary>
    <hr />
    <div class="setting-group">
      <app-options-setting
        name="File Format"
        description="Final file format(extension) of the trailer file."
        [options]="fileFormatOptions"
        [selectedOption]="profile()?.file_format"
        (optionChange)="profileService.updateSetting('file_format', $event)"
      />
      <app-text-setting
        name="File Name"
        description="File name to use for downloaded trailers."
        [isNumberType]="false"
        [isLongInput]="true"
        [placeholder]="'File Name'"
        [autocomplete]="'off'"
        [minLength]="1"
        [maxLength]="50"
        [value]="profile()?.file_name ?? ''"
        [disabled]="false"
        (onSubmit)="profileService.updateSetting('file_name', $event)"
      />
      <app-options-setting
        name="Folder Enabled"
        description="Save trailer file in a seperate folder inside Media folder."
        [options]="trueFalseOptions"
        [selectedOption]="profile()?.folder_enabled"
        (optionChange)="profileService.updateSetting('folder_enabled', $event)"
      />
      <app-text-setting
        name="Folder Name"
        description="Name of the folder to save trailer file."
        [isNumberType]="false"
        [isLongInput]="true"
        [placeholder]="'Folder Name'"
        [autocomplete]="'off'"
        [minLength]="1"
        [maxLength]="50"
        [value]="profile()?.folder_name ?? ''"
        [disabled]="!profile()?.folder_enabled"
        (onSubmit)="profileService.updateSetting('folder_name', $event)"
      />
      <app-options-setting
        name="Embed Metadata"
        description="Embed info from YouTube video in the trailer file."
        [options]="trueFalseOptions"
        [selectedOption]="profile()?.embed_metadata"
        (optionChange)="profileService.updateSetting('embed_metadata', $event)"
      />
      <app-options-setting
        name="Remove Silence"
        description="Detect and remove silence (3s+, 30dB) from the end of the trailer file."
        [options]="trueFalseOptions"
        [selectedOption]="profile()?.remove_silence"
        (optionChange)="profileService.updateSetting('remove_silence', $event)"
      />
    </div>
  </details>
</section>
<!-- Audio Settings -->
<section>
  <details open>
    <summary>Audio</summary>
    <hr />
    <div class="setting-group">
      <app-options-setting
        name="Audio Format"
        description="Final audio format(codec) of the trailer file."
        [options]="audioFormatOptions"
        [selectedOption]="profile()?.audio_format"
        (optionChange)="profileService.updateSetting('audio_format', $event)"
      />
      <app-range-setting
        name="Audio Volume Level"
        description="Volume level of the audio in the trailer file. Value less than 100 will reduce the loudness and viceversa!"
        descriptionExtra="Default is 100 (Full Volume). Minimum is 1. Maximum is 200."
        [minValue]="1"
        [maxValue]="200"
        [stepValue]="1"
        [value]="profile()?.audio_volume_level ?? 100"
        [disabled]="false"
        (onSubmit)="profileService.updateSetting('audio_volume_level', $event)"
      />
    </div>
  </details>
</section>
<!-- Video Settings -->
<section>
  <details open>
    <summary>Video</summary>
    <hr />
    <div class="setting-group">
      <app-options-setting
        name="Video Format"
        description="Final video format(codec) of the trailer file."
        [options]="videoFormatOptions"
        [selectedOption]="profile()?.video_format"
        (optionChange)="profileService.updateSetting('video_format', $event)"
      />
      <app-options-setting
        name="Video Resolution"
        description="Resolution of the trailer video file."
        [options]="videoResolutionOptions"
        [selectedOption]="profile()?.video_resolution"
        (optionChange)="profileService.updateSetting('video_resolution', $event)"
      />
    </div>
  </details>
</section>
<!-- Subtitle Settings -->
<section>
  <details open>
    <summary>Subtitle</summary>
    <hr />
    <div class="setting-group">
      <app-options-setting
        name="Subtitles Enabled"
        description="Enable or disable subtitle download for this profile."
        [options]="trueFalseOptions"
        [selectedOption]="profile()?.subtitles_enabled"
        (optionChange)="profileService.updateSetting('subtitles_enabled', $event)"
      />
      <app-options-setting
        name="Subtitles Format"
        description="Final subtitle format of the trailer file."
        [options]="subtitleFormatOptions"
        [selectedOption]="profile()?.subtitles_format"
        (optionChange)="profileService.updateSetting('subtitles_format', $event)"
      />
      <app-text-setting
        name="Subtitles Language"
        description="Language of the subtitle to download. Use 2-letter ISO language code."
        [isNumberType]="false"
        [isLongInput]="false"
        [placeholder]="'Subtitles Language'"
        [autocomplete]="'off'"
        [minLength]="2"
        [maxLength]="2"
        [value]="profile()?.subtitles_language ?? 'en'"
        [disabled]="!profile()?.subtitles_enabled"
        (onSubmit)="profileService.updateSetting('subtitles_language', $event)"
      />
    </div>
  </details>
</section>
<!-- Search Settings -->
<section>
  <details open>
    <summary>Search</summary>
    <hr />
    <div class="setting-group">
      <app-text-setting
        name="Search Query"
        description="Query to use when searching for trailers on YouTube."
        [isNumberType]="false"
        [isLongInput]="true"
        [placeholder]="'Search Query'"
        [autocomplete]="'off'"
        [minLength]="10"
        [maxLength]="100"
        [value]="profile()?.search_query ?? ''"
        [disabled]="false"
        (onSubmit)="profileService.updateSetting('search_query', $event)"
      />
      <app-range-setting
        name="Min Duration"
        description="Minimum video duration (in seconds) to consider while searching."
        descriptionExtra="Default is 30. Minimum is 30. Should be atmost \`Maximum Duration - 60\`."
        [minValue]="30"
        [maxValue]="minLimitMax()"
        [value]="profile()?.min_duration ?? 30"
        [disabled]="false"
        (onSubmit)="profileService.updateSetting('min_duration', $event)"
      />
      <app-range-setting
        name="Max Duration"
        description="Maximum video duration (in seconds) to consider while searching."
        descriptionExtra="Default is 600. Maximum is 600. Should be atleast \`Minimum Duration + 60\`."
        [minValue]="maxLimitMin()"
        [maxValue]="600"
        [value]="profile()?.max_duration ?? 600"
        [disabled]="false"
        (onSubmit)="profileService.updateSetting('max_duration', $event)"
      />
      <app-options-setting
        name="Always Search"
        description="Enable this to always search for trailers, ignoring the youtube id received from Radarr."
        [options]="trueFalseOptions"
        [selectedOption]="profile()?.always_search"
        (optionChange)="profileService.updateSetting('always_search', $event)"
      />
      <app-text-setting
        name="Include Words in Title"
        description="Download a video only if certain words exist in video title. Comma-separated list."
        descriptionExtra="Eg: 'trailer, official'"
        [isNumberType]="false"
        [isLongInput]="true"
        [placeholder]="'Include Words'"
        [autocomplete]="'off'"
        [minLength]="0"
        [maxLength]="100"
        [value]="profile()?.include_words ?? ''"
        [disabled]="false"
        (onSubmit)="profileService.updateSetting('include_words', $event)"
      />
      <app-text-setting
        name="Exclude Words in Title"
        description="Exclude downloading a video if certain words exist in video title. Comma-separated list."
        descriptionExtra="Eg: 'teaser, behind the scenes, review, comment'"
        [isNumberType]="false"
        [isLongInput]="true"
        [placeholder]="'Exclude Words List'"
        [autocomplete]="'off'"
        [minLength]="0"
        [maxLength]="100"
        [value]="profile()?.exclude_words ?? ''"
        [disabled]="false"
        (onSubmit)="profileService.updateSetting('exclude_words', $event)"
      />
    </div>
  </details>
</section>
<!-- Table to show filters list -->
<section>
  <details open>
    <summary>Filters</summary>
    <hr />
    <div class="setting-group">
      <p>Filters are conditions that media must meet. This profile is used only when all conditions match.</p>
      <small>Think of filters as rules; if a movie or show matches all the rules, this profile will be used.</small>
      @if (profile()?.customfilter?.filters?.length) {
        <table class="filter-details">
          <thead>
            <tr>
              <th>Column</th>
              <th>Condition</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            @for (filter of profile()?.customfilter?.filters; track filter) {
              <tr>
                <td>{{ filter.filter_by }}</td>
                <td>{{ filter.filter_condition }}</td>
                <td>{{ filter.filter_value }}</td>
              </tr>
            }
          </tbody>
        </table>
      } @else {
        <ng-template #noFilters>
          <p>No filters defined for this profile.</p>
        </ng-template>
      }
      <button class="primary filters-button" (click)="openFilterDialog()">Add/Edit Filters</button>
    </div>
  </details>
</section>

<dialog #deleteProfileDialog (click)="closeDeleteDialog()">
  <div class="dialog-content" (click)="$event.stopPropagation()">
    <h2>Delete Profile</h2>
    <p>This will Delete the profile and no longer use it for downloads</p>
    <p>Delete the profile?</p>
    <button class="danger" (click)="onConfirmDelete()" tabindex="2">Delete</button>
    <button class="secondary" (click)="closeDeleteDialog()" tabindex="1">Cancel</button>
  </div>
</dialog>
`, styles: ["/* src/app/settings/profiles/edit-profile/edit-profile.component.scss */\n:host {\n  position: relative;\n}\n.top-right-button {\n  position: absolute;\n  top: 0;\n  right: 0;\n  margin: 10px;\n}\ndetails {\n  margin: 0.5rem 0;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  background-color: var(--color-surface-container);\n}\nsummary {\n  padding: 1rem;\n  font-weight: bold;\n  cursor: pointer;\n  color: var(--color-primary);\n  white-space: nowrap;\n  overflow: hidden;\n  text-overflow: ellipsis;\n  max-width: calc(100vw - 260px);\n}\n@media (width < 1100px) {\n  summary {\n    max-width: calc(100vw - 100px);\n  }\n}\n@media (width < 765px) {\n  summary {\n    max-width: calc(100vw - 50px);\n  }\n}\n.setting-group {\n  display: flex;\n  flex-direction: column;\n  margin: 0 0.5rem;\n  container-type: inline-size;\n}\ntable {\n  text-align: center;\n  margin: 1.5rem auto 1rem;\n  padding: 1rem;\n  width: clamp(300px, 50vw, 800px);\n  border-collapse: collapse;\n  border: 2px solid var(--color-outline);\n  font-family: sans-serif;\n  font-size: 0.8rem;\n  letter-spacing: 1px;\n}\nthead,\ntfoot {\n  background-color: var(--color-secondary-container);\n}\nth,\ntd {\n  border: 1px solid var(--color-outline);\n  padding: 8px 10px;\n}\ntd:last-of-type {\n  text-align: center;\n}\ntbody > tr:nth-of-type(even) {\n  background-color: var(--color-surface-container-high);\n}\n.filters-button {\n  width: auto;\n  margin: 1rem auto;\n}\n.dialog-content {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content button {\n  margin: 10px;\n}\n/*# sourceMappingURL=edit-profile.component.css.map */\n"] }]
  }], () => [], null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(EditProfileComponent, { className: "EditProfileComponent", filePath: "src/app/settings/profiles/edit-profile/edit-profile.component.ts", lineNumber: 17 });
})();

// src/app/settings/profiles/show-profiles/show-profiles.component.ts
var _c06 = (a0, a1) => [a0, a1];
function ShowProfilesComponent_Conditional_12_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 8);
  }
}
function ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Conditional_8_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p");
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const profile_r1 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275advance();
    \u0275\u0275textInterpolate2("Subtitle: ", profile_r1.subtitles_language, " | ", profile_r1.subtitles_format, "");
  }
}
function ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Conditional_9_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p");
    \u0275\u0275text(1, "Subtitles: No");
    \u0275\u0275elementEnd();
  }
}
function ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Conditional_11_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 14);
    \u0275\u0275element(1, "path", 16);
    \u0275\u0275elementEnd();
  }
}
function ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Conditional_12_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 15);
    \u0275\u0275element(1, "path", 17);
    \u0275\u0275elementEnd();
  }
}
function ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 10)(1, "h3", 11);
    \u0275\u0275text(2);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "div", 12)(4, "p");
    \u0275\u0275text(5);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(6, "p");
    \u0275\u0275text(7);
    \u0275\u0275elementEnd();
    \u0275\u0275template(8, ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Conditional_8_Template, 2, 2, "p")(9, ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Conditional_9_Template, 2, 0, "p");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(10, "div", 13);
    \u0275\u0275template(11, ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Conditional_11_Template, 2, 0, ":svg:svg", 14)(12, ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Conditional_12_Template, 2, 0, ":svg:svg", 15);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const profile_r1 = ctx.$implicit;
    const ctx_r1 = \u0275\u0275nextContext(3);
    \u0275\u0275property("routerLink", \u0275\u0275pureFunction2(7, _c06, ctx_r1.RouteEdit, profile_r1.id));
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(profile_r1.customfilter.filter_name);
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate2("Video: ", profile_r1.video_resolution, "p | ", profile_r1.video_format, "");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1("Audio: ", profile_r1.audio_format, "");
    \u0275\u0275advance();
    \u0275\u0275conditional(profile_r1.subtitles_enabled ? 8 : 9);
    \u0275\u0275advance(3);
    \u0275\u0275conditional(profile_r1.enabled ? 11 : 12);
  }
}
function ShowProfilesComponent_Conditional_13_Conditional_0_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 9);
    \u0275\u0275repeaterCreate(1, ShowProfilesComponent_Conditional_13_Conditional_0_For_2_Template, 13, 10, "div", 10, \u0275\u0275repeaterTrackByIndex);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext(2);
    \u0275\u0275advance();
    \u0275\u0275repeater(ctx_r1.profileService.allProfiles.value());
  }
}
function ShowProfilesComponent_Conditional_13_Conditional_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 8)(1, "p");
    \u0275\u0275text(2, "No profiles found.");
    \u0275\u0275elementEnd()();
  }
}
function ShowProfilesComponent_Conditional_13_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, ShowProfilesComponent_Conditional_13_Conditional_0_Template, 3, 0, "div", 9)(1, ShowProfilesComponent_Conditional_13_Conditional_1_Template, 3, 0, "div", 8);
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext();
    \u0275\u0275conditional(ctx_r1.profileService.allProfiles.value() && ctx_r1.profileService.allProfiles.value().length > 0 ? 0 : 1);
  }
}
var ShowProfilesComponent = class _ShowProfilesComponent {
  constructor() {
    this.profileService = inject(ProfileService);
    this.router = inject(Router);
    this.viewContainerRef = inject(ViewContainerRef);
    this.isLoading = signal(true);
    this.RouteAdd = RouteAdd;
    this.RouteProfiles = RouteProfiles;
    this.RouteEdit = RouteEdit;
    this.RouteSettings = RouteSettings;
  }
  openFilterDialog() {
    const dialogRef = this.viewContainerRef.createComponent(AddCustomFilterDialogComponent);
    dialogRef.setInput("customFilter", null);
    dialogRef.setInput("filterType", "TRAILER");
    dialogRef.instance.dialogClosed.subscribe((emitValue) => {
      if (emitValue >= 0) {
        this.profileService.allProfiles.reload();
        this.router.navigate(["/settings/profiles/edit", emitValue]);
      }
      dialogRef.destroy();
    });
  }
  static {
    this.\u0275fac = function ShowProfilesComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _ShowProfilesComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _ShowProfilesComponent, selectors: [["app-show-profiles"]], decls: 14, vars: 3, consts: [[1, "title-block"], ["title", "Refresh", 1, "icononly-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", 1, "refresh-icon"], ["d", "M343-107q-120-42-194.5-146.5T74-490q0-29 4-57.5T91-604l-57 33-37-62 185-107 106 184-63 36-54-92q-13 30-18.5 60.5T147-490q0 113 65.5 200T381-171l-38 64Zm291-516v-73h107q-47-60-115.5-93.5T480-823q-66 0-123.5 24T255-734l-38-65q54-45 121-71t142-26q85 0 160.5 33T774-769v-67h73v213H634ZM598-1 413-107l107-184 62 37-54 94q123-17 204.5-110.5T814-489q0-19-2.5-37.5T805-563h74q4 18 6 36.5t2 36.5q0 142-87 251.5T578-96l56 33-36 62Z"], [1, "animated-button", "top-right-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z"], [1, "text"], [1, "center"], [1, "profile-container"], [1, "profile-card", 3, "routerLink"], [1, "profile-card-title"], [1, "profile-card-content"], [1, "profile-card-checkbox", "center"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "title", "Profile Enabled", 1, "profile-card-icon", "success"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "title", "Profile Disabled", 1, "profile-card-icon", "danger"], ["d", "m421-288 294-294-55-54-239 239-121-121-54 54 175 176Zm58.54 224q-85.18 0-161.02-33.02t-132.16-89.34q-56.32-56.32-89.34-132.29T64-480q0-86.27 33.08-162.15 33.08-75.88 89.68-132.47 56.61-56.59 132.22-88.99Q394.59-896 479.56-896q86.33 0 162.51 32.39 76.18 32.4 132.56 89Q831-718 863.5-641.96q32.5 76.04 32.5 162.5 0 85.46-32.39 160.8-32.4 75.34-88.99 131.92Q718.03-130.16 642-97.08 565.98-64 479.54-64Zm.46-73q142.51 0 242.76-100.74Q823-338.49 823-480q0-142.51-100.24-242.76Q622.51-823 480-823q-141.51 0-242.26 100.24Q137-622.51 137-480q0 141.51 100.74 242.26Q338.49-137 480-137Zm0-343Z"], ["d", "M836-29 724-141q-52 37-113.57 57Q548.87-64 480-64q-87.64 0-163.98-32.02-76.34-32.02-132.16-87.84-55.82-55.82-87.84-132.16T64-480q0-68.87 20-130.43Q104-672 141-724L15-850l52-52L888-81l-52 52ZM480-137q54.5 0 102.25-14.5T671-193L498-366l-77 78-175-176 49-49 122 120 27-27-251-251q-27 41-41.5 88.75T137-480q0 146 98.5 244.5T480-137Zm339-99-52-52q26-41 41-89.5T823-480q0-146-98.5-244.5T480-823q-54 0-102.5 15T288-767l-52-52q50.84-36.43 112.62-56.72Q410.4-896 480-896q87.89 0 163.94 32Q720-832 776-776t88 132.06q32 76.05 32 163.94 0 69.6-20.28 131.38Q855.43-286.84 819-236ZM594-461l-55-54 121-121 55 54-121 121Zm-67-66Zm-95 95Z"]], template: function ShowProfilesComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "div", 0)(1, "h2");
        \u0275\u0275text(2, "Profiles");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(3, "i", 1);
        \u0275\u0275listener("click", function ShowProfilesComponent_Template_i_click_3_listener() {
          return ctx.profileService.allProfiles.reload();
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(4, "svg", 2);
        \u0275\u0275element(5, "path", 3);
        \u0275\u0275elementEnd()()();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(6, "button", 4);
        \u0275\u0275listener("click", function ShowProfilesComponent_Template_button_click_6_listener() {
          return ctx.openFilterDialog();
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(7, "svg", 5);
        \u0275\u0275element(8, "path", 6);
        \u0275\u0275elementEnd();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(9, "span", 7);
        \u0275\u0275text(10, "Add New");
        \u0275\u0275elementEnd()();
        \u0275\u0275element(11, "hr");
        \u0275\u0275template(12, ShowProfilesComponent_Conditional_12_Template, 1, 0, "app-load-indicator", 8)(13, ShowProfilesComponent_Conditional_13_Template, 2, 1);
      }
      if (rf & 2) {
        \u0275\u0275advance(3);
        \u0275\u0275classProp("loading", ctx.profileService.allProfiles.isLoading());
        \u0275\u0275advance(9);
        \u0275\u0275conditional(ctx.profileService.allProfiles.isLoading() ? 12 : 13);
      }
    }, dependencies: [CommonModule, LoadIndicatorComponent, RouterLink], styles: ["\n\n[_nghost-%COMP%] {\n  height: 100%;\n  width: 100%;\n  display: flex;\n  flex-direction: column;\n  position: relative;\n  gap: 12px;\n}\n.title-block[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  justify-content: flex-start;\n  align-items: center;\n}\n.refresh-icon[_ngcontent-%COMP%] {\n  cursor: pointer;\n  fill: var(--color-on-surface);\n}\n.loading[_ngcontent-%COMP%] {\n  cursor: progress;\n  animation: spin-animation 2s linear infinite;\n}\n.top-right-button[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 0;\n  right: 0;\n  margin: 10px;\n}\n.center[_ngcontent-%COMP%] {\n  margin: auto;\n}\n.profile-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  flex-wrap: wrap;\n  gap: 1rem;\n}\n.profile-card[_ngcontent-%COMP%] {\n  display: grid;\n  grid-template-rows: auto 1fr auto;\n  grid-template-columns: 1fr auto;\n  gap: 10px;\n  max-width: 500px;\n  padding: 12px;\n  border: 2px solid var(--color-outline);\n  border-radius: 8px;\n  background-color: var(--color-surface-container);\n  color: var(--color-on-surface);\n  cursor: pointer;\n}\n@media (max-width: 765px) {\n  .profile-card[_ngcontent-%COMP%] {\n    margin: auto;\n    width: 100%;\n  }\n}\n.profile-card-title[_ngcontent-%COMP%] {\n  grid-row: 1;\n  grid-column: 1/span 2;\n  color: var(--color-primary);\n  text-align: center;\n}\n.profile-card-content[_ngcontent-%COMP%] {\n  grid-row: 2;\n  grid-column: 1;\n  padding: 0 1rem;\n}\n.profile-card-checkbox[_ngcontent-%COMP%] {\n  grid-row: 2;\n  grid-column: 2;\n  width: auto;\n  padding: 0.5rem;\n}\n.profile-card-icon[_ngcontent-%COMP%] {\n  width: 3rem;\n  height: 3rem;\n}\n.success[_ngcontent-%COMP%] {\n  fill: var(--color-success);\n}\n.error[_ngcontent-%COMP%] {\n  fill: var(--color-error);\n}\n/*# sourceMappingURL=show-profiles.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ShowProfilesComponent, [{
    type: Component,
    args: [{ selector: "app-show-profiles", imports: [CommonModule, LoadIndicatorComponent, RouterLink], template: '<div class="title-block">\n  <h2>Profiles</h2>\n  <i\n    class="icononly-button"\n    [class.loading]="profileService.allProfiles.isLoading()"\n    title="Refresh"\n    (click)="profileService.allProfiles.reload()"\n  >\n    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="refresh-icon">\n      <path\n        d="M343-107q-120-42-194.5-146.5T74-490q0-29 4-57.5T91-604l-57 33-37-62 185-107 106 184-63 36-54-92q-13 30-18.5 60.5T147-490q0 113 65.5 200T381-171l-38 64Zm291-516v-73h107q-47-60-115.5-93.5T480-823q-66 0-123.5 24T255-734l-38-65q54-45 121-71t142-26q85 0 160.5 33T774-769v-67h73v213H634ZM598-1 413-107l107-184 62 37-54 94q123-17 204.5-110.5T814-489q0-19-2.5-37.5T805-563h74q4 18 6 36.5t2 36.5q0 142-87 251.5T578-96l56 33-36 62Z"\n      />\n    </svg>\n  </i>\n</div>\n<button class="animated-button top-right-button" (click)="openFilterDialog()">\n  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">\n    <path d="M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z" />\n  </svg>\n  <span class="text">Add New</span>\n</button>\n<hr />\n\n@if (profileService.allProfiles.isLoading()) {\n  <app-load-indicator class="center" />\n} @else {\n  @if (profileService.allProfiles.value() && profileService.allProfiles.value().length > 0) {\n    <div class="profile-container">\n      @for (profile of profileService.allProfiles.value(); track $index) {\n        <div class="profile-card" [routerLink]="[RouteEdit, profile.id]">\n          <h3 class="profile-card-title">{{ profile.customfilter.filter_name }}</h3>\n          <div class="profile-card-content">\n            <p>Video: {{ profile.video_resolution }}p | {{ profile.video_format }}</p>\n            <p>Audio: {{ profile.audio_format }}</p>\n            @if (profile.subtitles_enabled) {\n              <p>Subtitle: {{ profile.subtitles_language }} | {{ profile.subtitles_format }}</p>\n            } @else {\n              <p>Subtitles: No</p>\n            }\n          </div>\n          <div class="profile-card-checkbox center">\n            @if (profile.enabled) {\n              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="profile-card-icon success" title="Profile Enabled">\n                <path\n                  d="m421-288 294-294-55-54-239 239-121-121-54 54 175 176Zm58.54 224q-85.18 0-161.02-33.02t-132.16-89.34q-56.32-56.32-89.34-132.29T64-480q0-86.27 33.08-162.15 33.08-75.88 89.68-132.47 56.61-56.59 132.22-88.99Q394.59-896 479.56-896q86.33 0 162.51 32.39 76.18 32.4 132.56 89Q831-718 863.5-641.96q32.5 76.04 32.5 162.5 0 85.46-32.39 160.8-32.4 75.34-88.99 131.92Q718.03-130.16 642-97.08 565.98-64 479.54-64Zm.46-73q142.51 0 242.76-100.74Q823-338.49 823-480q0-142.51-100.24-242.76Q622.51-823 480-823q-141.51 0-242.26 100.24Q137-622.51 137-480q0 141.51 100.74 242.26Q338.49-137 480-137Zm0-343Z"\n                />\n              </svg>\n            } @else {\n              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="profile-card-icon danger" title="Profile Disabled">\n                <path\n                  d="M836-29 724-141q-52 37-113.57 57Q548.87-64 480-64q-87.64 0-163.98-32.02-76.34-32.02-132.16-87.84-55.82-55.82-87.84-132.16T64-480q0-68.87 20-130.43Q104-672 141-724L15-850l52-52L888-81l-52 52ZM480-137q54.5 0 102.25-14.5T671-193L498-366l-77 78-175-176 49-49 122 120 27-27-251-251q-27 41-41.5 88.75T137-480q0 146 98.5 244.5T480-137Zm339-99-52-52q26-41 41-89.5T823-480q0-146-98.5-244.5T480-823q-54 0-102.5 15T288-767l-52-52q50.84-36.43 112.62-56.72Q410.4-896 480-896q87.89 0 163.94 32Q720-832 776-776t88 132.06q32 76.05 32 163.94 0 69.6-20.28 131.38Q855.43-286.84 819-236ZM594-461l-55-54 121-121 55 54-121 121Zm-67-66Zm-95 95Z"\n                />\n              </svg>\n            }\n          </div>\n        </div>\n      }\n    </div>\n  } @else {\n    <div class="center">\n      <p>No profiles found.</p>\n    </div>\n  }\n}\n', styles: ["/* src/app/settings/profiles/show-profiles/show-profiles.component.scss */\n:host {\n  height: 100%;\n  width: 100%;\n  display: flex;\n  flex-direction: column;\n  position: relative;\n  gap: 12px;\n}\n.title-block {\n  display: flex;\n  flex-direction: row;\n  justify-content: flex-start;\n  align-items: center;\n}\n.refresh-icon {\n  cursor: pointer;\n  fill: var(--color-on-surface);\n}\n.loading {\n  cursor: progress;\n  animation: spin-animation 2s linear infinite;\n}\n.top-right-button {\n  position: absolute;\n  top: 0;\n  right: 0;\n  margin: 10px;\n}\n.center {\n  margin: auto;\n}\n.profile-container {\n  display: flex;\n  flex-direction: row;\n  flex-wrap: wrap;\n  gap: 1rem;\n}\n.profile-card {\n  display: grid;\n  grid-template-rows: auto 1fr auto;\n  grid-template-columns: 1fr auto;\n  gap: 10px;\n  max-width: 500px;\n  padding: 12px;\n  border: 2px solid var(--color-outline);\n  border-radius: 8px;\n  background-color: var(--color-surface-container);\n  color: var(--color-on-surface);\n  cursor: pointer;\n}\n@media (max-width: 765px) {\n  .profile-card {\n    margin: auto;\n    width: 100%;\n  }\n}\n.profile-card-title {\n  grid-row: 1;\n  grid-column: 1/span 2;\n  color: var(--color-primary);\n  text-align: center;\n}\n.profile-card-content {\n  grid-row: 2;\n  grid-column: 1;\n  padding: 0 1rem;\n}\n.profile-card-checkbox {\n  grid-row: 2;\n  grid-column: 2;\n  width: auto;\n  padding: 0.5rem;\n}\n.profile-card-icon {\n  width: 3rem;\n  height: 3rem;\n}\n.success {\n  fill: var(--color-success);\n}\n.error {\n  fill: var(--color-error);\n}\n/*# sourceMappingURL=show-profiles.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(ShowProfilesComponent, { className: "ShowProfilesComponent", filePath: "src/app/settings/profiles/show-profiles/show-profiles.component.ts", lineNumber: 15 });
})();

// src/app/settings/settings.component.ts
var SettingsComponent = class _SettingsComponent {
  constructor() {
    this.RouteAbout = RouteAbout;
    this.RouteConnections = RouteConnections;
    this.RouteProfiles = RouteProfiles;
    this.RouteTrailer = RouteTrailer;
  }
  static {
    this.\u0275fac = function SettingsComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _SettingsComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _SettingsComponent, selectors: [["app-settings"]], decls: 12, vars: 4, consts: [[1, "settingsnav"], ["routerLinkActive", "active", 1, "setnav-btn", 3, "routerLink"], [1, "settings-container"], [1, "settings-content"]], template: function SettingsComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "div", 0)(1, "a", 1);
        \u0275\u0275text(2, "Connections");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(3, "a", 1);
        \u0275\u0275text(4, "Profiles");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(5, "a", 1);
        \u0275\u0275text(6, "Trailer");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(7, "a", 1);
        \u0275\u0275text(8, "About");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(9, "div", 2)(10, "div", 3);
        \u0275\u0275element(11, "router-outlet");
        \u0275\u0275elementEnd()();
      }
      if (rf & 2) {
        \u0275\u0275advance();
        \u0275\u0275property("routerLink", ctx.RouteConnections);
        \u0275\u0275advance(2);
        \u0275\u0275property("routerLink", ctx.RouteProfiles);
        \u0275\u0275advance(2);
        \u0275\u0275property("routerLink", ctx.RouteTrailer);
        \u0275\u0275advance(2);
        \u0275\u0275property("routerLink", ctx.RouteAbout);
      }
    }, dependencies: [RouterLink, RouterLinkActive, RouterOutlet], styles: ["\n\n.settings-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  margin: 1rem;\n}\n@media (width < 765px) {\n  .settings-container[_ngcontent-%COMP%] {\n    margin: 0.5rem;\n  }\n}\n.settingsnav[_ngcontent-%COMP%] {\n  position: sticky;\n  top: 76px;\n  left: 0;\n  right: 0;\n  z-index: 99;\n  margin: 0;\n  padding: 0;\n  display: flex;\n  flex-direction: row;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n}\n@media (width < 765px) {\n  .settingsnav[_ngcontent-%COMP%] {\n    order: 2;\n    justify-content: space-around;\n    position: fixed;\n    top: auto;\n    bottom: 78px;\n  }\n}\n.settingsnav[_ngcontent-%COMP%]    > *[_ngcontent-%COMP%] {\n  flex: 1;\n}\n.settings-content[_ngcontent-%COMP%] {\n  order: 2;\n  padding: 0.5rem;\n}\n@media (width < 765px) {\n  .settings-content[_ngcontent-%COMP%] {\n    margin-bottom: 80px;\n    order: 1;\n  }\n}\n.setnav-btn[_ngcontent-%COMP%] {\n  margin: 0;\n  padding: 0.8rem;\n  box-sizing: border-box;\n  text-decoration: none;\n  color: inherit;\n  text-align: center;\n  font-weight: 400;\n  transition: 0.3s;\n  cursor: pointer;\n  border-radius: 0;\n  border-bottom: 2px solid transparent;\n}\n.setnav-btn.active[_ngcontent-%COMP%] {\n  background-color: var(--color-secondary-container);\n  opacity: 1;\n  font-weight: 600;\n  color: var(--color-on-secondary-container);\n  border-bottom: 2px solid var(--color-primary);\n}\n.setnav-btn[_ngcontent-%COMP%]:not(.active):hover {\n  background-color: var(--color-secondary-container);\n  opacity: 0.6;\n  font-weight: 500;\n  color: var(--color-on-secondary-container);\n  border-bottom: 2px solid var(--color-primary);\n}\n/*# sourceMappingURL=settings.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(SettingsComponent, [{
    type: Component,
    args: [{ selector: "app-settings", imports: [RouterLink, RouterLinkActive, RouterOutlet], template: '<!-- Settings Tabs -->\n\n<div class="settingsnav">\n  <a class="setnav-btn" [routerLink]="RouteConnections" routerLinkActive="active">Connections</a>\n  <a class="setnav-btn" [routerLink]="RouteProfiles" routerLinkActive="active">Profiles</a>\n  <a class="setnav-btn" [routerLink]="RouteTrailer" routerLinkActive="active">Trailer</a>\n  <a class="setnav-btn" [routerLink]="RouteAbout" routerLinkActive="active">About</a>\n</div>\n<div class="settings-container">\n  <div class="settings-content">\n    <router-outlet />\n  </div>\n</div>\n', styles: ["/* src/app/settings/settings.component.scss */\n.settings-container {\n  display: flex;\n  flex-direction: column;\n  margin: 1rem;\n}\n@media (width < 765px) {\n  .settings-container {\n    margin: 0.5rem;\n  }\n}\n.settingsnav {\n  position: sticky;\n  top: 76px;\n  left: 0;\n  right: 0;\n  z-index: 99;\n  margin: 0;\n  padding: 0;\n  display: flex;\n  flex-direction: row;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface);\n}\n@media (width < 765px) {\n  .settingsnav {\n    order: 2;\n    justify-content: space-around;\n    position: fixed;\n    top: auto;\n    bottom: 78px;\n  }\n}\n.settingsnav > * {\n  flex: 1;\n}\n.settings-content {\n  order: 2;\n  padding: 0.5rem;\n}\n@media (width < 765px) {\n  .settings-content {\n    margin-bottom: 80px;\n    order: 1;\n  }\n}\n.setnav-btn {\n  margin: 0;\n  padding: 0.8rem;\n  box-sizing: border-box;\n  text-decoration: none;\n  color: inherit;\n  text-align: center;\n  font-weight: 400;\n  transition: 0.3s;\n  cursor: pointer;\n  border-radius: 0;\n  border-bottom: 2px solid transparent;\n}\n.setnav-btn.active {\n  background-color: var(--color-secondary-container);\n  opacity: 1;\n  font-weight: 600;\n  color: var(--color-on-secondary-container);\n  border-bottom: 2px solid var(--color-primary);\n}\n.setnav-btn:not(.active):hover {\n  background-color: var(--color-secondary-container);\n  opacity: 0.6;\n  font-weight: 500;\n  color: var(--color-on-secondary-container);\n  border-bottom: 2px solid var(--color-primary);\n}\n/*# sourceMappingURL=settings.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(SettingsComponent, { className: "SettingsComponent", filePath: "src/app/settings/settings.component.ts", lineNumber: 12 });
})();

// src/app/settings/trailer/trailer.component.ts
function TrailerComponent_div_4_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 14);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const message_r1 = ctx.$implicit;
    \u0275\u0275classProp("error", message_r1.toLowerCase().includes("error"));
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", message_r1, " ");
  }
}
function TrailerComponent_Conditional_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 2);
  }
}
function TrailerComponent_Conditional_6_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 3)(1, "strong");
    \u0275\u0275text(2, "Warning:");
    \u0275\u0275elementEnd();
    \u0275\u0275text(3, " Log Level set to 'Debug', this will generate too many logs, change it if not needed! ");
    \u0275\u0275elementEnd();
  }
}
function TrailerComponent_Conditional_38_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "app-options-setting", 15);
    \u0275\u0275listener("optionChange", function TrailerComponent_Conditional_38_Template_app_options_setting_optionChange_0_listener($event) {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.updateSetting("trailer_hardware_acceleration", $event));
    });
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    let tmp_2_0;
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275property("options", ctx_r2.trueFalseOptions)("selectedOption", (tmp_2_0 = ctx_r2.settings()) == null ? null : tmp_2_0.trailer_hardware_acceleration);
  }
}
var TrailerComponent = class _TrailerComponent {
  constructor() {
    this.settingsService = inject(SettingsService);
    this.webSocketService = inject(WebsocketService);
    this.isLoading = this.settingsService.settingsResource.isLoading;
    this.settings = this.settingsService.settingsResource.value;
    this.updateResults = [];
    this.loggingOptions = ["Debug", "Info", "Warning", "Error"];
    this.trueFalseOptions = ["true", "false"];
  }
  toTitleCase(str) {
    return str.split("_").map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(" ");
  }
  updateSetting(key, value) {
    this.settingsService.updateSetting(key, value).subscribe((msg) => {
      const status = msg.toLowerCase().includes("error") ? "Error" : "Success";
      this.webSocketService.showToast(msg, status);
      this.settingsService.settingsResource.reload();
    });
  }
  static {
    this.\u0275fac = function TrailerComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _TrailerComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _TrailerComponent, selectors: [["app-trailer"]], decls: 41, vars: 28, consts: [[1, "message-container"], ["class", "update-message", 3, "error", 4, "ngFor", "ngForOf"], [1, "center"], [1, "update-message", "error"], ["open", ""], [1, "setting-group"], ["name", "Monitor Enabled", "description", "Monitor media from Radarr/Sonarr to download trailers.", 3, "optionChange", "options", "selectedOption"], ["name", "Monitor Interval", "description", "Frequency (in minutes) to get new media data from Radarr/Sonarr.", "descriptionExtra", "Default is 60. Minuimum is 10. Container restart required to apply new interval.", "placeholder", "Monitor Interval", "autocomplete", "off", 3, "onSubmit", "isNumberType", "isLongInput", "minLength", "maxLength", "value", "disabled"], ["name", "Wait for Media", "description", "Wait for media to be imported into Radarr/Sonarr before downloading trailers.", 3, "optionChange", "options", "selectedOption"], ["name", "Log Level", "description", "Set logging level for the app.", 3, "optionChange", "options", "selectedOption"], ["name", "Yt-dlp Cookies Path", "description", "Path to yt-dlp cookies file to use for downloading trailers.", "placeholder", "/config/cookies.txt", "autocomplete", "off", 3, "onSubmit", "isNumberType", "isLongInput", "minLength", "maxLength", "value"], ["name", "Nvidia GPU Acceleration", "description", "Use Nvidia GPU for hardware acceleration.", 3, "options", "selectedOption"], ["name", "Update Yt-dlp", "description", "Update yt-dlp to latest version during container startup.", "descriptionExtra", "You need to restart the container to apply updates.", 3, "optionChange", "options", "selectedOption"], ["name", "URL Base", "description", "URL Base for use with reverse proxy configuration", "descriptionExtra", "Restart required to take effect!", "placeholder", "trailarr", "autocomplete", "off", 3, "onSubmit", "isNumberType", "isLongInput", "minLength", "maxLength", "value"], [1, "update-message"], ["name", "Nvidia GPU Acceleration", "description", "Use Nvidia GPU for hardware acceleration.", 3, "optionChange", "options", "selectedOption"]], template: function TrailerComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "h2");
        \u0275\u0275text(1, "General Settings");
        \u0275\u0275elementEnd();
        \u0275\u0275element(2, "hr");
        \u0275\u0275elementStart(3, "div", 0);
        \u0275\u0275template(4, TrailerComponent_div_4_Template, 2, 3, "div", 1);
        \u0275\u0275elementEnd();
        \u0275\u0275template(5, TrailerComponent_Conditional_5_Template, 1, 0, "app-load-indicator", 2)(6, TrailerComponent_Conditional_6_Template, 4, 0, "div", 3);
        \u0275\u0275elementStart(7, "section")(8, "details", 4)(9, "summary");
        \u0275\u0275text(10, "General");
        \u0275\u0275elementEnd();
        \u0275\u0275element(11, "hr");
        \u0275\u0275elementStart(12, "div", 5)(13, "app-options-setting", 6);
        \u0275\u0275listener("optionChange", function TrailerComponent_Template_app_options_setting_optionChange_13_listener($event) {
          return ctx.updateSetting("monitor_enabled", $event);
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(14, "app-text-setting", 7);
        \u0275\u0275listener("onSubmit", function TrailerComponent_Template_app_text_setting_onSubmit_14_listener($event) {
          return ctx.updateSetting("monitor_interval", $event);
        });
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(15, "section")(16, "details", 4)(17, "summary");
        \u0275\u0275text(18, "Files");
        \u0275\u0275elementEnd();
        \u0275\u0275element(19, "hr");
        \u0275\u0275elementStart(20, "div", 5)(21, "app-options-setting", 8);
        \u0275\u0275listener("optionChange", function TrailerComponent_Template_app_options_setting_optionChange_21_listener($event) {
          return ctx.updateSetting("wait_for_media", $event);
        });
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(22, "section")(23, "details", 4)(24, "summary");
        \u0275\u0275text(25, "Advanced Options");
        \u0275\u0275elementEnd();
        \u0275\u0275element(26, "hr");
        \u0275\u0275elementStart(27, "div", 5)(28, "app-options-setting", 9);
        \u0275\u0275listener("optionChange", function TrailerComponent_Template_app_options_setting_optionChange_28_listener($event) {
          return ctx.updateSetting("log_level", $event);
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(29, "app-text-setting", 10);
        \u0275\u0275listener("onSubmit", function TrailerComponent_Template_app_text_setting_onSubmit_29_listener($event) {
          return ctx.updateSetting("yt_cookies_path", $event);
        });
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(30, "section")(31, "details", 4)(32, "summary");
        \u0275\u0275text(33, "Experimental Options");
        \u0275\u0275elementEnd();
        \u0275\u0275element(34, "hr");
        \u0275\u0275elementStart(35, "div", 5)(36, "p");
        \u0275\u0275text(37, "These are experimental options, might not work as expected!");
        \u0275\u0275elementEnd();
        \u0275\u0275template(38, TrailerComponent_Conditional_38_Template, 1, 2, "app-options-setting", 11);
        \u0275\u0275elementStart(39, "app-options-setting", 12);
        \u0275\u0275listener("optionChange", function TrailerComponent_Template_app_options_setting_optionChange_39_listener($event) {
          return ctx.updateSetting("update_ytdlp", $event);
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(40, "app-text-setting", 13);
        \u0275\u0275listener("onSubmit", function TrailerComponent_Template_app_text_setting_onSubmit_40_listener($event) {
          return ctx.updateSetting("url_base", $event);
        });
        \u0275\u0275elementEnd()()()();
      }
      if (rf & 2) {
        let tmp_2_0;
        let tmp_4_0;
        let tmp_9_0;
        let tmp_12_0;
        let tmp_14_0;
        let tmp_19_0;
        let tmp_20_0;
        let tmp_22_0;
        let tmp_27_0;
        \u0275\u0275advance(4);
        \u0275\u0275property("ngForOf", ctx.updateResults);
        \u0275\u0275advance();
        \u0275\u0275conditional(ctx.isLoading() ? 5 : -1);
        \u0275\u0275advance();
        \u0275\u0275conditional(((tmp_2_0 = ctx.settings()) == null ? null : tmp_2_0.log_level) == "DEBUG" ? 6 : -1);
        \u0275\u0275advance(7);
        \u0275\u0275property("options", ctx.trueFalseOptions)("selectedOption", (tmp_4_0 = ctx.settings()) == null ? null : tmp_4_0.monitor_enabled);
        \u0275\u0275advance();
        \u0275\u0275property("isNumberType", true)("isLongInput", false)("minLength", 1)("maxLength", 6)("value", (tmp_9_0 = (tmp_9_0 = ctx.settings()) == null ? null : tmp_9_0.monitor_interval) !== null && tmp_9_0 !== void 0 ? tmp_9_0 : 60)("disabled", false);
        \u0275\u0275advance(7);
        \u0275\u0275property("options", ctx.trueFalseOptions)("selectedOption", (tmp_12_0 = ctx.settings()) == null ? null : tmp_12_0.wait_for_media);
        \u0275\u0275advance(7);
        \u0275\u0275property("options", ctx.loggingOptions)("selectedOption", ctx.toTitleCase((tmp_14_0 = (tmp_14_0 = ctx.settings()) == null ? null : tmp_14_0.log_level) !== null && tmp_14_0 !== void 0 ? tmp_14_0 : "INFO"));
        \u0275\u0275advance();
        \u0275\u0275property("isNumberType", false)("isLongInput", true)("minLength", 0)("maxLength", 255)("value", (tmp_19_0 = (tmp_19_0 = ctx.settings()) == null ? null : tmp_19_0.yt_cookies_path) !== null && tmp_19_0 !== void 0 ? tmp_19_0 : "");
        \u0275\u0275advance(9);
        \u0275\u0275conditional(((tmp_20_0 = ctx.settings()) == null ? null : tmp_20_0.nvidia_gpu_available) ? 38 : -1);
        \u0275\u0275advance();
        \u0275\u0275property("options", ctx.trueFalseOptions)("selectedOption", (tmp_22_0 = ctx.settings()) == null ? null : tmp_22_0.update_ytdlp);
        \u0275\u0275advance();
        \u0275\u0275property("isNumberType", false)("isLongInput", true)("minLength", 0)("maxLength", 255)("value", (tmp_27_0 = (tmp_27_0 = ctx.settings()) == null ? null : tmp_27_0.url_base) !== null && tmp_27_0 !== void 0 ? tmp_27_0 : "");
      }
    }, dependencies: [NgForOf, FormsModule, LoadIndicatorComponent, OptionsSettingComponent, TextSettingComponent], styles: ["\n\n[_nghost-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  gap: 12px;\n}\n.center[_ngcontent-%COMP%] {\n  position: fixed;\n  inset: 50vh 50vw;\n  transform: translate(-50%, -50%);\n  align-self: center;\n  justify-self: center;\n  margin: auto;\n}\n.message-container[_ngcontent-%COMP%] {\n  width: 100%;\n  display: flex;\n  flex-direction: column;\n  align-items: center;\n  gap: 1rem;\n  position: fixed;\n  top: 5rem;\n  right: 3rem;\n  z-index: 999;\n  max-width: 25%;\n}\n@media (width < 768px) {\n  .message-container[_ngcontent-%COMP%] {\n    max-width: 80%;\n    right: 1rem;\n  }\n}\n.update-message[_ngcontent-%COMP%] {\n  width: 100%;\n  display: flex;\n  justify-content: center;\n  align-items: center;\n  padding: 0.5rem;\n  border-radius: 0.5rem;\n  font-weight: bold;\n  color: var(--color-success-text);\n  background-color: var(--color-success);\n  animation: slideInDown 0.3s ease-out forwards;\n}\n.error[_ngcontent-%COMP%] {\n  color: var(--color-warning-text);\n  background-color: var(--color-warning);\n}\ndetails[_ngcontent-%COMP%] {\n  margin: 0.5rem 0;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  background-color: var(--color-surface-container);\n}\nsummary[_ngcontent-%COMP%] {\n  padding: 1rem;\n  font-weight: bold;\n  cursor: pointer;\n  color: var(--color-primary);\n  white-space: nowrap;\n  overflow: hidden;\n  text-overflow: ellipsis;\n  max-width: calc(100vw - 260px);\n}\n@media (width < 1100px) {\n  summary[_ngcontent-%COMP%] {\n    max-width: calc(100vw - 100px);\n  }\n}\n@media (width < 765px) {\n  summary[_ngcontent-%COMP%] {\n    max-width: calc(100vw - 50px);\n  }\n}\n.setting-group[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  margin: 0 0.5rem;\n  container-type: inline-size;\n}\n/*# sourceMappingURL=trailer.component.css.map */"], changeDetection: 0 });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(TrailerComponent, [{
    type: Component,
    args: [{ selector: "app-trailer", imports: [NgForOf, FormsModule, LoadIndicatorComponent, OptionsSettingComponent, TextSettingComponent], changeDetection: ChangeDetectionStrategy.OnPush, template: `<h2>General Settings</h2>
<hr />
<div class="message-container">
  <div *ngFor="let message of updateResults" class="update-message" [class.error]="message.toLowerCase().includes('error')">
    {{ message }}
  </div>
</div>
@if (isLoading()) {
  <app-load-indicator class="center" />
}
@if (settings()?.log_level == 'DEBUG') {
  <div class="update-message error">
    <strong>Warning:</strong> Log Level set to 'Debug', this will generate too many logs, change it if not needed!
  </div>
}
<section>
  <details open>
    <summary>General</summary>
    <hr />
    <div class="setting-group">
      <app-options-setting
        name="Monitor Enabled"
        description="Monitor media from Radarr/Sonarr to download trailers."
        [options]="trueFalseOptions"
        [selectedOption]="settings()?.monitor_enabled"
        (optionChange)="updateSetting('monitor_enabled', $event)"
      />
      <app-text-setting
        name="Monitor Interval"
        description="Frequency (in minutes) to get new media data from Radarr/Sonarr."
        descriptionExtra="Default is 60. Minuimum is 10. Container restart required to apply new interval."
        [isNumberType]="true"
        [isLongInput]="false"
        placeholder="Monitor Interval"
        autocomplete="off"
        [minLength]="1"
        [maxLength]="6"
        [value]="settings()?.monitor_interval ?? 60"
        [disabled]="false"
        (onSubmit)="updateSetting('monitor_interval', $event)"
      />
    </div>
  </details>
</section>
<section>
  <details open>
    <summary>Files</summary>
    <hr />
    <div class="setting-group">
      <app-options-setting
        name="Wait for Media"
        description="Wait for media to be imported into Radarr/Sonarr before downloading trailers."
        [options]="trueFalseOptions"
        [selectedOption]="settings()?.wait_for_media"
        (optionChange)="updateSetting('wait_for_media', $event)"
      />
    </div>
  </details>
</section>
<section>
  <details open>
    <summary>Advanced Options</summary>
    <hr />
    <div class="setting-group">
      <app-options-setting
        name="Log Level"
        description="Set logging level for the app."
        [options]="loggingOptions"
        [selectedOption]="toTitleCase(settings()?.log_level ?? 'INFO')"
        (optionChange)="updateSetting('log_level', $event)"
      />
      <app-text-setting
        name="Yt-dlp Cookies Path"
        description="Path to yt-dlp cookies file to use for downloading trailers."
        [isNumberType]="false"
        [isLongInput]="true"
        placeholder="/config/cookies.txt"
        autocomplete="off"
        [minLength]="0"
        [maxLength]="255"
        [value]="settings()?.yt_cookies_path ?? ''"
        (onSubmit)="updateSetting('yt_cookies_path', $event)"
      />
    </div>
  </details>
</section>
<section>
  <details open>
    <summary>Experimental Options</summary>
    <hr />
    <div class="setting-group">
      <p>These are experimental options, might not work as expected!</p>
      @if (settings()?.nvidia_gpu_available) {
        <app-options-setting
          name="Nvidia GPU Acceleration"
          description="Use Nvidia GPU for hardware acceleration."
          [options]="trueFalseOptions"
          [selectedOption]="settings()?.trailer_hardware_acceleration"
          (optionChange)="updateSetting('trailer_hardware_acceleration', $event)"
        />
      }
      <app-options-setting
        name="Update Yt-dlp"
        description="Update yt-dlp to latest version during container startup."
        descriptionExtra="You need to restart the container to apply updates."
        [options]="trueFalseOptions"
        [selectedOption]="settings()?.update_ytdlp"
        (optionChange)="updateSetting('update_ytdlp', $event)"
      />
      <app-text-setting
        name="URL Base"
        description="URL Base for use with reverse proxy configuration"
        descriptionExtra="Restart required to take effect!"
        [isNumberType]="false"
        [isLongInput]="true"
        placeholder="trailarr"
        autocomplete="off"
        [minLength]="0"
        [maxLength]="255"
        [value]="settings()?.url_base ?? ''"
        (onSubmit)="updateSetting('url_base', $event)"
      />
    </div>
  </details>
</section>
<!-- } -->
`, styles: ["/* src/app/settings/trailer/trailer.component.scss */\n:host {\n  display: flex;\n  flex-direction: column;\n  gap: 12px;\n}\n.center {\n  position: fixed;\n  inset: 50vh 50vw;\n  transform: translate(-50%, -50%);\n  align-self: center;\n  justify-self: center;\n  margin: auto;\n}\n.message-container {\n  width: 100%;\n  display: flex;\n  flex-direction: column;\n  align-items: center;\n  gap: 1rem;\n  position: fixed;\n  top: 5rem;\n  right: 3rem;\n  z-index: 999;\n  max-width: 25%;\n}\n@media (width < 768px) {\n  .message-container {\n    max-width: 80%;\n    right: 1rem;\n  }\n}\n.update-message {\n  width: 100%;\n  display: flex;\n  justify-content: center;\n  align-items: center;\n  padding: 0.5rem;\n  border-radius: 0.5rem;\n  font-weight: bold;\n  color: var(--color-success-text);\n  background-color: var(--color-success);\n  animation: slideInDown 0.3s ease-out forwards;\n}\n.error {\n  color: var(--color-warning-text);\n  background-color: var(--color-warning);\n}\ndetails {\n  margin: 0.5rem 0;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  background-color: var(--color-surface-container);\n}\nsummary {\n  padding: 1rem;\n  font-weight: bold;\n  cursor: pointer;\n  color: var(--color-primary);\n  white-space: nowrap;\n  overflow: hidden;\n  text-overflow: ellipsis;\n  max-width: calc(100vw - 260px);\n}\n@media (width < 1100px) {\n  summary {\n    max-width: calc(100vw - 100px);\n  }\n}\n@media (width < 765px) {\n  summary {\n    max-width: calc(100vw - 50px);\n  }\n}\n.setting-group {\n  display: flex;\n  flex-direction: column;\n  margin: 0 0.5rem;\n  container-type: inline-size;\n}\n/*# sourceMappingURL=trailer.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(TrailerComponent, { className: "TrailerComponent", filePath: "src/app/settings/trailer/trailer.component.ts", lineNumber: 18 });
})();

// src/app/settings/routes.ts
var routes_default = [
  {
    path: "",
    loadComponent: () => SettingsComponent,
    children: [
      { path: RouteConnections, component: ShowConnectionsComponent },
      { path: `${RouteConnections}/${RouteAdd}`, component: AddConnectionComponent },
      { path: `${RouteConnections}/${RouteEdit}/:${RouteParamConnectionId}`, component: EditConnectionComponent },
      { path: RouteProfiles, component: ShowProfilesComponent },
      { path: `${RouteProfiles}/${RouteEdit}/:${RouteParamProfileId}`, component: EditProfileComponent },
      { path: RouteTrailer, component: TrailerComponent },
      { path: RouteAbout, component: AboutComponent },
      { path: "**", redirectTo: RouteTrailer, pathMatch: "prefix" }
    ]
  }
];
export {
  routes_default as default
};
//# sourceMappingURL=chunk-GOLNWYFZ.js.map
