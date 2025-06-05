import {
  DefaultValueAccessor,
  FormArrayName,
  FormBuilder,
  FormControlName,
  FormGroupDirective,
  FormGroupName,
  FormsModule,
  MaxLengthValidator,
  NgControlStatus,
  NgControlStatusGroup,
  NgSelectOption,
  NumberValueAccessor,
  ReactiveFormsModule,
  SelectControlValueAccessor,
  Validators,
  ɵNgNoValidate,
  ɵNgSelectMultipleOption
} from "./chunk-BOQEVO5H.js";
import {
  LoadIndicatorComponent
} from "./chunk-7SOVNULQ.js";
import {
  Component,
  EventEmitter,
  HttpClient,
  Injectable,
  Output,
  computed,
  effect,
  environment,
  inject,
  input,
  setClassMetadata,
  viewChild,
  ɵsetClassDebugInfo,
  ɵɵadvance,
  ɵɵconditional,
  ɵɵdefineComponent,
  ɵɵdefineInjectable,
  ɵɵelement,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵgetCurrentView,
  ɵɵlistener,
  ɵɵnamespaceSVG,
  ɵɵnextContext,
  ɵɵproperty,
  ɵɵpropertyInterpolate1,
  ɵɵqueryAdvance,
  ɵɵrepeater,
  ɵɵrepeaterCreate,
  ɵɵrepeaterTrackByIdentity,
  ɵɵresetView,
  ɵɵrestoreView,
  ɵɵtemplate,
  ɵɵtext,
  ɵɵtextInterpolate1,
  ɵɵviewQuerySignal
} from "./chunk-FAGZ4ZSE.js";

// src/app/models/customfilter.ts
var BooleanFilterCondition;
(function(BooleanFilterCondition2) {
  BooleanFilterCondition2["EQUALS"] = "EQUALS";
})(BooleanFilterCondition || (BooleanFilterCondition = {}));
var DateFilterCondition;
(function(DateFilterCondition2) {
  DateFilterCondition2["IS_AFTER"] = "IS_AFTER";
  DateFilterCondition2["IS_BEFORE"] = "IS_BEFORE";
  DateFilterCondition2["IN_THE_LAST"] = "IN_THE_LAST";
  DateFilterCondition2["NOT_IN_THE_LAST"] = "NOT_IN_THE_LAST";
  DateFilterCondition2["EQUALS"] = "EQUALS";
  DateFilterCondition2["NOT_EQUALS"] = "NOT_EQUALS";
})(DateFilterCondition || (DateFilterCondition = {}));
var NumberFilterCondition;
(function(NumberFilterCondition2) {
  NumberFilterCondition2["GREATER_THAN"] = "GREATER_THAN";
  NumberFilterCondition2["GREATER_THAN_EQUAL"] = "GREATER_THAN_EQUAL";
  NumberFilterCondition2["LESS_THAN"] = "LESS_THAN";
  NumberFilterCondition2["LESS_THAN_EQUAL"] = "LESS_THAN_EQUAL";
  NumberFilterCondition2["EQUALS"] = "EQUALS";
  NumberFilterCondition2["NOT_EQUALS"] = "NOT_EQUALS";
})(NumberFilterCondition || (NumberFilterCondition = {}));
var StringFilterCondition;
(function(StringFilterCondition2) {
  StringFilterCondition2["CONTAINS"] = "CONTAINS";
  StringFilterCondition2["NOT_CONTAINS"] = "NOT_CONTAINS";
  StringFilterCondition2["EQUALS"] = "EQUALS";
  StringFilterCondition2["NOT_EQUALS"] = "NOT_EQUALS";
  StringFilterCondition2["STARTS_WITH"] = "STARTS_WITH";
  StringFilterCondition2["NOT_STARTS_WITH"] = "NOT_STARTS_WITH";
  StringFilterCondition2["ENDS_WITH"] = "ENDS_WITH";
  StringFilterCondition2["NOT_ENDS_WITH"] = "NOT_ENDS_WITH";
  StringFilterCondition2["IS_EMPTY"] = "IS_EMPTY";
  StringFilterCondition2["IS_NOT_EMPTY"] = "IS_NOT_EMPTY";
})(StringFilterCondition || (StringFilterCondition = {}));
var booleanFilterKeys = ["arr_monitored", "is_movie", "media_exists", "monitor", "trailer_exists"];
var dateFilterKeys = ["added_at", "downloaded_at", "updated_at"];
var numberFilterKeys = ["arr_id", "connection_id", "id", "runtime", "year"];
var stringFilterKeys = [
  "clean_title",
  "folder_path",
  "imdb_id",
  "language",
  "media_filename",
  "overview",
  "status",
  "studio",
  "title",
  "title_slug",
  "txdb_id",
  "youtube_trailer_id"
];
var FilterType;
(function(FilterType2) {
  FilterType2["HOME"] = "HOME";
  FilterType2["MOVIES"] = "MOVIES";
  FilterType2["SERIES"] = "SERIES";
  FilterType2["TRAILER"] = "TRAILER";
})(FilterType || (FilterType = {}));

// src/app/services/customfilter.service.ts
var CustomfilterService = class _CustomfilterService {
  constructor() {
    this.httpClient = inject(HttpClient);
    this.cf_url = environment.apiUrl + environment.customfilters;
  }
  create(customFilter) {
    if (customFilter.filter_type === FilterType.TRAILER) {
      const profileUrl = environment.apiUrl + environment.profiles;
      const profileCreate = {
        customfilter: customFilter
      };
      return this.httpClient.post(profileUrl, profileCreate);
    }
    return this.httpClient.post(this.cf_url, customFilter);
  }
  update(customFilter) {
    const url = this.cf_url + customFilter.id;
    return this.httpClient.put(url, customFilter);
  }
  delete(id) {
    const url = this.cf_url + id;
    return this.httpClient.delete(url);
  }
  getViewFilters(moviesOnly) {
    const view = moviesOnly == null ? "home" : moviesOnly ? "movie" : "series";
    const url = this.cf_url + view;
    return this.httpClient.get(url);
  }
  static {
    this.\u0275fac = function CustomfilterService_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _CustomfilterService)();
    };
  }
  static {
    this.\u0275prov = /* @__PURE__ */ \u0275\u0275defineInjectable({ token: _CustomfilterService, factory: _CustomfilterService.\u0275fac, providedIn: "root" });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(CustomfilterService, [{
    type: Injectable,
    args: [{
      providedIn: "root"
    }]
  }], null, null);
})();

// src/app/media/add-filter-dialog/add-filter-dialog.component.ts
var _c0 = ["customFilterDialog"];
function AddCustomFilterDialogComponent_Conditional_2_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 1);
  }
}
function AddCustomFilterDialogComponent_Conditional_3_For_7_For_6_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "option", 16);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const filter_r5 = ctx.$implicit;
    const ctx_r1 = \u0275\u0275nextContext(3);
    \u0275\u0275property("value", filter_r5);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", ctx_r1.displayTitle(filter_r5), " ");
  }
}
function AddCustomFilterDialogComponent_Conditional_3_For_7_For_12_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "option", 16);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const condition_r6 = ctx.$implicit;
    const ctx_r1 = \u0275\u0275nextContext(3);
    \u0275\u0275property("value", condition_r6);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", ctx_r1.displayTitle(condition_r6), " ");
  }
}
function AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_14_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "input", 18);
  }
  if (rf & 2) {
    const \u0275$index_18_r4 = \u0275\u0275nextContext().$index;
    \u0275\u0275propertyInterpolate1("id", "filter_value_", \u0275$index_18_r4, "");
  }
}
function AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_15_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "input", 19);
  }
  if (rf & 2) {
    const \u0275$index_18_r4 = \u0275\u0275nextContext().$index;
    \u0275\u0275propertyInterpolate1("id", "filter_value_", \u0275$index_18_r4, "");
  }
}
function AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_16_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "input", 25);
    \u0275\u0275elementStart(1, "span");
    \u0275\u0275text(2, " days");
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const \u0275$index_18_r4 = \u0275\u0275nextContext().$index;
    \u0275\u0275propertyInterpolate1("id", "filter_value_", \u0275$index_18_r4, "");
  }
}
function AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_17_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "input", 20);
  }
  if (rf & 2) {
    const \u0275$index_18_r4 = \u0275\u0275nextContext().$index;
    \u0275\u0275propertyInterpolate1("id", "filter_value_", \u0275$index_18_r4, "");
  }
}
function AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_18_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "select", 21)(1, "option", 26);
    \u0275\u0275text(2, "True");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "option", 27);
    \u0275\u0275text(4, "False");
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const \u0275$index_18_r4 = \u0275\u0275nextContext().$index;
    \u0275\u0275propertyInterpolate1("id", "filter_value_", \u0275$index_18_r4, "");
  }
}
function AddCustomFilterDialogComponent_Conditional_3_For_7_Template(rf, ctx) {
  if (rf & 1) {
    const _r3 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 8)(1, "div", 4)(2, "select", 14);
    \u0275\u0275listener("change", function AddCustomFilterDialogComponent_Conditional_3_For_7_Template_select_change_2_listener($event) {
      const \u0275$index_18_r4 = \u0275\u0275restoreView(_r3).$index;
      const ctx_r1 = \u0275\u0275nextContext(2);
      return \u0275\u0275resetView(ctx_r1.onFilterByChange($event, \u0275$index_18_r4));
    });
    \u0275\u0275elementStart(3, "option", 15);
    \u0275\u0275text(4, "Select Filter By");
    \u0275\u0275elementEnd();
    \u0275\u0275repeaterCreate(5, AddCustomFilterDialogComponent_Conditional_3_For_7_For_6_Template, 2, 2, "option", 16, \u0275\u0275repeaterTrackByIdentity);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(7, "div", 4)(8, "select", 17);
    \u0275\u0275listener("change", function AddCustomFilterDialogComponent_Conditional_3_For_7_Template_select_change_8_listener($event) {
      const \u0275$index_18_r4 = \u0275\u0275restoreView(_r3).$index;
      const ctx_r1 = \u0275\u0275nextContext(2);
      return \u0275\u0275resetView(ctx_r1.onFilterConditionChange($event, \u0275$index_18_r4));
    });
    \u0275\u0275elementStart(9, "option", 15);
    \u0275\u0275text(10, "Select Condition");
    \u0275\u0275elementEnd();
    \u0275\u0275repeaterCreate(11, AddCustomFilterDialogComponent_Conditional_3_For_7_For_12_Template, 2, 2, "option", 16, \u0275\u0275repeaterTrackByIdentity);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(13, "div", 4);
    \u0275\u0275template(14, AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_14_Template, 1, 2, "input", 18)(15, AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_15_Template, 1, 2, "input", 19)(16, AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_16_Template, 3, 2)(17, AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_17_Template, 1, 2, "input", 20)(18, AddCustomFilterDialogComponent_Conditional_3_For_7_Conditional_18_Template, 5, 2, "select", 21);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(19, "button", 22);
    \u0275\u0275listener("click", function AddCustomFilterDialogComponent_Conditional_3_For_7_Template_button_click_19_listener() {
      const \u0275$index_18_r4 = \u0275\u0275restoreView(_r3).$index;
      const ctx_r1 = \u0275\u0275nextContext(2);
      return \u0275\u0275resetView(ctx_r1.removeFilter(\u0275$index_18_r4));
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(20, "svg", 23);
    \u0275\u0275element(21, "path", 24);
    \u0275\u0275elementEnd()()();
  }
  if (rf & 2) {
    const \u0275$index_18_r4 = ctx.$index;
    const ctx_r1 = \u0275\u0275nextContext(2);
    \u0275\u0275property("formGroupName", \u0275$index_18_r4);
    \u0275\u0275advance(2);
    \u0275\u0275propertyInterpolate1("id", "filter_by_", \u0275$index_18_r4, "");
    \u0275\u0275advance(3);
    \u0275\u0275repeater(ctx_r1.filterKeys);
    \u0275\u0275advance(3);
    \u0275\u0275propertyInterpolate1("id", "filter_condition_", \u0275$index_18_r4, "");
    \u0275\u0275advance(3);
    \u0275\u0275repeater(ctx_r1.filterConditions[\u0275$index_18_r4]);
    \u0275\u0275advance(3);
    \u0275\u0275conditional(ctx_r1.filterValueTypes[\u0275$index_18_r4] === "string" ? 14 : ctx_r1.filterValueTypes[\u0275$index_18_r4] === "number" ? 15 : ctx_r1.filterValueTypes[\u0275$index_18_r4] === "number_days" ? 16 : ctx_r1.filterValueTypes[\u0275$index_18_r4] === "date" ? 17 : ctx_r1.filterValueTypes[\u0275$index_18_r4] === "boolean" ? 18 : -1);
  }
}
function AddCustomFilterDialogComponent_Conditional_3_Conditional_13_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "button", 12);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext(2);
    \u0275\u0275property("disabled", ctx_r1.customFilterForm.pristine || ctx_r1.customFilterForm.invalid || ctx_r1.submitting);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", ctx_r1.customFilter() ? "Update" : "Create", " ");
  }
}
function AddCustomFilterDialogComponent_Conditional_3_Conditional_14_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 13);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 28)(2, "circle", 29);
    \u0275\u0275element(3, "animate", 30);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(4, "circle", 31);
    \u0275\u0275element(5, "animate", 32);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(6, "circle", 33);
    \u0275\u0275element(7, "animate", 34);
    \u0275\u0275elementEnd()()();
  }
}
function AddCustomFilterDialogComponent_Conditional_3_Template(rf, ctx) {
  if (rf & 1) {
    const _r1 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "form", 3);
    \u0275\u0275listener("ngSubmit", function AddCustomFilterDialogComponent_Conditional_3_Template_form_ngSubmit_0_listener() {
      \u0275\u0275restoreView(_r1);
      const ctx_r1 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r1.onSubmit());
    })("click", function AddCustomFilterDialogComponent_Conditional_3_Template_form_click_0_listener($event) {
      \u0275\u0275restoreView(_r1);
      return \u0275\u0275resetView($event.stopPropagation());
    });
    \u0275\u0275elementStart(1, "div", 4)(2, "label", 5);
    \u0275\u0275text(3, "Label");
    \u0275\u0275elementEnd();
    \u0275\u0275element(4, "input", 6);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(5, "div", 7);
    \u0275\u0275repeaterCreate(6, AddCustomFilterDialogComponent_Conditional_3_For_7_Template, 22, 6, "div", 8, \u0275\u0275repeaterTrackByIdentity);
    \u0275\u0275elementStart(8, "button", 9);
    \u0275\u0275listener("click", function AddCustomFilterDialogComponent_Conditional_3_Template_button_click_8_listener() {
      \u0275\u0275restoreView(_r1);
      const ctx_r1 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r1.addFilter());
    });
    \u0275\u0275text(9, "Add Filter");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(10, "div", 10)(11, "button", 11);
    \u0275\u0275listener("click", function AddCustomFilterDialogComponent_Conditional_3_Template_button_click_11_listener() {
      \u0275\u0275restoreView(_r1);
      const ctx_r1 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r1.closeDialog(-1));
    });
    \u0275\u0275text(12, "Cancel");
    \u0275\u0275elementEnd();
    \u0275\u0275template(13, AddCustomFilterDialogComponent_Conditional_3_Conditional_13_Template, 2, 2, "button", 12)(14, AddCustomFilterDialogComponent_Conditional_3_Conditional_14_Template, 8, 0, "div", 13);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext();
    \u0275\u0275property("formGroup", ctx_r1.customFilterForm);
    \u0275\u0275advance(6);
    \u0275\u0275repeater(ctx_r1.filters.controls);
    \u0275\u0275advance(7);
    \u0275\u0275conditional(!ctx_r1.submitting ? 13 : 14);
  }
}
var AddCustomFilterDialogComponent = class _AddCustomFilterDialogComponent {
  constructor() {
    this.fb = inject(FormBuilder);
    this.filterType = input.required();
    this.filterTypeValue = computed(() => {
      let _filterType = this.filterType().toUpperCase();
      if (_filterType == "MOVIES") {
        return FilterType.MOVIES;
      }
      if (_filterType == "SERIES") {
        return FilterType.SERIES;
      }
      if (_filterType == "TRAILER") {
        return FilterType.TRAILER;
      }
      return FilterType.HOME;
    });
    this.customFilter = input(null);
    this.dialogClosed = new EventEmitter();
    this.isLoading = true;
    this.customfilterService = inject(CustomfilterService);
    this.computedSignal = computed(() => {
      let customFilterData = this.customFilter();
      this.initForm(customFilterData);
      return true;
    });
    this.boolFilterConditions = Object.values(BooleanFilterCondition);
    this.dateFilterConditions = Object.values(DateFilterCondition);
    this.numberFilterConditions = Object.values(NumberFilterCondition);
    this.stringFilterConditions = Object.values(StringFilterCondition);
    this.filterConditions = [];
    this.filterValueTypes = [];
    this.filterKeys = booleanFilterKeys.concat(dateFilterKeys, numberFilterKeys, stringFilterKeys).sort();
    this.viewForOptions = Object.values(FilterType);
    this.customFilterDialog = viewChild.required("customFilterDialog");
    this.submitting = false;
    effect(() => {
      this.initForm(this.customFilter());
    });
  }
  ngAfterViewInit() {
    this.customFilterDialog().nativeElement.showModal();
  }
  closeDialog(emitValue) {
    this.customFilterDialog().nativeElement.close();
    this.dialogClosed.emit(emitValue);
    this.filters.clear();
    this.addFilter();
    this.customFilterForm.reset();
  }
  displayTitle(value) {
    return value.toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }
  initForm(customFilterData) {
    let _form = this.fb.group({
      id: [customFilterData ? customFilterData.id : null],
      filter_type: [customFilterData ? customFilterData.filter_type : this.filterTypeValue(), Validators.required],
      filter_name: [customFilterData ? customFilterData.filter_name : "", [Validators.required, Validators.maxLength(30)]],
      filters: this.fb.array([], Validators.required)
      // Will hold an array of filters.
    });
    this.customFilterForm = _form;
    if (customFilterData && customFilterData.filters && customFilterData.filters.length) {
      customFilterData.filters.forEach((filter) => {
        this.addFilter(filter);
      });
    } else {
      this.addFilter();
    }
    this.isLoading = false;
    return _form;
  }
  // Getter for the filters FormArray.
  get filters() {
    return this.customFilterForm.get("filters");
  }
  // Creates a FormGroup for a single filter.
  createFilter(filter) {
    return this.fb.group({
      id: [filter ? filter.id : null],
      filter_by: [filter ? filter.filter_by : "", Validators.required],
      filter_condition: [filter ? filter.filter_condition : "", Validators.required],
      filter_value: [filter ? filter.filter_value : "", Validators.required],
      customfilter_id: [filter ? filter.customfilter_id : null]
    });
  }
  // Get the filter conditions for a given filter key.
  getFilterConditions(filterKey) {
    if (booleanFilterKeys.includes(filterKey)) {
      return this.boolFilterConditions;
    } else if (dateFilterKeys.includes(filterKey)) {
      return this.dateFilterConditions;
    } else if (numberFilterKeys.includes(filterKey)) {
      return this.numberFilterConditions;
    } else if (stringFilterKeys.includes(filterKey)) {
      return this.stringFilterConditions;
    }
    return [];
  }
  // Get the filter value type for a given filter key.
  getFilterValueType(filterKey, filterCondition) {
    if (booleanFilterKeys.includes(filterKey)) {
      return "boolean";
    } else if (dateFilterKeys.includes(filterKey)) {
      if (filterCondition === DateFilterCondition.IN_THE_LAST || filterCondition === DateFilterCondition.NOT_IN_THE_LAST) {
        return "number_days";
      }
      return "date";
    } else if (numberFilterKeys.includes(filterKey)) {
      return "number";
    }
    return "string";
  }
  // Adds a new filter FormGroup to the filters FormArray.
  addFilter(filter) {
    if (filter && filter.filter_by) {
      this.filterConditions.push(this.getFilterConditions(filter.filter_by));
      this.filterValueTypes.push(this.getFilterValueType(filter.filter_by, filter.filter_condition));
    } else {
      this.filterConditions.push([]);
      this.filterValueTypes.push("string");
    }
    this.filters.push(this.createFilter(filter));
  }
  // Removes a filter FormGroup from the filters FormArray.
  removeFilter(index) {
    this.filterConditions.splice(index, 1);
    this.filters.removeAt(index);
  }
  // Add a value change listener for the filter_by control.
  onFilterByChange(event, index) {
    const filterByControl = this.filters.at(index).get("filter_by")?.value;
    this.filterConditions[index] = this.getFilterConditions(filterByControl);
    this.filterValueTypes[index] = this.getFilterValueType(filterByControl, "");
    this.filters.at(index).get("filter_condition")?.setValue("");
    if (booleanFilterKeys.includes(filterByControl)) {
      this.filters.at(index).get("filter_condition")?.setValue(BooleanFilterCondition.EQUALS);
    }
    this.filters.at(index).get("filter_value")?.reset();
  }
  onFilterConditionChange(event, index) {
    const filterByControl = this.filters.at(index).get("filter_by")?.value;
    if (event.target) {
      const filterCondition = event.target.value;
      this.filterValueTypes[index] = this.getFilterValueType(filterByControl, filterCondition);
    }
    this.filters.at(index).get("filter_value")?.reset();
  }
  onSubmit() {
    if (this.submitting) {
      return;
    }
    this.submitting = true;
    if (this.customFilterForm.valid) {
      let formData = this.customFilterForm.value;
      formData.filters.forEach((filter) => {
        filter.filter_value = filter.filter_value.toString();
      });
      if (this.customFilter()?.id) {
        this.customfilterService.update(formData).subscribe((value) => {
          this.closeDialog(value.id);
          this.submitting = false;
        });
      } else {
        this.customfilterService.create(formData).subscribe((value) => {
          this.closeDialog(value.id);
          this.submitting = false;
        });
      }
    } else {
      console.log("Form is invalid");
      this.customFilterForm.markAllAsTouched();
      this.submitting = false;
    }
  }
  static {
    this.\u0275fac = function AddCustomFilterDialogComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _AddCustomFilterDialogComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _AddCustomFilterDialogComponent, selectors: [["app-add-filter-dialog"]], viewQuery: function AddCustomFilterDialogComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuerySignal(ctx.customFilterDialog, _c0, 5);
      }
      if (rf & 2) {
        \u0275\u0275queryAdvance();
      }
    }, inputs: { filterType: [1, "filterType"], customFilter: [1, "customFilter"] }, outputs: { dialogClosed: "dialogClosed" }, decls: 4, vars: 1, consts: [["customFilterDialog", ""], [1, "center"], [3, "formGroup"], [3, "ngSubmit", "click", "formGroup"], [1, "form-group"], ["for", "filter_name"], ["id", "filter_name", "type", "text", "maxlength", "30", "formControlName", "filter_name"], ["formArrayName", "filters", 1, "filters-container"], [1, "filter-group", 3, "formGroupName"], ["type", "button", 1, "secondary", 3, "click"], [1, "buttons-row"], ["type", "button", 1, "danger", 3, "click"], ["type", "submit", 1, "primary", 3, "disabled"], ["title", "Submitting form data"], ["formControlName", "filter_by", 3, "change", "id"], ["value", "", "disabled", ""], [3, "value"], ["formControlName", "filter_condition", 3, "change", "id"], ["type", "text", "formControlName", "filter_value", 3, "id"], ["type", "number", "formControlName", "filter_value", 3, "id"], ["type", "date", "formControlName", "filter_value", 3, "id"], ["formControlName", "filter_value", 3, "id"], ["type", "button", 1, "danger", "icononly-button", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M253-99q-38.21 0-65.11-26.6Q161-152.2 161-190v-552h-58v-91h228v-47h297v47h228v91h-58v552q0 37.18-27.21 64.09Q743.59-99 706-99H253Zm453-643H253v552h453v-552ZM357-268h74v-398h-74v398Zm173 0h75v-398h-75v398ZM253-742v552-552Z"], ["type", "number", "placeholder", "days", "formControlName", "filter_value", 3, "id"], ["value", "true"], ["value", "false"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 0 200 200", 1, "icon-loading"], ["stroke-width", "14", "r", "15", "cx", "40", "cy", "65"], ["attributeName", "cy", "calcMode", "spline", "dur", "2", "values", "65;135;65;", "keySplines", ".5 0 .5 1;.5 0 .5 1", "repeatCount", "indefinite", "begin", "-.4"], ["stroke-width", "14", "r", "15", "cx", "100", "cy", "65"], ["attributeName", "cy", "calcMode", "spline", "dur", "2", "values", "65;135;65;", "keySplines", ".5 0 .5 1;.5 0 .5 1", "repeatCount", "indefinite", "begin", "-.2"], ["stroke-width", "14", "r", "15", "cx", "160", "cy", "65"], ["attributeName", "cy", "calcMode", "spline", "dur", "2", "values", "65;135;65;", "keySplines", ".5 0 .5 1;.5 0 .5 1", "repeatCount", "indefinite", "begin", "0"]], template: function AddCustomFilterDialogComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "dialog", null, 0);
        \u0275\u0275template(2, AddCustomFilterDialogComponent_Conditional_2_Template, 1, 0, "app-load-indicator", 1)(3, AddCustomFilterDialogComponent_Conditional_3_Template, 15, 2, "form", 2);
        \u0275\u0275elementEnd();
      }
      if (rf & 2) {
        \u0275\u0275advance(2);
        \u0275\u0275conditional(ctx.isLoading ? 2 : 3);
      }
    }, dependencies: [FormsModule, \u0275NgNoValidate, NgSelectOption, \u0275NgSelectMultipleOption, DefaultValueAccessor, NumberValueAccessor, SelectControlValueAccessor, NgControlStatus, NgControlStatusGroup, MaxLengthValidator, LoadIndicatorComponent, ReactiveFormsModule, FormGroupDirective, FormControlName, FormGroupName, FormArrayName], styles: ["\n\n[_nghost-%COMP%] {\n  display: contents;\n}\n.center[_ngcontent-%COMP%] {\n  margin: auto;\n}\nform[_ngcontent-%COMP%] {\n  padding: 1rem;\n  display: block flex;\n  flex-direction: column;\n  gap: 1rem;\n}\nlabel[_ngcontent-%COMP%] {\n  display: block;\n  margin-bottom: 0.4rem;\n  font-weight: bold;\n}\ninput[_ngcontent-%COMP%], \nselect[_ngcontent-%COMP%] {\n  padding: 0.5rem;\n  box-sizing: border-box;\n}\noption[_ngcontent-%COMP%] {\n  background-color: var(--color-surface-container-high);\n}\n.ng-touched.ng-invalid[_ngcontent-%COMP%]:not(form):not(div) {\n  border: 2px solid var(--color-danger);\n}\n.error[_ngcontent-%COMP%] {\n  color: var(--color-danger);\n  font-size: 0.9rem;\n  margin-top: 0.4rem;\n}\n.filters-container[_ngcontent-%COMP%] {\n  border-top: 1px solid var(--color-outline);\n  padding-top: 1rem;\n}\n.filter-group[_ngcontent-%COMP%] {\n  display: block flex;\n  flex-wrap: wrap;\n  gap: 1rem;\n  align-items: center;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  padding: 0.5rem;\n  margin-bottom: 0.75rem;\n  background-color: var(--color-surface-container-high);\n}\n.filter-group[_ngcontent-%COMP%]   [_ngcontent-%COMP%]:nth-child(3) {\n  flex: 1;\n  text-align: start;\n}\n.danger[_ngcontent-%COMP%] {\n  width: auto;\n  height: auto;\n}\n.danger[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  fill: var(--color-danger-text);\n}\n.buttons-row[_ngcontent-%COMP%] {\n  display: block flex;\n  align-items: center;\n  justify-content: space-around;\n}\n.icon-loading[_ngcontent-%COMP%] {\n  width: 1.5rem;\n  height: 1.5rem;\n  fill: var(--color-on-surface);\n}\n/*# sourceMappingURL=add-filter-dialog.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(AddCustomFilterDialogComponent, [{
    type: Component,
    args: [{ selector: "app-add-filter-dialog", imports: [FormsModule, LoadIndicatorComponent, ReactiveFormsModule], template: `<dialog #customFilterDialog>
  @if (isLoading) {
    <app-load-indicator class="center" />
  } @else {
    <form [formGroup]="customFilterForm" (ngSubmit)="onSubmit()" (click)="$event.stopPropagation()">
      <!-- View Name -->
      <div class="form-group">
        <label for="filter_name">Label</label>
        <input id="filter_name" type="text" maxlength="30" formControlName="filter_name" />
      </div>

      <!-- Filters FormArray -->
      <div formArrayName="filters" class="filters-container">
        <!-- <h3>Filters</h3> -->
        @for (filterGroup of filters.controls; track filterGroup; let i = $index) {
          <div [formGroupName]="i" class="filter-group">
            <!-- Filter By -->
            <div class="form-group">
              <!-- <label for="filter_by_{{ i }}">Filter By</label> -->
              <select id="filter_by_{{ i }}" formControlName="filter_by" (change)="onFilterByChange($event, i)">
                <option value="" disabled>Select Filter By</option>
                @for (filter of filterKeys; track filter) {
                  <option [value]="filter">
                    {{ displayTitle(filter) }}
                  </option>
                }
              </select>
            </div>

            <!-- Filter Condition -->
            <div class="form-group">
              <!-- <label for="filter_condition_{{ i }}">Filter Condition</label> -->
              <select id="filter_condition_{{ i }}" formControlName="filter_condition" (change)="onFilterConditionChange($event, i)">
                <option value="" disabled>Select Condition</option>
                @for (condition of filterConditions[i]; track condition) {
                  <option [value]="condition">
                    {{ displayTitle(condition) }}
                  </option>
                }
              </select>
            </div>

            <!-- Filter Value -->
            <div class="form-group">
              <!-- <label for="filter_value_{{ i }}">Filter Value</label> -->
              @if (filterValueTypes[i] === 'string') {
                <input id="filter_value_{{ i }}" type="text" formControlName="filter_value" />
              } @else if (filterValueTypes[i] === 'number') {
                <input id="filter_value_{{ i }}" type="number" formControlName="filter_value" />
              } @else if (filterValueTypes[i] === 'number_days') {
                <input id="filter_value_{{ i }}" type="number" placeholder="days" formControlName="filter_value" />
                <span> days</span>
              } @else if (filterValueTypes[i] === 'date') {
                <input id="filter_value_{{ i }}" type="date" formControlName="filter_value" />
              } @else if (filterValueTypes[i] === 'boolean') {
                <select id="filter_value_{{ i }}" formControlName="filter_value">
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              }
            </div>

            <!-- Remove Filter Button -->
            <button type="button" class="danger icononly-button" (click)="removeFilter(i)">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
                <path
                  d="M253-99q-38.21 0-65.11-26.6Q161-152.2 161-190v-552h-58v-91h228v-47h297v47h228v91h-58v552q0 37.18-27.21 64.09Q743.59-99 706-99H253Zm453-643H253v552h453v-552ZM357-268h74v-398h-74v398Zm173 0h75v-398h-75v398ZM253-742v552-552Z"
                />
              </svg>
            </button>
          </div>
        }
        <!-- Button to add a new filter -->
        <button type="button" class="secondary" (click)="addFilter()">Add Filter</button>
      </div>
      <div class="buttons-row">
        <!-- Button to Cancel Dialog -->
        <button type="button" class="danger" (click)="closeDialog(-1)">Cancel</button>

        @if (!submitting) {
          <!-- Submit button -->
          <button type="submit" class="primary" [disabled]="customFilterForm.pristine || customFilterForm.invalid || submitting">
            {{ customFilter() ? 'Update' : 'Create' }}
          </button>
        } @else {
          <!-- Show loading icon -->
          <div title="Submitting form data">
            <svg xmlns="http://www.w3.org/2000/svg" class="icon-loading" viewBox="0 0 200 200">
              <circle stroke-width="14" r="15" cx="40" cy="65">
                <animate
                  attributeName="cy"
                  calcMode="spline"
                  dur="2"
                  values="65;135;65;"
                  keySplines=".5 0 .5 1;.5 0 .5 1"
                  repeatCount="indefinite"
                  begin="-.4"
                ></animate>
              </circle>
              <circle stroke-width="14" r="15" cx="100" cy="65">
                <animate
                  attributeName="cy"
                  calcMode="spline"
                  dur="2"
                  values="65;135;65;"
                  keySplines=".5 0 .5 1;.5 0 .5 1"
                  repeatCount="indefinite"
                  begin="-.2"
                ></animate>
              </circle>
              <circle stroke-width="14" r="15" cx="160" cy="65">
                <animate
                  attributeName="cy"
                  calcMode="spline"
                  dur="2"
                  values="65;135;65;"
                  keySplines=".5 0 .5 1;.5 0 .5 1"
                  repeatCount="indefinite"
                  begin="0"
                ></animate>
              </circle>
            </svg>
          </div>
        }
      </div>
    </form>
  }
</dialog>
`, styles: ["/* src/app/media/add-filter-dialog/add-filter-dialog.component.scss */\n:host {\n  display: contents;\n}\n.center {\n  margin: auto;\n}\nform {\n  padding: 1rem;\n  display: block flex;\n  flex-direction: column;\n  gap: 1rem;\n}\nlabel {\n  display: block;\n  margin-bottom: 0.4rem;\n  font-weight: bold;\n}\ninput,\nselect {\n  padding: 0.5rem;\n  box-sizing: border-box;\n}\noption {\n  background-color: var(--color-surface-container-high);\n}\n.ng-touched.ng-invalid:not(form):not(div) {\n  border: 2px solid var(--color-danger);\n}\n.error {\n  color: var(--color-danger);\n  font-size: 0.9rem;\n  margin-top: 0.4rem;\n}\n.filters-container {\n  border-top: 1px solid var(--color-outline);\n  padding-top: 1rem;\n}\n.filter-group {\n  display: block flex;\n  flex-wrap: wrap;\n  gap: 1rem;\n  align-items: center;\n  border: 1px solid var(--color-outline);\n  border-radius: 0.5rem;\n  padding: 0.5rem;\n  margin-bottom: 0.75rem;\n  background-color: var(--color-surface-container-high);\n}\n.filter-group :nth-child(3) {\n  flex: 1;\n  text-align: start;\n}\n.danger {\n  width: auto;\n  height: auto;\n}\n.danger svg {\n  fill: var(--color-danger-text);\n}\n.buttons-row {\n  display: block flex;\n  align-items: center;\n  justify-content: space-around;\n}\n.icon-loading {\n  width: 1.5rem;\n  height: 1.5rem;\n  fill: var(--color-on-surface);\n}\n/*# sourceMappingURL=add-filter-dialog.component.css.map */\n"] }]
  }], () => [], { dialogClosed: [{
    type: Output
  }] });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(AddCustomFilterDialogComponent, { className: "AddCustomFilterDialogComponent", filePath: "src/app/media/add-filter-dialog/add-filter-dialog.component.ts", lineNumber: 27 });
})();

export {
  DateFilterCondition,
  NumberFilterCondition,
  StringFilterCondition,
  booleanFilterKeys,
  dateFilterKeys,
  numberFilterKeys,
  stringFilterKeys,
  CustomfilterService,
  AddCustomFilterDialogComponent
};
//# sourceMappingURL=chunk-GVMLCJCM.js.map
