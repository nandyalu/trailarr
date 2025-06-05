import {
  ProfileSelectDialogComponent
} from "./chunk-L4Z4F7TL.js";
import {
  MediaService
} from "./chunk-3ILQGILQ.js";
import {
  durationString,
  jsonEqual
} from "./chunk-GF5DKDDQ.js";
import "./chunk-J3HM2TW5.js";
import {
  ActivatedRoute,
  FilesService
} from "./chunk-U5GO6X62.js";
import {
  WebsocketService
} from "./chunk-KIVIDEQ5.js";
import {
  DefaultValueAccessor,
  FormsModule,
  NgControlStatus,
  NgModel
} from "./chunk-BOQEVO5H.js";
import {
  LoadIndicatorComponent
} from "./chunk-7SOVNULQ.js";
import {
  Component,
  DatePipe,
  NgIf,
  NgTemplateOutlet,
  Pipe,
  TitleCasePipe,
  ViewChild,
  ViewContainerRef,
  __async,
  catchError,
  computed,
  effect,
  inject,
  input,
  of,
  resource,
  setClassMetadata,
  signal,
  ɵsetClassDebugInfo,
  ɵɵadvance,
  ɵɵclassProp,
  ɵɵconditional,
  ɵɵdeclareLet,
  ɵɵdefineComponent,
  ɵɵdefinePipe,
  ɵɵelement,
  ɵɵelementContainer,
  ɵɵelementContainerEnd,
  ɵɵelementContainerStart,
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
  ɵɵpropertyInterpolate1,
  ɵɵpureFunction1,
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
  ɵɵstyleMap,
  ɵɵtemplate,
  ɵɵtemplateRefExtractor,
  ɵɵtext,
  ɵɵtextInterpolate,
  ɵɵtextInterpolate1,
  ɵɵtextInterpolate2,
  ɵɵtwoWayBindingSet,
  ɵɵtwoWayListener,
  ɵɵtwoWayProperty,
  ɵɵviewQuery
} from "./chunk-FAGZ4ZSE.js";

// src/app/helpers/duration-pipe.ts
var DurationConvertPipe = class _DurationConvertPipe {
  transform(value) {
    return durationString(value);
  }
  static {
    this.\u0275fac = function DurationConvertPipe_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _DurationConvertPipe)();
    };
  }
  static {
    this.\u0275pipe = /* @__PURE__ */ \u0275\u0275definePipe({ name: "durationConvert", type: _DurationConvertPipe, pure: true });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(DurationConvertPipe, [{
    type: Pipe,
    args: [{ name: "durationConvert", pure: true }]
  }], null, null);
})();

// src/app/media/media-details/files/files.component.ts
var _c0 = ["optionsDialog"];
var _c1 = ["textDialog"];
var _c2 = ["videoDialog"];
var _c3 = ["videoDialogContent"];
var _c4 = ["videoInfoDialog"];
var _c5 = ["renameDialog"];
var _c6 = ["deleteFileDialog"];
var _c7 = (a0) => ({ folderUntyped: a0 });
var _forTrack0 = ($index, $item) => $item.index;
function FilesComponent_Conditional_4_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 11);
  }
}
function FilesComponent_Conditional_5_Conditional_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 33);
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext(2);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1("Error: ", ctx_r1.filesError(), "");
  }
}
function FilesComponent_Conditional_5_Conditional_2_ng_container_8_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function FilesComponent_Conditional_5_Conditional_2_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 34);
    \u0275\u0275element(1, "div");
    \u0275\u0275elementStart(2, "div");
    \u0275\u0275text(3, "Name");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(4, "div");
    \u0275\u0275text(5, "Size");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(6, "div");
    \u0275\u0275text(7, "Modified");
    \u0275\u0275elementEnd()();
    \u0275\u0275template(8, FilesComponent_Conditional_5_Conditional_2_ng_container_8_Template, 1, 0, "ng-container", 35);
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext(2);
    const folFileTemplate_r3 = \u0275\u0275reference(7);
    \u0275\u0275advance(8);
    \u0275\u0275property("ngTemplateOutlet", folFileTemplate_r3)("ngTemplateOutletContext", \u0275\u0275pureFunction1(2, _c7, ctx_r1.filesResource.value()));
  }
}
function FilesComponent_Conditional_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 12);
    \u0275\u0275template(1, FilesComponent_Conditional_5_Conditional_1_Template, 2, 1, "p", 33)(2, FilesComponent_Conditional_5_Conditional_2_Template, 9, 4);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext();
    \u0275\u0275advance();
    \u0275\u0275conditional(ctx_r1.filesResource.error() ? 1 : 2);
  }
}
function FilesComponent_ng_template_6_Conditional_4_Conditional_0_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 16);
    \u0275\u0275element(1, "path", 43);
    \u0275\u0275elementEnd();
  }
}
function FilesComponent_ng_template_6_Conditional_4_Conditional_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 16);
    \u0275\u0275element(1, "path", 44);
    \u0275\u0275elementEnd();
  }
}
function FilesComponent_ng_template_6_Conditional_4_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, FilesComponent_ng_template_6_Conditional_4_Conditional_0_Template, 2, 0, ":svg:svg", 16)(1, FilesComponent_ng_template_6_Conditional_4_Conditional_1_Template, 2, 0, ":svg:svg", 16);
  }
  if (rf & 2) {
    \u0275\u0275nextContext();
    const folder_r5 = \u0275\u0275readContextLet(0);
    \u0275\u0275conditional(folder_r5.isExpanded ? 0 : 1);
  }
}
function FilesComponent_ng_template_6_Conditional_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 16);
    \u0275\u0275element(1, "path", 45);
    \u0275\u0275elementEnd();
  }
}
function FilesComponent_ng_template_6_Conditional_13_Conditional_1_For_1_ng_container_0_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainer(0);
  }
}
function FilesComponent_ng_template_6_Conditional_13_Conditional_1_For_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, FilesComponent_ng_template_6_Conditional_13_Conditional_1_For_1_ng_container_0_Template, 1, 0, "ng-container", 35);
  }
  if (rf & 2) {
    const childFolder_r6 = ctx.$implicit;
    \u0275\u0275nextContext(4);
    const folFileTemplate_r3 = \u0275\u0275reference(7);
    \u0275\u0275property("ngTemplateOutlet", folFileTemplate_r3)("ngTemplateOutletContext", \u0275\u0275pureFunction1(2, _c7, childFolder_r6));
  }
}
function FilesComponent_ng_template_6_Conditional_13_Conditional_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275repeaterCreate(0, FilesComponent_ng_template_6_Conditional_13_Conditional_1_For_1_Template, 1, 4, "ng-container", null, \u0275\u0275repeaterTrackByIdentity);
  }
  if (rf & 2) {
    \u0275\u0275nextContext(2);
    const folder_r5 = \u0275\u0275readContextLet(0);
    \u0275\u0275repeater(folder_r5.files);
  }
}
function FilesComponent_ng_template_6_Conditional_13_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 42);
    \u0275\u0275template(1, FilesComponent_ng_template_6_Conditional_13_Conditional_1_Template, 2, 0);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    \u0275\u0275nextContext();
    const folder_r5 = \u0275\u0275readContextLet(0);
    \u0275\u0275advance();
    \u0275\u0275conditional(folder_r5.isExpanded ? 1 : -1);
  }
}
function FilesComponent_ng_template_6_Template(rf, ctx) {
  if (rf & 1) {
    const _r4 = \u0275\u0275getCurrentView();
    \u0275\u0275declareLet(0);
    \u0275\u0275elementStart(1, "div", 36)(2, "div", 37);
    \u0275\u0275listener("click", function FilesComponent_ng_template_6_Template_div_click_2_listener() {
      \u0275\u0275restoreView(_r4);
      const folder_r5 = \u0275\u0275readContextLet(0);
      const ctx_r1 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r1.openFolderOrOptions(folder_r5));
    });
    \u0275\u0275elementStart(3, "div", 38);
    \u0275\u0275template(4, FilesComponent_ng_template_6_Conditional_4_Template, 2, 1)(5, FilesComponent_ng_template_6_Conditional_5_Template, 2, 0, ":svg:svg", 16);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(6, "div", 39);
    \u0275\u0275text(7);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(8, "div", 40);
    \u0275\u0275text(9);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(10, "div", 41);
    \u0275\u0275text(11);
    \u0275\u0275pipe(12, "date");
    \u0275\u0275elementEnd()();
    \u0275\u0275template(13, FilesComponent_ng_template_6_Conditional_13_Template, 2, 1, "div", 42);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const folderUntyped_r7 = ctx.folderUntyped;
    const folder_r8 = \u0275\u0275storeLet(\u0275\u0275nextContext().asFolderInfo(folderUntyped_r7));
    \u0275\u0275advance(2);
    \u0275\u0275classProp("parent", folder_r8.type == "folder");
    \u0275\u0275advance(2);
    \u0275\u0275conditional(folder_r8.type === "folder" ? 4 : 5);
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate(folder_r8.name);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(folder_r8.size);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(\u0275\u0275pipeBind1(12, 8, folder_r8.modified));
    \u0275\u0275advance(2);
    \u0275\u0275conditional(folder_r8.type === "folder" ? 13 : -1);
  }
}
function FilesComponent_Conditional_18_Template(rf, ctx) {
  if (rf & 1) {
    const _r9 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 46);
    \u0275\u0275listener("click", function FilesComponent_Conditional_18_Template_div_click_0_listener() {
      \u0275\u0275restoreView(_r9);
      const ctx_r1 = \u0275\u0275nextContext();
      ctx_r1.closeOptionsDialog();
      return \u0275\u0275resetView(ctx_r1.openVideoDialog());
    });
    \u0275\u0275elementStart(1, "span");
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(2, "svg", 16);
    \u0275\u0275element(3, "path", 47);
    \u0275\u0275elementEnd()();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(4, "span");
    \u0275\u0275text(5, "Play Video");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(6, "div", 48);
    \u0275\u0275listener("click", function FilesComponent_Conditional_18_Template_div_click_6_listener() {
      \u0275\u0275restoreView(_r9);
      const ctx_r1 = \u0275\u0275nextContext();
      ctx_r1.closeOptionsDialog();
      return \u0275\u0275resetView(ctx_r1.openVideoInfoDialog());
    });
    \u0275\u0275elementStart(7, "span");
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(8, "svg", 16);
    \u0275\u0275element(9, "path", 49);
    \u0275\u0275elementEnd()();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(10, "span");
    \u0275\u0275text(11, "Video Info");
    \u0275\u0275elementEnd()();
  }
}
function FilesComponent_Conditional_19_Conditional_0_Template(rf, ctx) {
  if (rf & 1) {
    const _r10 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 51);
    \u0275\u0275listener("click", function FilesComponent_Conditional_19_Conditional_0_Template_div_click_0_listener() {
      \u0275\u0275restoreView(_r10);
      const ctx_r1 = \u0275\u0275nextContext(2);
      ctx_r1.closeOptionsDialog();
      return \u0275\u0275resetView(ctx_r1.openTextDialog());
    });
    \u0275\u0275elementStart(1, "span");
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(2, "svg", 16);
    \u0275\u0275element(3, "path", 52);
    \u0275\u0275elementEnd()();
    \u0275\u0275namespaceHTML();
    \u0275\u0275elementStart(4, "span");
    \u0275\u0275text(5, "View Text");
    \u0275\u0275elementEnd()();
  }
}
function FilesComponent_Conditional_19_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, FilesComponent_Conditional_19_Conditional_0_Template, 6, 0, "div", 50);
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext();
    \u0275\u0275conditional(ctx_r1.isTextFile() ? 0 : -1);
  }
}
function FilesComponent_Conditional_34_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 11);
  }
}
function FilesComponent_Conditional_35_For_7_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275text(0, "\n          ");
    \u0275\u0275text(1, "\n          ");
    \u0275\u0275elementStart(2, "code");
    \u0275\u0275text(3);
    \u0275\u0275elementEnd();
    \u0275\u0275text(4, "\n        ");
  }
  if (rf & 2) {
    const line_r12 = ctx.$implicit;
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate(line_r12);
  }
}
function FilesComponent_Conditional_35_Template(rf, ctx) {
  if (rf & 1) {
    const _r11 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 53);
    \u0275\u0275listener("click", function FilesComponent_Conditional_35_Template_div_click_0_listener($event) {
      \u0275\u0275restoreView(_r11);
      return \u0275\u0275resetView($event.stopPropagation());
    });
    \u0275\u0275elementStart(1, "h2");
    \u0275\u0275text(2);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "div", 54)(4, "pre");
    \u0275\u0275text(5, "        ");
    \u0275\u0275repeaterCreate(6, FilesComponent_Conditional_35_For_7_Template, 5, 1, null, null, \u0275\u0275repeaterTrackByIndex);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(8, "div", 27)(9, "button", 29);
    \u0275\u0275listener("click", function FilesComponent_Conditional_35_Template_button_click_9_listener() {
      \u0275\u0275restoreView(_r11);
      const ctx_r1 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r1.closeTextDialog());
    });
    \u0275\u0275text(10, "Close");
    \u0275\u0275elementEnd()()();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext();
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(ctx_r1.selectedFileName());
    \u0275\u0275advance(4);
    \u0275\u0275repeater(ctx_r1.selectedFileText());
  }
}
function FilesComponent_Conditional_42_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 11);
  }
}
function FilesComponent_Conditional_43_Conditional_4_Conditional_24_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 57)(1, "span");
    \u0275\u0275text(2, "Audio Tracks");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "code");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext(3);
    \u0275\u0275advance(4);
    \u0275\u0275textInterpolate(ctx_r1.audioTracks());
  }
}
function FilesComponent_Conditional_43_Conditional_4_Conditional_25_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 57)(1, "span");
    \u0275\u0275text(2, "Subtitles");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "code");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const ctx_r1 = \u0275\u0275nextContext(3);
    \u0275\u0275advance(4);
    \u0275\u0275textInterpolate(ctx_r1.subtitleTracks());
  }
}
function FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_4_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 57)(1, "span");
    \u0275\u0275text(2, "Codec");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "code");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const stream_r14 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275advance(4);
    \u0275\u0275textInterpolate(stream_r14.codec_name);
  }
}
function FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 57)(1, "span");
    \u0275\u0275text(2, "Language");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "code");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const stream_r14 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275advance(4);
    \u0275\u0275textInterpolate(stream_r14.language);
  }
}
function FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_6_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 57)(1, "span");
    \u0275\u0275text(2, "Display Dimensions");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "code");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const stream_r14 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275advance(4);
    \u0275\u0275textInterpolate2("", stream_r14.coded_width, "x", stream_r14.coded_height, "");
  }
}
function FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_7_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 57)(1, "span");
    \u0275\u0275text(2, "Audio Channels");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "code");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const stream_r14 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275advance(4);
    \u0275\u0275textInterpolate(stream_r14.audio_channels);
  }
}
function FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_8_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 57)(1, "span");
    \u0275\u0275text(2, "Audio Frequency");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "code");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const stream_r14 = \u0275\u0275nextContext().$implicit;
    \u0275\u0275advance(4);
    \u0275\u0275textInterpolate(stream_r14.sample_rate);
  }
}
function FilesComponent_Conditional_43_Conditional_4_For_27_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "section")(1, "h2");
    \u0275\u0275text(2);
    \u0275\u0275elementEnd();
    \u0275\u0275element(3, "hr");
    \u0275\u0275template(4, FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_4_Template, 5, 1, "div", 57)(5, FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_5_Template, 5, 1, "div", 57)(6, FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_6_Template, 5, 2, "div", 57)(7, FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_7_Template, 5, 1, "div", 57)(8, FilesComponent_Conditional_43_Conditional_4_For_27_Conditional_8_Template, 5, 1, "div", 57);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const stream_r14 = ctx.$implicit;
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate2("Track ", stream_r14.index, ": ", stream_r14.codec_type, "");
    \u0275\u0275advance(2);
    \u0275\u0275conditional(stream_r14.codec_name ? 4 : -1);
    \u0275\u0275advance();
    \u0275\u0275conditional(stream_r14.language ? 5 : -1);
    \u0275\u0275advance();
    \u0275\u0275conditional(stream_r14.coded_height && stream_r14.coded_width ? 6 : -1);
    \u0275\u0275advance();
    \u0275\u0275conditional(stream_r14.audio_channels ? 7 : -1);
    \u0275\u0275advance();
    \u0275\u0275conditional(stream_r14.sample_rate ? 8 : -1);
  }
}
function FilesComponent_Conditional_43_Conditional_4_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "section", 56)(1, "h2");
    \u0275\u0275text(2, "File Info");
    \u0275\u0275elementEnd();
    \u0275\u0275element(3, "hr");
    \u0275\u0275elementStart(4, "div", 57)(5, "span");
    \u0275\u0275text(6, "File Name");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(7, "code");
    \u0275\u0275text(8);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(9, "div", 57)(10, "span");
    \u0275\u0275text(11, "Format");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(12, "code");
    \u0275\u0275text(13);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(14, "div", 57)(15, "span");
    \u0275\u0275text(16, "Bitrate");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(17, "code");
    \u0275\u0275text(18);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(19, "div", 57)(20, "span");
    \u0275\u0275text(21, "Duration");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(22, "code");
    \u0275\u0275text(23);
    \u0275\u0275elementEnd()();
    \u0275\u0275template(24, FilesComponent_Conditional_43_Conditional_4_Conditional_24_Template, 5, 1, "div", 57)(25, FilesComponent_Conditional_43_Conditional_4_Conditional_25_Template, 5, 1, "div", 57);
    \u0275\u0275elementEnd();
    \u0275\u0275repeaterCreate(26, FilesComponent_Conditional_43_Conditional_4_For_27_Template, 9, 7, "section", null, _forTrack0);
  }
  if (rf & 2) {
    const info_r15 = ctx;
    const ctx_r1 = \u0275\u0275nextContext(2);
    \u0275\u0275advance(8);
    \u0275\u0275textInterpolate(info_r15.name);
    \u0275\u0275advance(5);
    \u0275\u0275textInterpolate(info_r15.format_name);
    \u0275\u0275advance(5);
    \u0275\u0275textInterpolate(info_r15.bitrate);
    \u0275\u0275advance(5);
    \u0275\u0275textInterpolate(info_r15.duration);
    \u0275\u0275advance();
    \u0275\u0275conditional(ctx_r1.audioTracks().length > 0 ? 24 : -1);
    \u0275\u0275advance();
    \u0275\u0275conditional(ctx_r1.subtitleTracks().length > 0 ? 25 : -1);
    \u0275\u0275advance();
    \u0275\u0275repeater(info_r15.streams);
  }
}
function FilesComponent_Conditional_43_Conditional_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "h2");
    \u0275\u0275text(1, "Video Info");
    \u0275\u0275elementEnd();
    \u0275\u0275element(2, "hr");
    \u0275\u0275elementStart(3, "code", 58);
    \u0275\u0275text(4, " Unable to fetch video info. ");
    \u0275\u0275elementEnd();
  }
}
function FilesComponent_Conditional_43_Template(rf, ctx) {
  if (rf & 1) {
    const _r13 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 24)(1, "h1");
    \u0275\u0275text(2, "Video Properties");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "div", 55);
    \u0275\u0275listener("click", function FilesComponent_Conditional_43_Template_div_click_3_listener($event) {
      \u0275\u0275restoreView(_r13);
      return \u0275\u0275resetView($event.stopPropagation());
    });
    \u0275\u0275template(4, FilesComponent_Conditional_43_Conditional_4_Template, 28, 6)(5, FilesComponent_Conditional_43_Conditional_5_Template, 5, 0);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(6, "div", 27)(7, "button", 29);
    \u0275\u0275listener("click", function FilesComponent_Conditional_43_Template_button_click_7_listener() {
      \u0275\u0275restoreView(_r13);
      const ctx_r1 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r1.closeVideoInfoDialog());
    });
    \u0275\u0275text(8, "Close");
    \u0275\u0275elementEnd()()();
  }
  if (rf & 2) {
    let tmp_10_0;
    const ctx_r1 = \u0275\u0275nextContext();
    \u0275\u0275advance(4);
    \u0275\u0275conditional((tmp_10_0 = ctx_r1.videoInfo()) ? 4 : 5, tmp_10_0);
  }
}
var FilesComponent = class _FilesComponent {
  constructor() {
    this.filesService = inject(FilesService);
    this.mediaService = inject(MediaService);
    this.webSocketService = inject(WebsocketService);
    this.mediaId = input.required();
    this.textFileLoading = signal(true);
    this.videoInfoLoading = signal(true);
    this.selectedFilePath = "";
    this.selectedFileName = signal("");
    this.videoInfo = signal(null);
    this.selectedFileText = signal([], { equal: jsonEqual });
    this.audioTracks = computed(() => (this.videoInfo()?.streams ?? []).filter((stream) => stream.codec_type.includes("audio")).map((stream) => `${stream.language || "unk"} (${stream.codec_name})`).join(", "));
    this.subtitleTracks = computed(() => (this.videoInfo()?.streams ?? []).filter((stream) => stream.codec_type.includes("subtitle")).map((stream) => `${stream.language || "unk"} (${stream.codec_name})`).join(", "));
    this.filesResource = resource({
      request: this.mediaId,
      loader: ({ request: mediaId }) => this.mediaService.fetchMediaFiles(mediaId)
    });
    this.filesError = computed(() => {
      const _error = this.filesResource.error();
      return _error.error.detail;
    });
    this.isTextFile = computed(() => [".txt", ".srt", ".log", ".json", ".py", ".sh"].some((ext) => this.selectedFileName().endsWith(ext)));
    this.isVideoFile = computed(() => [".mp4", ".mkv", ".avi", ".webm"].some((ext) => this.selectedFileName().endsWith(ext)));
  }
  // ngOnInit() {
  //   this.getMediaFiles();
  // }
  // getMediaFiles(): void {
  //   // Get Media Files
  //   this.mediaService.getMediaFiles(this.mediaId() + 1000).subscribe((files: FolderInfo | string) => {
  //     if (typeof files === 'string') {
  //       this.mediaFilesResponse = files;
  //     } else {
  //       this.mediaFiles = files;
  //     }
  //     this.filesLoading = false;
  //   });
  // }
  asFolderInfo(folder) {
    return folder;
  }
  openFolderOrOptions(folder) {
    if (folder.type === "folder") {
      folder.isExpanded = !folder.isExpanded;
    } else {
      this.selectedFilePath = folder.path;
      this.selectedFileName.set(folder.name);
      this.openOptionsDialog();
    }
  }
  renameFile() {
    this.closeRenameDialog();
    let selectedFileBasePath = this.selectedFilePath.split("/").slice(0, -1).join("/");
    let newName = selectedFileBasePath + "/" + this.selectedFileName();
    this.filesService.renameFileFolApiV1FilesRenamePost({ old_path: this.selectedFilePath, new_path: newName }).subscribe((renamed) => {
      let msg = "";
      if (renamed) {
        msg = "File renamed successfully!";
      } else {
        msg = "Failed to rename file!";
      }
      this.webSocketService.showToast(msg, renamed ? "success" : "error");
      this.filesResource.reload();
    });
  }
  deleteFile() {
    this.closeDeleteFileDialog();
    this.filesService.deleteFileFolApiV1FilesDeleteDelete({ path: this.selectedFilePath, media_id: this.mediaId() }).subscribe((deleted) => {
      let msg = "";
      if (deleted) {
        msg = "Deleted successfully!";
      } else {
        msg = "Failed to delete!";
      }
      this.webSocketService.showToast(msg, deleted ? "success" : "error");
      this.filesResource.reload();
    });
  }
  openOptionsDialog() {
    this.optionsDialog.nativeElement.showModal();
  }
  closeOptionsDialog() {
    this.optionsDialog.nativeElement.close();
  }
  openTextDialog() {
    this.closeOptionsDialog();
    this.textFileLoading.set(true);
    this.selectedFileText.set([]);
    this.textDialog.nativeElement.showModal();
    this.filesService.readFileApiV1FilesReadGet({ file_path: this.selectedFilePath }).subscribe({
      next: (content) => this.selectedFileText.set(content.split("\n")),
      complete: () => this.textFileLoading.set(false),
      error: () => this.textFileLoading.set(false)
    });
  }
  closeTextDialog() {
    this.textDialog.nativeElement.close();
  }
  openVideoDialog() {
    this.videoDialog.nativeElement.showModal();
    let videoUrl = `/api/v1/files/video?file_path=${encodeURIComponent(this.selectedFilePath)}`;
    let videoRef = `
      <style>
        video {
          width: 75vw;
          height: auto;
        }
        @media (max-width: 768px) {
          video {
            width: 100%;
          }
        }
      </style>
      <video controls controlsList="nodownload">
        <source src="${videoUrl}" type="video/mp4">
        Your browser does not support the video tag.</source>
      </video>`;
    this.videoDialogContent.nativeElement.innerHTML = videoRef;
  }
  closeVideoDialog() {
    this.videoDialogContent.nativeElement.innerHTML = "";
    this.videoDialog.nativeElement.close();
  }
  openVideoInfoDialog() {
    this.videoInfoLoading.set(true);
    this.videoInfoDialog.nativeElement.showModal();
    this.filesService.getVideoInfoApiV1FilesVideoInfoGet({ file_path: this.selectedFilePath }).subscribe({
      next: (videoInfo) => {
        this.videoInfo.set(videoInfo);
      },
      complete: () => this.videoInfoLoading.set(false),
      error: () => this.videoInfoLoading.set(false)
    });
  }
  closeVideoInfoDialog() {
    this.videoInfoDialog.nativeElement.close();
    this.videoInfo.set(null);
  }
  openRenameDialog() {
    this.closeOptionsDialog();
    this.renameDialog.nativeElement.showModal();
  }
  closeRenameDialog() {
    this.renameDialog.nativeElement.close();
  }
  openDeleteFileDialog() {
    this.closeOptionsDialog();
    this.deleteFileDialog.nativeElement.showModal();
  }
  closeDeleteFileDialog() {
    this.deleteFileDialog.nativeElement.close();
  }
  static {
    this.\u0275fac = function FilesComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _FilesComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _FilesComponent, selectors: [["media-files"]], viewQuery: function FilesComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuery(_c0, 5);
        \u0275\u0275viewQuery(_c1, 5);
        \u0275\u0275viewQuery(_c2, 5);
        \u0275\u0275viewQuery(_c3, 5);
        \u0275\u0275viewQuery(_c4, 5);
        \u0275\u0275viewQuery(_c5, 5);
        \u0275\u0275viewQuery(_c6, 5);
      }
      if (rf & 2) {
        let _t;
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.optionsDialog = _t.first);
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.textDialog = _t.first);
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.videoDialog = _t.first);
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.videoDialogContent = _t.first);
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.videoInfoDialog = _t.first);
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.renameDialog = _t.first);
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.deleteFileDialog = _t.first);
      }
    }, inputs: { mediaId: [1, "mediaId"] }, decls: 69, vars: 6, consts: [["folFileTemplate", ""], ["optionsDialog", ""], ["optionsDialogContent", ""], ["textDialog", ""], ["videoDialog", ""], ["videoDialogContent", ""], ["videoInfoDialog", ""], ["renameDialog", ""], ["deleteFileDialog", ""], [1, "media-files-container"], [1, "text-md", "files-title"], [1, "center"], [1, "media-files"], [3, "click"], [1, "dialog-content", 3, "click"], [1, "close", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "m249-186-63-63 231-231-231-230 63-64 231 230 231-230 63 64-230 230 230 231-63 63-231-230-231 230Z"], [1, "dialog-options"], ["title", "Rename", 1, "icon-link", 3, "click"], ["d", "M81-5v-138h798V-5H81Zm150-327h30l371-371-13.35-15.86L604-733 231-362v30Zm-68 69v-126l486-488q10-9 23.11-14.5 13.12-5.5 26-5.5 12.89 0 25.89 5.75T748-876l28 25q12 10 17 23.99 5 13.99 5 26.52 0 13.17-5.46 26.76Q787.09-760.14 777-751L288-263H163Zm563-538-27-27 27 27Zm-94 98-13.35-15.86L604-733l28 30Z"], ["title", "Delete", 1, "icon-link", "danger-option", 3, "click"], ["d", "M253-99q-38.21 0-65.11-26.6Q161-152.2 161-190v-552h-58v-91h228v-47h297v47h228v91h-58v552q0 37.18-27.21 64.09Q743.59-99 706-99H253Zm453-643H253v552h453v-552ZM357-268h74v-398h-74v398Zm173 0h75v-398h-75v398ZM253-742v552-552Z"], [1, "text-dialog"], [1, "info-dialog"], [1, "rename-dialog", 3, "click"], ["id", "rename-file", "type", "text", "placeholder", "New Name", 1, "rename-input", 3, "ngModelChange", "ngModel"], [1, "buttons-row"], [1, "primary", 3, "click"], [1, "tertiary", 3, "click"], ["id", "deleteFileDialog", 3, "click"], [1, "delete-dialog", 3, "click"], [1, "danger", 3, "click"], [1, "text-sm", "text-center"], [1, "files-header", "sm-none", "text-sm"], [4, "ngTemplateOutlet", "ngTemplateOutletContext"], [1, "files-accordion"], [1, "files-header", 3, "click"], [1, "files-icon"], [1, "files-name"], [1, "files-size"], [1, "files-modified"], [1, "child"], ["d", "M146.67-160q-26.34 0-46.5-20.17Q80-200.33 80-226.67v-506.66q0-26.34 20.17-46.5Q120.33-800 146.67-800H414l66.67 66.67h332.66q26.34 0 46.5 20.16Q880-693 880-666.67H146.67v440l100-373.33H940L834.33-209.67q-6.66 24.67-24.5 37.17Q792-160 766.67-160h-620Z"], ["d", "M146.67-160q-27 0-46.84-20.17Q80-200.33 80-226.67v-506.66q0-26.34 19.83-46.5Q119.67-800 146.67-800H414l66.67 66.67h332.66q26.34 0 46.5 20.16Q880-693 880-666.67v440q0 26.34-20.17 46.5Q839.67-160 813.33-160H146.67Z"], ["d", "M319.33-246.67h321.34v-66.66H319.33v66.66Zm0-166.66h321.34V-480H319.33v66.67ZM226.67-80q-27 0-46.84-19.83Q160-119.67 160-146.67v-666.66q0-27 19.83-46.84Q199.67-880 226.67-880H574l226 226v507.33q0 27-19.83 46.84Q760.33-80 733.33-80H226.67Zm314-542.67h192.66L540.67-813.33v190.66Z"], ["title", "Play Video", 1, "icon-link", 3, "click"], ["d", "M320-203v-560l440 280-440 280Zm60-280Zm0 171 269-171-269-171v342Z"], ["title", "Video Info", 1, "icon-link", 3, "click"], ["d", "M447-272h73v-248h-73v248Zm32.89-330Q496-602 507-612.59q11-10.58 11-26.23 0-17.63-10.87-28.4Q496.26-678 480.19-678q-17.19 0-27.69 10.6T442-639.68q0 16.28 10.89 26.98 10.9 10.7 27 10.7Zm-.08 538q-85.92 0-161.52-33.02-75.61-33.02-131.93-89.34-56.32-56.32-89.34-132.13T64-480.5q0-86.09 33.08-161.81t89.68-132.31q56.61-56.59 132.06-88.99Q394.27-896 480.06-896q86.15 0 162.17 32.39 76.02 32.4 132.4 89Q831-718 863.5-641.96 896-565.92 896-479.72q0 86.19-32.39 161.29-32.4 75.11-88.99 131.51Q718.03-130.53 642-97.26 565.98-64 479.81-64Zm.69-73q142.01 0 242.26-100.74Q823-338.49 823-480.5T722.94-722.76Q622.89-823 480-823q-141.51 0-242.26 100.06Q137-622.89 137-480q0 141.51 100.74 242.26Q338.49-137 480.5-137Zm-.5-343Z"], ["title", "View Text", 1, "icon-link"], ["title", "View Text", 1, "icon-link", 3, "click"], ["d", "M321-250h318v-69H321v69Zm0-169h319v-68H321v68ZM229-59q-35.78 0-63.39-26.91Q138-112.83 138-150v-660q0-37.59 27.61-64.79Q193.22-902 229-902h364l230 228v524q0 37.17-27.91 64.09Q767.19-59 731-59H229Zm316-569v-182H229v660h502v-478H545ZM229-810v182-182 660-660Z"], [1, "text-dialog", 3, "click"], [1, "text-content"], [1, "info-container", 3, "click"], ["open", ""], [1, "info-content"], [1, "video-info"]], template: function FilesComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275elementStart(0, "div", 9)(1, "p", 10);
        \u0275\u0275text(2, "Files");
        \u0275\u0275elementEnd();
        \u0275\u0275element(3, "hr");
        \u0275\u0275template(4, FilesComponent_Conditional_4_Template, 1, 0, "app-load-indicator", 11)(5, FilesComponent_Conditional_5_Template, 3, 1, "div", 12);
        \u0275\u0275elementEnd();
        \u0275\u0275template(6, FilesComponent_ng_template_6_Template, 14, 10, "ng-template", null, 0, \u0275\u0275templateRefExtractor);
        \u0275\u0275elementStart(8, "dialog", 13, 1);
        \u0275\u0275listener("click", function FilesComponent_Template_dialog_click_8_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeOptionsDialog());
        });
        \u0275\u0275elementStart(10, "div", 14, 2);
        \u0275\u0275listener("click", function FilesComponent_Template_div_click_10_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(12, "h2");
        \u0275\u0275text(13, "Options");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(14, "i", 15);
        \u0275\u0275listener("click", function FilesComponent_Template_i_click_14_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeOptionsDialog());
        });
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(15, "svg", 16);
        \u0275\u0275element(16, "path", 17);
        \u0275\u0275elementEnd()();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(17, "div", 18);
        \u0275\u0275template(18, FilesComponent_Conditional_18_Template, 12, 0)(19, FilesComponent_Conditional_19_Template, 1, 1);
        \u0275\u0275elementStart(20, "div", 19);
        \u0275\u0275listener("click", function FilesComponent_Template_div_click_20_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.openRenameDialog());
        });
        \u0275\u0275elementStart(21, "span");
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(22, "svg", 16);
        \u0275\u0275element(23, "path", 20);
        \u0275\u0275elementEnd()();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(24, "span");
        \u0275\u0275text(25, "Rename");
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(26, "div", 21);
        \u0275\u0275listener("click", function FilesComponent_Template_div_click_26_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.openDeleteFileDialog());
        });
        \u0275\u0275elementStart(27, "span");
        \u0275\u0275namespaceSVG();
        \u0275\u0275elementStart(28, "svg", 16);
        \u0275\u0275element(29, "path", 22);
        \u0275\u0275elementEnd()();
        \u0275\u0275namespaceHTML();
        \u0275\u0275elementStart(30, "span");
        \u0275\u0275text(31, "Delete");
        \u0275\u0275elementEnd()()()()();
        \u0275\u0275elementStart(32, "dialog", 13, 3);
        \u0275\u0275listener("click", function FilesComponent_Template_dialog_click_32_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeTextDialog());
        });
        \u0275\u0275template(34, FilesComponent_Conditional_34_Template, 1, 0, "app-load-indicator", 11)(35, FilesComponent_Conditional_35_Template, 11, 1, "div", 23);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(36, "dialog", 13, 4);
        \u0275\u0275listener("click", function FilesComponent_Template_dialog_click_36_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeVideoDialog());
        });
        \u0275\u0275elementStart(38, "div", 13, 5);
        \u0275\u0275listener("click", function FilesComponent_Template_div_click_38_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementEnd()();
        \u0275\u0275elementStart(40, "dialog", 13, 6);
        \u0275\u0275listener("click", function FilesComponent_Template_dialog_click_40_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeVideoInfoDialog());
        });
        \u0275\u0275template(42, FilesComponent_Conditional_42_Template, 1, 0, "app-load-indicator", 11)(43, FilesComponent_Conditional_43_Template, 9, 1, "div", 24);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(44, "dialog", 13, 7);
        \u0275\u0275listener("click", function FilesComponent_Template_dialog_click_44_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeRenameDialog());
        });
        \u0275\u0275elementStart(46, "div", 25);
        \u0275\u0275listener("click", function FilesComponent_Template_div_click_46_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(47, "h2");
        \u0275\u0275text(48, "Rename");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(49, "input", 26);
        \u0275\u0275listener("ngModelChange", function FilesComponent_Template_input_ngModelChange_49_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.selectedFileName.set($event));
        });
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(50, "div", 27)(51, "button", 28);
        \u0275\u0275listener("click", function FilesComponent_Template_button_click_51_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.renameFile());
        });
        \u0275\u0275text(52, "Rename");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(53, "button", 29);
        \u0275\u0275listener("click", function FilesComponent_Template_button_click_53_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeRenameDialog());
        });
        \u0275\u0275text(54, "Cancel");
        \u0275\u0275elementEnd()()()();
        \u0275\u0275elementStart(55, "dialog", 30, 8);
        \u0275\u0275listener("click", function FilesComponent_Template_dialog_click_55_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeDeleteFileDialog());
        });
        \u0275\u0275elementStart(57, "div", 31);
        \u0275\u0275listener("click", function FilesComponent_Template_div_click_57_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(58, "h3");
        \u0275\u0275text(59, "Confirm Delete");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(60, "code");
        \u0275\u0275text(61);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(62, "p");
        \u0275\u0275text(63, "Are you sure you want to delete this file?");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(64, "div", 27)(65, "button", 32);
        \u0275\u0275listener("click", function FilesComponent_Template_button_click_65_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.deleteFile());
        });
        \u0275\u0275text(66, "Confirm");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(67, "button", 29);
        \u0275\u0275listener("click", function FilesComponent_Template_button_click_67_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeDeleteFileDialog());
        });
        \u0275\u0275text(68, "Cancel");
        \u0275\u0275elementEnd()()()();
      }
      if (rf & 2) {
        \u0275\u0275advance(4);
        \u0275\u0275conditional(ctx.filesResource.isLoading() ? 4 : 5);
        \u0275\u0275advance(14);
        \u0275\u0275conditional(ctx.isVideoFile() ? 18 : 19);
        \u0275\u0275advance(16);
        \u0275\u0275conditional(ctx.textFileLoading() ? 34 : 35);
        \u0275\u0275advance(8);
        \u0275\u0275conditional(ctx.videoInfoLoading() ? 42 : 43);
        \u0275\u0275advance(7);
        \u0275\u0275property("ngModel", ctx.selectedFileName());
        \u0275\u0275advance(12);
        \u0275\u0275textInterpolate(ctx.selectedFileName());
      }
    }, dependencies: [DatePipe, FormsModule, DefaultValueAccessor, NgControlStatus, NgModel, LoadIndicatorComponent, NgTemplateOutlet], styles: ['\n\n[_nghost-%COMP%] {\n  display: contents;\n}\n.center[_ngcontent-%COMP%] {\n  margin: auto;\n}\n.text-center[_ngcontent-%COMP%] {\n  text-align: center;\n}\n.media-files-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n  margin: 1rem;\n}\n.media-files-container[_ngcontent-%COMP%]   .media-files[_ngcontent-%COMP%] {\n  width: 100%;\n  display: block;\n  border: 1px solid var(--color-outline);\n  border-radius: 4px;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface-variant);\n  overflow-y: auto;\n}\n.media-files-container[_ngcontent-%COMP%]   .files-title[_ngcontent-%COMP%] {\n  margin: 0;\n  margin-block: 0;\n}\n.files-header[_ngcontent-%COMP%] {\n  grid-row: 1;\n  display: grid;\n  grid-template-columns: auto 6fr 1fr 2fr;\n  gap: 0.5rem;\n  align-items: center;\n  text-align: center;\n  padding: 1rem;\n  border: none;\n  outline: none;\n  transition: 0.4s;\n  border-top: 1px solid var(--color-outline);\n  position: relative;\n  font-size: 0.75rem;\n}\n@media (max-width: 765px) {\n  .files-header[_ngcontent-%COMP%] {\n    grid-template-columns: auto auto auto;\n    grid-template-rows: 1fr auto;\n  }\n}\n.files-header[_ngcontent-%COMP%]::before {\n  content: "";\n  display: block;\n  position: absolute;\n  top: 50%;\n  left: -1rem;\n  width: 1rem;\n  height: 1px;\n  background-color: var(--color-outline);\n}\n.files-accordion[_ngcontent-%COMP%] {\n  width: 100%;\n  display: grid;\n  grid-template-rows: 1fr auto;\n  border-left: 1px solid var(--color-outline);\n  position: relative;\n}\n.files-accordion[_ngcontent-%COMP%]   .parent[_ngcontent-%COMP%] {\n  cursor: pointer;\n}\n.files-accordion[_ngcontent-%COMP%]   .child[_ngcontent-%COMP%] {\n  grid-row: 2;\n  padding: 0 0 0 1rem;\n  position: relative;\n  cursor: pointer;\n}\n.child[_ngcontent-%COMP%]   .files-accordion[_ngcontent-%COMP%]:last-child {\n  border-bottom: 1px solid var(--color-outline);\n  margin-bottom: 1rem;\n}\n.files-header[_ngcontent-%COMP%]   .files-icon[_ngcontent-%COMP%] {\n  display: flex;\n  align-items: center;\n  justify-content: center;\n}\n@media (max-width: 765px) {\n  .files-header[_ngcontent-%COMP%]   .files-icon[_ngcontent-%COMP%] {\n    grid-row: 1/span 2;\n    grid-column: 1;\n    justify-self: center;\n  }\n}\n.files-header[_ngcontent-%COMP%]   .files-name[_ngcontent-%COMP%] {\n  font-size: 1rem;\n  text-align: left;\n  display: flex;\n  align-items: center;\n  gap: 0.25rem;\n}\n@media (max-width: 765px) {\n  .files-header[_ngcontent-%COMP%]   .files-name[_ngcontent-%COMP%] {\n    grid-row: 1;\n    grid-column: 2/span 2;\n    justify-self: start;\n  }\n}\n.files-header[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  width: 1.5rem;\n  height: 1.5rem;\n  fill: var(--color-on-surface);\n}\n@media (max-width: 765px) {\n  .files-header[_ngcontent-%COMP%]   .files-size[_ngcontent-%COMP%] {\n    grid-row: 2;\n    grid-column: 2;\n    justify-self: start;\n    margin-left: 0.25rem;\n  }\n  .files-header[_ngcontent-%COMP%]   .files-modified[_ngcontent-%COMP%] {\n    grid-row: 2;\n    grid-column: 3;\n    justify-self: end;\n  }\n}\ndialog[_ngcontent-%COMP%]   app-load-indicator[_ngcontent-%COMP%] {\n  margin: 4rem;\n}\n.dialog-content[_ngcontent-%COMP%] {\n  margin: 1rem;\n  position: relative;\n}\n.dialog-header[_ngcontent-%COMP%] {\n  position: relative;\n}\n.dialog-content[_ngcontent-%COMP%]   .close[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 0;\n  right: 0;\n  cursor: pointer;\n  border-radius: 50%;\n}\n.dialog-content[_ngcontent-%COMP%]   .close[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  height: 2rem;\n  width: 2rem;\n  fill: var(--color-on-surface);\n  padding: 0;\n}\n.dialog-options[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  padding: 1rem;\n}\n.icon-link[_ngcontent-%COMP%] {\n  display: flex;\n  align-items: center;\n  text-decoration: none;\n  transition: all 0.4s;\n  cursor: pointer;\n  padding: 1rem 3rem 1rem 0;\n  border-bottom: 1px solid var(--color-outline);\n  font-size: 1.25rem;\n}\n.icon-link[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n  height: 1.5rem;\n}\n.icon-link[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  width: 1.5rem;\n  height: 1.5rem;\n  fill: var(--color-on-surface);\n  padding: 0;\n  margin: 0 0.5rem;\n}\n.danger-option[_ngcontent-%COMP%] {\n  color: var(--color-error);\n}\n.danger-option[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  fill: var(--color-error);\n}\n.rename-dialog[_ngcontent-%COMP%], \n.delete-dialog[_ngcontent-%COMP%], \n.text-dialog[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  justify-content: center;\n  align-items: center;\n  gap: 1.5rem;\n  margin: 1.5rem;\n  max-width: 75vw;\n  max-height: 75vh;\n}\n@media (width < 765px) {\n  .rename-dialog[_ngcontent-%COMP%], \n   .delete-dialog[_ngcontent-%COMP%], \n   .text-dialog[_ngcontent-%COMP%] {\n    max-width: 90vw;\n    margin: 1rem;\n  }\n}\n.delete-dialog[_ngcontent-%COMP%] {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 0 1rem 1rem;\n  margin: 0;\n  gap: 1rem;\n}\n#deleteFileDialog[_ngcontent-%COMP%]::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.text-content[_ngcontent-%COMP%] {\n  max-width: 75vw;\n  max-height: 70vh;\n  overflow-y: auto;\n  border: 1px solid var(--color-outline);\n  border-radius: 1rem;\n  margin: 0.25rem;\n}\n.text-content[_ngcontent-%COMP%]   pre[_ngcontent-%COMP%] {\n  padding: 1rem;\n  white-space: pre-wrap;\n  word-wrap: break-word;\n  text-align: start;\n  counter-reset: listing;\n  line-height: 0;\n  --indent: 2rem;\n  --lineHeight: 2;\n}\n.text-content[_ngcontent-%COMP%]   pre[_ngcontent-%COMP%]   code[_ngcontent-%COMP%] {\n  counter-increment: listing;\n  display: block;\n  padding: 0 0 0 var(--indent);\n  text-indent: calc(-1 * var(--indent));\n  margin: 0;\n  line-height: var(--lineHeight);\n}\n.text-content[_ngcontent-%COMP%]   pre[_ngcontent-%COMP%]   code[_ngcontent-%COMP%]::before {\n  content: counter(listing) ". ";\n  display: inline-block;\n  width: var(--indent);\n  padding-left: auto;\n  margin-left: auto;\n  text-align: right;\n  color: var(--color-outline);\n}\n@media (width < 765px) {\n  .text-content[_ngcontent-%COMP%]   pre[_ngcontent-%COMP%] {\n    padding: 0.5rem;\n    --indentSm: 1.5rem;\n    --lineHeightSm: 1.25;\n  }\n  .text-content[_ngcontent-%COMP%]   pre[_ngcontent-%COMP%]   code[_ngcontent-%COMP%] {\n    padding: 0 0 0 var(--indentSm);\n    text-indent: calc(-1 * var(--indentSm));\n    line-height: var(--lineHeightSm);\n  }\n  .text-content[_ngcontent-%COMP%]   pre[_ngcontent-%COMP%]   code[_ngcontent-%COMP%]::before {\n    width: var(--indentSm);\n  }\n}\n.buttons-row[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  justify-content: space-around;\n  gap: 1rem;\n  width: 70%;\n}\n.rename-input[_ngcontent-%COMP%] {\n  field-sizing: content;\n  min-width: 50vw;\n  max-width: 75vw;\n  padding: 1rem;\n  border: 1px solid var(--color-outline);\n  border-radius: 1rem;\n  font-size: 1.2rem;\n}\n@media (width < 765px) {\n  .rename-input[_ngcontent-%COMP%] {\n    max-width: 90vw;\n  }\n}\n.info-dialog[_ngcontent-%COMP%], \n.info-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n  margin: 1.5rem;\n  max-width: 75vw;\n  align-items: center;\n  max-height: 75vh;\n}\n@media (width < 765px) {\n  .info-dialog[_ngcontent-%COMP%], \n   .info-container[_ngcontent-%COMP%] {\n    max-width: 90vw;\n  }\n}\n.info-container[_ngcontent-%COMP%] {\n  max-height: 65vh;\n  overflow-y: auto;\n}\nsection[_ngcontent-%COMP%] {\n  width: 100%;\n}\n.info-content[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  margin: 1rem 0.5rem;\n  gap: 1rem;\n}\n@media (width < 765px) {\n  .info-content[_ngcontent-%COMP%] {\n    flex-direction: column;\n    align-items: flex-start;\n    gap: 0.25rem;\n  }\n}\n.info-content[_ngcontent-%COMP%]   label[_ngcontent-%COMP%], \n.info-content[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n  font-weight: bold;\n  text-align: left;\n  width: 30%;\n}\n@media (width < 765px) {\n  .info-content[_ngcontent-%COMP%]   label[_ngcontent-%COMP%], \n   .info-content[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n    width: 100%;\n    font-weight: unset;\n    font-style: italic;\n    font-size: small;\n  }\n}\n.info-content[_ngcontent-%COMP%]    > [_ngcontent-%COMP%]:nth-child(2) {\n  text-decoration: none;\n  text-align: left;\n  margin: 0;\n  padding: 0.25rem;\n}\n/*# sourceMappingURL=files.component.css.map */'] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(FilesComponent, [{
    type: Component,
    args: [{ selector: "media-files", imports: [DatePipe, FormsModule, LoadIndicatorComponent, NgTemplateOutlet], template: `<div class="media-files-container">
  <p class="text-md files-title">Files</p>
  <hr />
  @if (filesResource.isLoading()) {
    <app-load-indicator class="center" />
  } @else {
    <div class="media-files">
      @if (filesResource.error()) {
        <p class="text-sm text-center">Error: {{ filesError() }}</p>
        <!-- }
      @if (mediaFiles === undefined) {
        <p class="text-sm text-center">{{mediaFilesResponse}}</p> -->
      } @else {
        <!-- Header -->
        <div class="files-header sm-none text-sm">
          <div></div>
          <!-- Empty Col for Icons -->
          <div>Name</div>
          <div>Size</div>
          <div>Modified</div>
        </div>
        <!-- Content -->
        <ng-container *ngTemplateOutlet="folFileTemplate; context: {folderUntyped: filesResource.value()}"></ng-container>
      }
    </div>
  }
</div>

<ng-template let-folderUntyped="folderUntyped" #folFileTemplate>
  @let folder = asFolderInfo(folderUntyped);
  <div class="files-accordion">
    <div class="files-header" (click)="openFolderOrOptions(folder)" [class.parent]="folder.type == 'folder'">
      <div class="files-icon">
        @if (folder.type === 'folder') {
          <!-- Show Folder Icon -->
          @if (folder.isExpanded) {
            <!-- Folder Open Icon -->
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
              <path
                d="M146.67-160q-26.34 0-46.5-20.17Q80-200.33 80-226.67v-506.66q0-26.34 20.17-46.5Q120.33-800 146.67-800H414l66.67 66.67h332.66q26.34 0 46.5 20.16Q880-693 880-666.67H146.67v440l100-373.33H940L834.33-209.67q-6.66 24.67-24.5 37.17Q792-160 766.67-160h-620Z"
              />
            </svg>
          } @else {
            <!-- Folder Closed Icon -->
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
              <path
                d="M146.67-160q-27 0-46.84-20.17Q80-200.33 80-226.67v-506.66q0-26.34 19.83-46.5Q119.67-800 146.67-800H414l66.67 66.67h332.66q26.34 0 46.5 20.16Q880-693 880-666.67v440q0 26.34-20.17 46.5Q839.67-160 813.33-160H146.67Z"
              />
            </svg>
          }
        } @else {
          <!-- File Icon -->
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
            <path
              d="M319.33-246.67h321.34v-66.66H319.33v66.66Zm0-166.66h321.34V-480H319.33v66.67ZM226.67-80q-27 0-46.84-19.83Q160-119.67 160-146.67v-666.66q0-27 19.83-46.84Q199.67-880 226.67-880H574l226 226v507.33q0 27-19.83 46.84Q760.33-80 733.33-80H226.67Zm314-542.67h192.66L540.67-813.33v190.66Z"
            />
          </svg>
        }
      </div>
      <div class="files-name">{{ folder.name }}</div>
      <div class="files-size">{{ folder.size }}</div>
      <div class="files-modified">{{ folder.modified | date }}</div>
    </div>
    @if (folder.type === 'folder') {
      <div class="child">
        <!-- Child Folders -->
        @if (folder.isExpanded) {
          <!-- Recursive call for child folders -->
          @for (childFolder of folder.files; track childFolder) {
            <ng-container *ngTemplateOutlet="folFileTemplate; context: {folderUntyped: childFolder}"></ng-container>
          }
        }
      </div>
    }
  </div>
</ng-template>

<!-- Options Dialog -->
<dialog #optionsDialog (click)="closeOptionsDialog()">
  <div class="dialog-content" (click)="$event.stopPropagation()" #optionsDialogContent>
    <h2>Options</h2>
    <!-- <div class="dialog-header">
    </div> -->
    <i class="close" (click)="closeOptionsDialog()">
      <!-- Close Icon - Google Fonts -->
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
        <path d="m249-186-63-63 231-231-231-230 63-64 231 230 231-230 63 64-230 230 230 231-63 63-231-230-231 230Z" />
      </svg>
    </i>
    <div class="dialog-options">
      @if (isVideoFile()) {
        <div class="icon-link" (click)="closeOptionsDialog(); openVideoDialog()" title="Play Video">
          <span>
            <!-- Play Arrow Icon - Google Fonts -->
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
              <path d="M320-203v-560l440 280-440 280Zm60-280Zm0 171 269-171-269-171v342Z" />
            </svg>
          </span>
          <span>Play Video</span>
        </div>
        <div class="icon-link" (click)="closeOptionsDialog(); openVideoInfoDialog()" title="Video Info">
          <span>
            <!-- Info Icon - Google Fonts -->
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
              <path
                d="M447-272h73v-248h-73v248Zm32.89-330Q496-602 507-612.59q11-10.58 11-26.23 0-17.63-10.87-28.4Q496.26-678 480.19-678q-17.19 0-27.69 10.6T442-639.68q0 16.28 10.89 26.98 10.9 10.7 27 10.7Zm-.08 538q-85.92 0-161.52-33.02-75.61-33.02-131.93-89.34-56.32-56.32-89.34-132.13T64-480.5q0-86.09 33.08-161.81t89.68-132.31q56.61-56.59 132.06-88.99Q394.27-896 480.06-896q86.15 0 162.17 32.39 76.02 32.4 132.4 89Q831-718 863.5-641.96 896-565.92 896-479.72q0 86.19-32.39 161.29-32.4 75.11-88.99 131.51Q718.03-130.53 642-97.26 565.98-64 479.81-64Zm.69-73q142.01 0 242.26-100.74Q823-338.49 823-480.5T722.94-722.76Q622.89-823 480-823q-141.51 0-242.26 100.06Q137-622.89 137-480q0 141.51 100.74 242.26Q338.49-137 480.5-137Zm-.5-343Z"
              />
            </svg>
          </span>
          <span>Video Info</span>
        </div>
      } @else {
        @if (isTextFile()) {
          <div class="icon-link" (click)="closeOptionsDialog(); openTextDialog()" title="View Text">
            <span>
              <!-- Description Icon - Google Fonts -->
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
                <path
                  d="M321-250h318v-69H321v69Zm0-169h319v-68H321v68ZM229-59q-35.78 0-63.39-26.91Q138-112.83 138-150v-660q0-37.59 27.61-64.79Q193.22-902 229-902h364l230 228v524q0 37.17-27.91 64.09Q767.19-59 731-59H229Zm316-569v-182H229v660h502v-478H545ZM229-810v182-182 660-660Z"
                />
              </svg>
            </span>
            <span>View Text</span>
          </div>
        }
      }
      <div class="icon-link" title="Rename" (click)="openRenameDialog()">
        <span>
          <!-- Border Color Icon - Google Fonts -->
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
            <path
              d="M81-5v-138h798V-5H81Zm150-327h30l371-371-13.35-15.86L604-733 231-362v30Zm-68 69v-126l486-488q10-9 23.11-14.5 13.12-5.5 26-5.5 12.89 0 25.89 5.75T748-876l28 25q12 10 17 23.99 5 13.99 5 26.52 0 13.17-5.46 26.76Q787.09-760.14 777-751L288-263H163Zm563-538-27-27 27 27Zm-94 98-13.35-15.86L604-733l28 30Z"
            />
          </svg>
        </span>
        <span>Rename</span>
      </div>
      <div class="icon-link danger-option" title="Delete" (click)="openDeleteFileDialog()">
        <span>
          <!-- Delete Icon - Google Fonts -->
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
            <path
              d="M253-99q-38.21 0-65.11-26.6Q161-152.2 161-190v-552h-58v-91h228v-47h297v47h228v91h-58v552q0 37.18-27.21 64.09Q743.59-99 706-99H253Zm453-643H253v552h453v-552ZM357-268h74v-398h-74v398Zm173 0h75v-398h-75v398ZM253-742v552-552Z"
            />
          </svg>
        </span>
        <span>Delete</span>
      </div>
    </div>
  </div>
</dialog>

<!-- Text Dialog -->
<dialog #textDialog (click)="closeTextDialog()">
  @if (textFileLoading()) {
    <app-load-indicator class="center" />
  } @else {
    <div class="text-dialog" (click)="$event.stopPropagation()">
      <h2>{{ selectedFileName() }}</h2>
      <div class="text-content">
        <pre>
        @for (line of selectedFileText(); track $index) {
          <!-- <span class="line">{{line}}</span> -->
          <code>{{line}}</code>
        }
        <!-- <code>{{selectedFileText}}</code> -->
      </pre>
      </div>
      <div class="buttons-row">
        <button class="tertiary" (click)="closeTextDialog()">Close</button>
      </div>
    </div>
  }
</dialog>

<!-- PlayVideo Dialog -->
<dialog #videoDialog (click)="closeVideoDialog()">
  <div (click)="$event.stopPropagation()" #videoDialogContent>
    <!-- <video controls [autoplay]="true" [muted]="true" controlsList="nodownload" oncanplay="this.play()" onloadedmetadata="this.muted = true" #videoElement>
      <source [src]="apiVideoUrl" type="video/mp4">
      Your browser does not support the video tag.
    </video> -->
  </div>
</dialog>

<!-- Video Info Dialog -->
<dialog #videoInfoDialog (click)="closeVideoInfoDialog()">
  @if (videoInfoLoading()) {
    <app-load-indicator class="center" />
  } @else {
    <div class="info-dialog">
      <h1>Video Properties</h1>
      <div class="info-container" (click)="$event.stopPropagation()">
        @if (videoInfo(); as info) {
          <section open>
            <h2>File Info</h2>
            <hr />
            <div class="info-content">
              <span>File Name</span>
              <code>{{ info.name }}</code>
            </div>
            <div class="info-content">
              <span>Format</span>
              <code>{{ info.format_name }}</code>
            </div>
            <div class="info-content">
              <span>Bitrate</span>
              <code>{{ info.bitrate }}</code>
            </div>
            <div class="info-content">
              <span>Duration</span>
              <code>{{ info.duration }}</code>
            </div>
            @if (audioTracks().length > 0) {
              <div class="info-content">
                <span>Audio Tracks</span>
                <code>{{ audioTracks() }}</code>
              </div>
            }
            @if (subtitleTracks().length > 0) {
              <div class="info-content">
                <span>Subtitles</span>
                <code>{{ subtitleTracks() }}</code>
              </div>
            }
          </section>
          @for (stream of info.streams; track stream.index) {
            <section>
              <h2>Track {{ stream.index }}: {{ stream.codec_type }}</h2>
              <hr />
              @if (stream.codec_name) {
                <div class="info-content">
                  <span>Codec</span>
                  <code>{{ stream.codec_name }}</code>
                </div>
              }
              @if (stream.language) {
                <div class="info-content">
                  <span>Language</span>
                  <code>{{ stream.language }}</code>
                </div>
              }
              @if (stream.coded_height && stream.coded_width) {
                <div class="info-content">
                  <span>Display Dimensions</span>
                  <code>{{ stream.coded_width }}x{{ stream.coded_height }}</code>
                </div>
              }
              @if (stream.audio_channels) {
                <div class="info-content">
                  <span>Audio Channels</span>
                  <code>{{ stream.audio_channels }}</code>
                </div>
              }
              @if (stream.sample_rate) {
                <div class="info-content">
                  <span>Audio Frequency</span>
                  <code>{{ stream.sample_rate }}</code>
                </div>
              }
            </section>
          }
        } @else {
          <h2>Video Info</h2>
          <hr />
          <code class="video-info"> Unable to fetch video info. </code>
        }
      </div>
      <div class="buttons-row">
        <button class="tertiary" (click)="closeVideoInfoDialog()">Close</button>
      </div>
    </div>
  }
</dialog>

<!-- Rename Dialog -->
<dialog #renameDialog (click)="closeRenameDialog()">
  <div class="rename-dialog" (click)="$event.stopPropagation()">
    <h2>Rename</h2>
    <input
      id="rename-file"
      class="rename-input"
      type="text"
      [ngModel]="selectedFileName()"
      (ngModelChange)="selectedFileName.set($event)"
      placeholder="New Name"
    />
    <div class="buttons-row">
      <button class="primary" (click)="renameFile()">Rename</button>
      <button class="tertiary" (click)="closeRenameDialog()">Cancel</button>
    </div>
  </div>
</dialog>

<!-- Delete Dialog -->
<dialog #deleteFileDialog id="deleteFileDialog" (click)="closeDeleteFileDialog()">
  <div class="delete-dialog" (click)="$event.stopPropagation()">
    <h3>Confirm Delete</h3>
    <code>{{ selectedFileName() }}</code>
    <p>Are you sure you want to delete this file?</p>
    <div class="buttons-row">
      <button class="danger" (click)="deleteFile()">Confirm</button>
      <button class="tertiary" (click)="closeDeleteFileDialog()">Cancel</button>
    </div>
  </div>
</dialog>
`, styles: ['/* src/app/media/media-details/files/files.component.scss */\n:host {\n  display: contents;\n}\n.center {\n  margin: auto;\n}\n.text-center {\n  text-align: center;\n}\n.media-files-container {\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n  margin: 1rem;\n}\n.media-files-container .media-files {\n  width: 100%;\n  display: block;\n  border: 1px solid var(--color-outline);\n  border-radius: 4px;\n  background-color: var(--color-surface-container-high);\n  color: var(--color-on-surface-variant);\n  overflow-y: auto;\n}\n.media-files-container .files-title {\n  margin: 0;\n  margin-block: 0;\n}\n.files-header {\n  grid-row: 1;\n  display: grid;\n  grid-template-columns: auto 6fr 1fr 2fr;\n  gap: 0.5rem;\n  align-items: center;\n  text-align: center;\n  padding: 1rem;\n  border: none;\n  outline: none;\n  transition: 0.4s;\n  border-top: 1px solid var(--color-outline);\n  position: relative;\n  font-size: 0.75rem;\n}\n@media (max-width: 765px) {\n  .files-header {\n    grid-template-columns: auto auto auto;\n    grid-template-rows: 1fr auto;\n  }\n}\n.files-header::before {\n  content: "";\n  display: block;\n  position: absolute;\n  top: 50%;\n  left: -1rem;\n  width: 1rem;\n  height: 1px;\n  background-color: var(--color-outline);\n}\n.files-accordion {\n  width: 100%;\n  display: grid;\n  grid-template-rows: 1fr auto;\n  border-left: 1px solid var(--color-outline);\n  position: relative;\n}\n.files-accordion .parent {\n  cursor: pointer;\n}\n.files-accordion .child {\n  grid-row: 2;\n  padding: 0 0 0 1rem;\n  position: relative;\n  cursor: pointer;\n}\n.child .files-accordion:last-child {\n  border-bottom: 1px solid var(--color-outline);\n  margin-bottom: 1rem;\n}\n.files-header .files-icon {\n  display: flex;\n  align-items: center;\n  justify-content: center;\n}\n@media (max-width: 765px) {\n  .files-header .files-icon {\n    grid-row: 1/span 2;\n    grid-column: 1;\n    justify-self: center;\n  }\n}\n.files-header .files-name {\n  font-size: 1rem;\n  text-align: left;\n  display: flex;\n  align-items: center;\n  gap: 0.25rem;\n}\n@media (max-width: 765px) {\n  .files-header .files-name {\n    grid-row: 1;\n    grid-column: 2/span 2;\n    justify-self: start;\n  }\n}\n.files-header svg {\n  width: 1.5rem;\n  height: 1.5rem;\n  fill: var(--color-on-surface);\n}\n@media (max-width: 765px) {\n  .files-header .files-size {\n    grid-row: 2;\n    grid-column: 2;\n    justify-self: start;\n    margin-left: 0.25rem;\n  }\n  .files-header .files-modified {\n    grid-row: 2;\n    grid-column: 3;\n    justify-self: end;\n  }\n}\ndialog app-load-indicator {\n  margin: 4rem;\n}\n.dialog-content {\n  margin: 1rem;\n  position: relative;\n}\n.dialog-header {\n  position: relative;\n}\n.dialog-content .close {\n  position: absolute;\n  top: 0;\n  right: 0;\n  cursor: pointer;\n  border-radius: 50%;\n}\n.dialog-content .close svg {\n  height: 2rem;\n  width: 2rem;\n  fill: var(--color-on-surface);\n  padding: 0;\n}\n.dialog-options {\n  display: flex;\n  flex-direction: column;\n  padding: 1rem;\n}\n.icon-link {\n  display: flex;\n  align-items: center;\n  text-decoration: none;\n  transition: all 0.4s;\n  cursor: pointer;\n  padding: 1rem 3rem 1rem 0;\n  border-bottom: 1px solid var(--color-outline);\n  font-size: 1.25rem;\n}\n.icon-link span {\n  height: 1.5rem;\n}\n.icon-link svg {\n  width: 1.5rem;\n  height: 1.5rem;\n  fill: var(--color-on-surface);\n  padding: 0;\n  margin: 0 0.5rem;\n}\n.danger-option {\n  color: var(--color-error);\n}\n.danger-option svg {\n  fill: var(--color-error);\n}\n.rename-dialog,\n.delete-dialog,\n.text-dialog {\n  display: flex;\n  flex-direction: column;\n  justify-content: center;\n  align-items: center;\n  gap: 1.5rem;\n  margin: 1.5rem;\n  max-width: 75vw;\n  max-height: 75vh;\n}\n@media (width < 765px) {\n  .rename-dialog,\n  .delete-dialog,\n  .text-dialog {\n    max-width: 90vw;\n    margin: 1rem;\n  }\n}\n.delete-dialog {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 0 1rem 1rem;\n  margin: 0;\n  gap: 1rem;\n}\n#deleteFileDialog::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.text-content {\n  max-width: 75vw;\n  max-height: 70vh;\n  overflow-y: auto;\n  border: 1px solid var(--color-outline);\n  border-radius: 1rem;\n  margin: 0.25rem;\n}\n.text-content pre {\n  padding: 1rem;\n  white-space: pre-wrap;\n  word-wrap: break-word;\n  text-align: start;\n  counter-reset: listing;\n  line-height: 0;\n  --indent: 2rem;\n  --lineHeight: 2;\n}\n.text-content pre code {\n  counter-increment: listing;\n  display: block;\n  padding: 0 0 0 var(--indent);\n  text-indent: calc(-1 * var(--indent));\n  margin: 0;\n  line-height: var(--lineHeight);\n}\n.text-content pre code::before {\n  content: counter(listing) ". ";\n  display: inline-block;\n  width: var(--indent);\n  padding-left: auto;\n  margin-left: auto;\n  text-align: right;\n  color: var(--color-outline);\n}\n@media (width < 765px) {\n  .text-content pre {\n    padding: 0.5rem;\n    --indentSm: 1.5rem;\n    --lineHeightSm: 1.25;\n  }\n  .text-content pre code {\n    padding: 0 0 0 var(--indentSm);\n    text-indent: calc(-1 * var(--indentSm));\n    line-height: var(--lineHeightSm);\n  }\n  .text-content pre code::before {\n    width: var(--indentSm);\n  }\n}\n.buttons-row {\n  display: flex;\n  flex-direction: row;\n  justify-content: space-around;\n  gap: 1rem;\n  width: 70%;\n}\n.rename-input {\n  field-sizing: content;\n  min-width: 50vw;\n  max-width: 75vw;\n  padding: 1rem;\n  border: 1px solid var(--color-outline);\n  border-radius: 1rem;\n  font-size: 1.2rem;\n}\n@media (width < 765px) {\n  .rename-input {\n    max-width: 90vw;\n  }\n}\n.info-dialog,\n.info-container {\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n  margin: 1.5rem;\n  max-width: 75vw;\n  align-items: center;\n  max-height: 75vh;\n}\n@media (width < 765px) {\n  .info-dialog,\n  .info-container {\n    max-width: 90vw;\n  }\n}\n.info-container {\n  max-height: 65vh;\n  overflow-y: auto;\n}\nsection {\n  width: 100%;\n}\n.info-content {\n  display: flex;\n  flex-direction: row;\n  align-items: center;\n  margin: 1rem 0.5rem;\n  gap: 1rem;\n}\n@media (width < 765px) {\n  .info-content {\n    flex-direction: column;\n    align-items: flex-start;\n    gap: 0.25rem;\n  }\n}\n.info-content label,\n.info-content span {\n  font-weight: bold;\n  text-align: left;\n  width: 30%;\n}\n@media (width < 765px) {\n  .info-content label,\n  .info-content span {\n    width: 100%;\n    font-weight: unset;\n    font-style: italic;\n    font-size: small;\n  }\n}\n.info-content > :nth-child(2) {\n  text-decoration: none;\n  text-align: left;\n  margin: 0;\n  padding: 0.25rem;\n}\n/*# sourceMappingURL=files.component.css.map */\n'] }]
  }], null, { optionsDialog: [{
    type: ViewChild,
    args: ["optionsDialog"]
  }], textDialog: [{
    type: ViewChild,
    args: ["textDialog"]
  }], videoDialog: [{
    type: ViewChild,
    args: ["videoDialog"]
  }], videoDialogContent: [{
    type: ViewChild,
    args: ["videoDialogContent"]
  }], videoInfoDialog: [{
    type: ViewChild,
    args: ["videoInfoDialog"]
  }], renameDialog: [{
    type: ViewChild,
    args: ["renameDialog"]
  }], deleteFileDialog: [{
    type: ViewChild,
    args: ["deleteFileDialog"]
  }] });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(FilesComponent, { className: "FilesComponent", filePath: "src/app/media/media-details/files/files.component.ts", lineNumber: 23 });
})();

// src/app/media/media-details/media-details.component.ts
var _c02 = ["deleteDialog"];
function MediaDetailsComponent_app_load_indicator_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 10);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_div_6__svg_svg_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 47);
    \u0275\u0275element(1, "path", 48);
    \u0275\u0275elementEnd();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_div_6_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 45);
    \u0275\u0275template(1, MediaDetailsComponent_ng_template_2_div_0_div_6__svg_svg_1_Template, 2, 0, "svg", 46);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(3);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx_r2.media.trailer_exists);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_0_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 51);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 52);
    \u0275\u0275element(2, "path", 53);
    \u0275\u0275elementEnd()();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_1_span_1__svg_svg_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(0, "svg", 57);
    \u0275\u0275element(1, "path", 58);
    \u0275\u0275elementEnd();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_1_span_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "span");
    \u0275\u0275template(1, MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_1_span_1__svg_svg_1_Template, 2, 0, "svg", 56);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(5);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx_r2.media.monitor);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_1_span_2_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "span");
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 59);
    \u0275\u0275element(2, "path", 60);
    \u0275\u0275elementEnd()();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_1_Template(rf, ctx) {
  if (rf & 1) {
    const _r4 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 54);
    \u0275\u0275listener("click", function MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_1_Template_div_click_0_listener() {
      \u0275\u0275restoreView(_r4);
      const ctx_r2 = \u0275\u0275nextContext(4);
      ctx_r2.isLoadingMonitor = true;
      return \u0275\u0275resetView(ctx_r2.monitorSeries());
    });
    \u0275\u0275template(1, MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_1_span_1_Template, 2, 1, "span", 55)(2, MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_1_span_2_Template, 3, 0, "span", 55);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(4);
    \u0275\u0275property("title", ctx_r2.media.monitor ? "Monitored, click to change" : "Not Monitored, click to change");
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx_r2.media.monitor);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", !ctx_r2.media.monitor);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_template_7_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_0_Template, 3, 0, "div", 49)(1, MediaDetailsComponent_ng_template_2_div_0_ng_template_7_div_1_Template, 3, 3, "div", 50);
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(3);
    \u0275\u0275property("ngIf", ctx_r2.isLoadingMonitor);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", !ctx_r2.isLoadingMonitor);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_a_19_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "a", 61);
    \u0275\u0275element(1, "img", 62);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(3);
    \u0275\u0275propertyInterpolate1("href", "https://www.imdb.com/title/", ctx_r2.media.imdb_id, "/", \u0275\u0275sanitizeUrl);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_container_20_a_1_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "a", 64);
    \u0275\u0275element(1, "img", 65);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(4);
    \u0275\u0275propertyInterpolate1("href", "https://www.themoviedb.org/movie/", ctx_r2.media.txdb_id, "", \u0275\u0275sanitizeUrl);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_container_20_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementContainerStart(0);
    \u0275\u0275template(1, MediaDetailsComponent_ng_template_2_div_0_ng_container_20_a_1_Template, 2, 2, "a", 63);
    \u0275\u0275elementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(3);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx_r2.media.txdb_id);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_template_21_a_0_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "a", 67);
    \u0275\u0275element(1, "img", 68);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(4);
    \u0275\u0275propertyInterpolate1("href", "https://www.thetvdb.com/?tab=series&id=", ctx_r2.media.txdb_id, "", \u0275\u0275sanitizeUrl);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_ng_template_21_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, MediaDetailsComponent_ng_template_2_div_0_ng_template_21_a_0_Template, 2, 2, "a", 66);
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(3);
    \u0275\u0275property("ngIf", ctx_r2.media.txdb_id);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_Conditional_66_Template(rf, ctx) {
  if (rf & 1) {
    const _r5 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "span", 69);
    \u0275\u0275listener("click", function MediaDetailsComponent_ng_template_2_div_0_Conditional_66_Template_span_click_0_listener() {
      \u0275\u0275restoreView(_r5);
      const ctx_r2 = \u0275\u0275nextContext(3);
      return \u0275\u0275resetView(ctx_r2.openProfileSelectDialog(true));
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 70);
    \u0275\u0275element(2, "path", 71);
    \u0275\u0275elementEnd()();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_Conditional_67_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "span", 39);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 72)(2, "circle", 73);
    \u0275\u0275element(3, "animate", 74);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(4, "circle", 75);
    \u0275\u0275element(5, "animate", 76);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(6, "circle", 77);
    \u0275\u0275element(7, "animate", 78);
    \u0275\u0275elementEnd()()();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_Conditional_68_button_0_Template(rf, ctx) {
  if (rf & 1) {
    const _r6 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "button", 80);
    \u0275\u0275listener("click", function MediaDetailsComponent_ng_template_2_div_0_Conditional_68_button_0_Template_button_click_0_listener() {
      \u0275\u0275restoreView(_r6);
      const ctx_r2 = \u0275\u0275nextContext(4);
      return \u0275\u0275resetView(ctx_r2.saveYtId());
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 70);
    \u0275\u0275element(2, "path", 81);
    \u0275\u0275elementEnd()();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_Conditional_68_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, MediaDetailsComponent_ng_template_2_div_0_Conditional_68_button_0_Template, 3, 0, "button", 79);
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(3);
    \u0275\u0275property("ngIf", ctx_r2.trailer_url != ctx_r2.media.youtube_trailer_id);
  }
}
function MediaDetailsComponent_ng_template_2_div_0_p_69_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "p", 82);
    \u0275\u0275text(1, " Click Download to download trailer from updated link! ");
    \u0275\u0275elementEnd();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_button_71_Template(rf, ctx) {
  if (rf & 1) {
    const _r7 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "button", 83);
    \u0275\u0275listener("click", function MediaDetailsComponent_ng_template_2_div_0_button_71_Template_button_click_0_listener() {
      \u0275\u0275restoreView(_r7);
      const ctx_r2 = \u0275\u0275nextContext(3);
      return \u0275\u0275resetView(ctx_r2.openTrailer());
    });
    \u0275\u0275text(1, "Watch");
    \u0275\u0275elementEnd();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_button_72_span_3_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "span", 86);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 52);
    \u0275\u0275element(2, "path", 53);
    \u0275\u0275elementEnd()();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_button_72_Template(rf, ctx) {
  if (rf & 1) {
    const _r8 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "button", 84);
    \u0275\u0275listener("click", function MediaDetailsComponent_ng_template_2_div_0_button_72_Template_button_click_0_listener() {
      \u0275\u0275restoreView(_r8);
      const ctx_r2 = \u0275\u0275nextContext(3);
      return \u0275\u0275resetView(ctx_r2.openProfileSelectDialog(false));
    });
    \u0275\u0275elementStart(1, "span");
    \u0275\u0275text(2, "Download ");
    \u0275\u0275elementEnd();
    \u0275\u0275template(3, MediaDetailsComponent_ng_template_2_div_0_button_72_span_3_Template, 3, 0, "span", 85);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext(3);
    \u0275\u0275property("disabled", ctx_r2.isLoadingDownload || ctx_r2.media.status == "downloading");
    \u0275\u0275advance(3);
    \u0275\u0275property("ngIf", ctx_r2.isLoadingDownload || ctx_r2.media.status == "downloading");
  }
}
function MediaDetailsComponent_ng_template_2_div_0_button_73_Template(rf, ctx) {
  if (rf & 1) {
    const _r9 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "button", 87);
    \u0275\u0275listener("click", function MediaDetailsComponent_ng_template_2_div_0_button_73_Template_button_click_0_listener() {
      \u0275\u0275restoreView(_r9);
      const ctx_r2 = \u0275\u0275nextContext(3);
      return \u0275\u0275resetView(ctx_r2.showDeleteDialog());
    });
    \u0275\u0275text(1, "Delete");
    \u0275\u0275elementEnd();
  }
}
function MediaDetailsComponent_ng_template_2_div_0_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "div", 13);
    \u0275\u0275element(1, "div", 14);
    \u0275\u0275elementStart(2, "div", 15);
    \u0275\u0275element(3, "img", 16);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(4, "div", 17)(5, "div", 18);
    \u0275\u0275template(6, MediaDetailsComponent_ng_template_2_div_0_div_6_Template, 2, 1, "div", 19)(7, MediaDetailsComponent_ng_template_2_div_0_ng_template_7_Template, 2, 2, "ng-template", null, 2, \u0275\u0275templateRefExtractor);
    \u0275\u0275elementStart(9, "span", 20);
    \u0275\u0275listener("click", function MediaDetailsComponent_ng_template_2_div_0_Template_span_click_9_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext(2);
      return \u0275\u0275resetView(ctx_r2.copyToClipboard(ctx_r2.media.title));
    });
    \u0275\u0275text(10);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(11, "div", 18)(12, "span", 21);
    \u0275\u0275text(13);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(14, "span", 21);
    \u0275\u0275pipe(15, "durationConvert");
    \u0275\u0275text(16);
    \u0275\u0275pipe(17, "durationConvert");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(18, "div", 18);
    \u0275\u0275template(19, MediaDetailsComponent_ng_template_2_div_0_a_19_Template, 2, 2, "a", 22)(20, MediaDetailsComponent_ng_template_2_div_0_ng_container_20_Template, 2, 1, "ng-container", 23)(21, MediaDetailsComponent_ng_template_2_div_0_ng_template_21_Template, 1, 1, "ng-template", null, 3, \u0275\u0275templateRefExtractor);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(23, "div", 24)(24, "span")(25, "div", 25)(26, "span", 26);
    \u0275\u0275text(27, "Path");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(28, "span", 27);
    \u0275\u0275listener("click", function MediaDetailsComponent_ng_template_2_div_0_Template_span_click_28_listener() {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext(2);
      return \u0275\u0275resetView(ctx_r2.copyToClipboard(ctx_r2.media.folder_path));
    });
    \u0275\u0275elementStart(29, "code");
    \u0275\u0275text(30);
    \u0275\u0275elementEnd()()()();
    \u0275\u0275elementStart(31, "span")(32, "div", 28)(33, "span", 26);
    \u0275\u0275text(34, "Status");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(35, "span", 29);
    \u0275\u0275text(36);
    \u0275\u0275pipe(37, "titlecase");
    \u0275\u0275elementStart(38, "span", 30)(39, "p");
    \u0275\u0275text(40);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(41, "p");
    \u0275\u0275text(42);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(43, "p");
    \u0275\u0275text(44);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(45, "p");
    \u0275\u0275text(46);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(47, "p");
    \u0275\u0275text(48);
    \u0275\u0275elementEnd()()()()()();
    \u0275\u0275elementStart(49, "div", 18)(50, "div", 31)(51, "span", 26);
    \u0275\u0275text(52, "Overview");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(53, "span", 32);
    \u0275\u0275text(54);
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(55, "div", 18)(56, "div", 28)(57, "span", 26);
    \u0275\u0275text(58, "Trailer");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(59, "div", 33)(60, "div", 34)(61, "span", 35);
    \u0275\u0275text(62, "https://www.youtube.com/watch?v=");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(63, "span", 36);
    \u0275\u0275text(64, "Youtube ID/URL:");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(65, "input", 37);
    \u0275\u0275twoWayListener("ngModelChange", function MediaDetailsComponent_ng_template_2_div_0_Template_input_ngModelChange_65_listener($event) {
      \u0275\u0275restoreView(_r2);
      const ctx_r2 = \u0275\u0275nextContext(2);
      \u0275\u0275twoWayBindingSet(ctx_r2.trailer_url, $event) || (ctx_r2.trailer_url = $event);
      return \u0275\u0275resetView($event);
    });
    \u0275\u0275elementEnd()();
    \u0275\u0275template(66, MediaDetailsComponent_ng_template_2_div_0_Conditional_66_Template, 3, 0, "span", 38)(67, MediaDetailsComponent_ng_template_2_div_0_Conditional_67_Template, 8, 0, "span", 39)(68, MediaDetailsComponent_ng_template_2_div_0_Conditional_68_Template, 1, 1, "button", 40);
    \u0275\u0275elementEnd();
    \u0275\u0275template(69, MediaDetailsComponent_ng_template_2_div_0_p_69_Template, 2, 0, "p", 41);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(70, "div", 18);
    \u0275\u0275template(71, MediaDetailsComponent_ng_template_2_div_0_button_71_Template, 2, 0, "button", 42)(72, MediaDetailsComponent_ng_template_2_div_0_button_72_Template, 4, 2, "button", 43)(73, MediaDetailsComponent_ng_template_2_div_0_button_73_Template, 2, 0, "button", 44);
    \u0275\u0275elementEnd()()();
  }
  if (rf & 2) {
    const noTrailer_r10 = \u0275\u0275reference(8);
    const showTVDBLogo_r11 = \u0275\u0275reference(22);
    const ctx_r2 = \u0275\u0275nextContext(2);
    \u0275\u0275advance();
    \u0275\u0275styleMap("background-image: url(" + ctx_r2.media.fanart_path + ");");
    \u0275\u0275advance();
    \u0275\u0275classProp("sm-none", !ctx_r2.media.poster_path);
    \u0275\u0275propertyInterpolate1("title", "", ctx_r2.media.title, " Poster");
    \u0275\u0275advance();
    \u0275\u0275propertyInterpolate("src", ctx_r2.media.poster_path || "assets/poster-lg.png", \u0275\u0275sanitizeUrl);
    \u0275\u0275propertyInterpolate("alt", ctx_r2.media.title);
    \u0275\u0275advance(3);
    \u0275\u0275property("ngIf", ctx_r2.media.trailer_exists)("ngIfElse", noTrailer_r10);
    \u0275\u0275advance(3);
    \u0275\u0275property("title", ctx_r2.media.title);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate1(" ", ctx_r2.media.title, " ");
    \u0275\u0275advance(2);
    \u0275\u0275property("title", ctx_r2.media.year);
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(ctx_r2.media.year);
    \u0275\u0275advance();
    \u0275\u0275property("title", \u0275\u0275pipeBind1(15, 36, ctx_r2.media.runtime));
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(\u0275\u0275pipeBind1(17, 38, ctx_r2.media.runtime));
    \u0275\u0275advance(3);
    \u0275\u0275property("ngIf", ctx_r2.media.imdb_id);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx_r2.media.is_movie)("ngIfElse", showTVDBLogo_r11);
    \u0275\u0275advance(5);
    \u0275\u0275property("title", ctx_r2.media.folder_path);
    \u0275\u0275advance(5);
    \u0275\u0275textInterpolate(ctx_r2.media.folder_path);
    \u0275\u0275advance(6);
    \u0275\u0275textInterpolate1("", \u0275\u0275pipeBind1(37, 40, ctx_r2.media.status), " ");
    \u0275\u0275advance(4);
    \u0275\u0275textInterpolate1("Monitored: ", ctx_r2.media.monitor, "");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1("Downloaded: ", ctx_r2.media.trailer_exists, "");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1("Added: ", ctx_r2.media.added_at.toLocaleString(), "");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1("Updated: ", ctx_r2.media.updated_at.toLocaleString(), "");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1("Downloaded: ", ctx_r2.media.downloaded_at.toLocaleString() || "", "");
    \u0275\u0275advance(6);
    \u0275\u0275textInterpolate(ctx_r2.media.overview);
    \u0275\u0275advance(11);
    \u0275\u0275twoWayProperty("ngModel", ctx_r2.trailer_url);
    \u0275\u0275advance();
    \u0275\u0275conditional(ctx_r2.media.youtube_trailer_id == "" && ctx_r2.trailer_url == "" && !ctx_r2.isLoadingDownload ? 66 : -1);
    \u0275\u0275advance();
    \u0275\u0275conditional(ctx_r2.isLoadingDownload ? 67 : -1);
    \u0275\u0275advance();
    \u0275\u0275conditional(ctx_r2.trailer_url != ctx_r2.media.youtube_trailer_id && !ctx_r2.isLoadingDownload ? 68 : -1);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx_r2.trailer_url != ctx_r2.media.youtube_trailer_id);
    \u0275\u0275advance(2);
    \u0275\u0275property("ngIf", ctx_r2.media.youtube_trailer_id);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", !ctx_r2.media.trailer_exists || ctx_r2.media.youtube_trailer_id != ctx_r2.trailer_url);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx_r2.media.trailer_exists);
  }
}
function MediaDetailsComponent_ng_template_2_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275template(0, MediaDetailsComponent_ng_template_2_div_0_Template, 74, 42, "div", 11);
    \u0275\u0275element(1, "media-files", 12);
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275property("ngIf", ctx_r2.media);
    \u0275\u0275advance();
    \u0275\u0275property("mediaId", ctx_r2.mediaId());
  }
}
var MediaDetailsComponent = class _MediaDetailsComponent {
  constructor() {
    this.mediaService = inject(MediaService);
    this.route = inject(ActivatedRoute);
    this.websocketService = inject(WebsocketService);
    this.viewContainerRef = inject(ViewContainerRef);
    this.mediaId = input(0, { transform: Number });
    this.media = void 0;
    this.isLoading = true;
    this.isLoadingMonitor = false;
    this.isLoadingDownload = false;
    this.trailer_url = "";
    this.mediaEffect = effect(() => {
      this.isLoading = true;
      this.getMediaData();
    });
  }
  /**
   * Copies the provided text to the clipboard. If the Clipboard API is not available,
   * it falls back to using the `execCommand` method for wider browser compatibility.
   *
   * @param textToCopy - The text string to be copied to the clipboard.
   * @returns A promise that resolves when the text has been successfully copied.
   *
   * @remarks
   * This method uses the modern Clipboard API if available, and falls back to the
   * `execCommand` method for older browsers. It also displays a toast notification
   * indicating the success or failure of the copy operation.
   *
   * @example
   * ```typescript
   * this.copyToClipboard("Hello, World!");
   * ```
   */
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
  ngOnInit() {
    this.isLoading = true;
    this.webSocketSubscription = this.websocketService.toastMessage.subscribe(() => {
      this.getMediaData();
    });
  }
  ngOnDestroy() {
    this.webSocketSubscription?.unsubscribe();
  }
  /**
   * Fetches media data based on the current media ID. \
   * Also sets the `trailer_url` property to the YouTube trailer ID of the media.
   * @returns {void}
   */
  getMediaData() {
    this.mediaService.getMediaByID(this.mediaId()).subscribe((media_res) => {
      this.media = media_res;
      this.trailer_url = media_res.youtube_trailer_id;
      this.isLoading = false;
    });
  }
  openProfileSelectDialog(isNextActionSearch) {
    const dialogRef = this.viewContainerRef.createComponent(ProfileSelectDialogComponent);
    dialogRef.instance.onSubmit.subscribe((profileId) => {
      if (isNextActionSearch) {
        this.searchTrailer(profileId);
      } else {
        this.downloadTrailer(profileId);
      }
      dialogRef.destroy();
    });
    dialogRef.instance.onClosed.subscribe(() => {
      dialogRef.destroy();
    });
  }
  /**
   * Downloads the trailer for the current media if the trailer ID has changed.
   *
   * This method checks if the new trailer URL contains the old trailer ID and if the trailer already exists.
   * If the trailer ID is the same and the trailer exists, it does not proceed with the download.
   * Otherwise, it sets the loading state to true and initiates the download process via the media service.
   *
   * @param {number} profileId - The ID of the profile to use for downloading the trailer.
   *
   * @returns {void}
   */
  downloadTrailer(profileId) {
    const old_id = this.media?.youtube_trailer_id?.toLowerCase() || "";
    const new_id = this.trailer_url.toLowerCase();
    if (new_id.includes(old_id) && this.media?.trailer_exists) {
      return;
    }
    this.isLoadingDownload = true;
    this.mediaService.downloadMediaTrailer(this.mediaId(), profileId, this.trailer_url).subscribe((res) => {
      console.log(res);
    });
  }
  /**
   * Toggles the monitoring status of the current media item.
   *
   * This method sets the `isLoadingMonitor` flag to true, then toggles the `monitor` status of the media item.
   * It calls the `monitorMedia` method of `mediaService` with the media ID and the new monitor status.
   * Once the subscription receives a response, it logs the response, updates the media's monitor status,
   * and sets the `isLoadingMonitor` flag to false.
   */
  monitorSeries() {
    this.isLoadingMonitor = true;
    const monitor = !this.media?.monitor;
    this.mediaService.monitorMedia(this.mediaId(), monitor).subscribe((res) => {
      console.log(res);
      this.media.monitor = monitor;
      this.isLoadingMonitor = false;
    });
  }
  searchTrailer(profileID) {
    this.websocketService.showToast("Searching for trailer...");
    this.isLoadingDownload = true;
    this.mediaService.searchMediaTrailer(this.mediaId(), profileID).pipe(catchError((error) => {
      console.error("Error searching trailer:", error.error.detail);
      this.websocketService.showToast(error.error.detail, "Error");
      this.isLoadingDownload = false;
      return of("");
    })).subscribe((res) => {
      if (res) {
        this.media.youtube_trailer_id = res;
        this.trailer_url = res;
      }
      this.isLoadingDownload = false;
    });
  }
  saveYtId() {
    this.websocketService.showToast("Saving youtube id...");
    this.isLoadingDownload = true;
    this.mediaService.saveMediaTrailer(this.mediaId(), this.trailer_url).pipe(catchError((error) => {
      console.error("Error searching trailer:", error.error.detail);
      this.websocketService.showToast(error.error.detail, "Error");
      this.isLoadingDownload = false;
      return of("");
    })).subscribe((res) => {
      if (res) {
        this.media.youtube_trailer_id = res;
        this.trailer_url = res;
      }
      this.isLoadingDownload = false;
    });
  }
  /**
   * Opens a new browser tab to play the YouTube trailer of the current media.
   * If the media does not have a YouTube trailer ID, the function returns without doing anything.
   *
   * @returns {void}
   */
  openTrailer() {
    if (!this.media?.youtube_trailer_id) {
      return;
    }
    window.open(`https://www.youtube.com/watch?v=${this.media.youtube_trailer_id}`, "_blank");
  }
  /**
   * Displays the delete dialog modal.
   * This method opens the delete dialog by calling the `showModal` method
   * on the native element of the delete dialog.
   *
   * @returns {void}
   */
  showDeleteDialog() {
    this.deleteDialog.nativeElement.showModal();
  }
  /**
   * Closes the delete dialog.
   *
   * This method is used to close the delete dialog by accessing the native element
   * and invoking the `close` method on it.
   */
  closeDeleteDialog() {
    this.deleteDialog.nativeElement.close();
  }
  /**
   * Handles the confirmation of trailer deletion.
   * Closes the delete dialog and calls the media service to delete the trailer.
   * Updates the media object to reflect that the trailer no longer exists.
   */
  onConfirmDelete() {
    this.closeDeleteDialog();
    this.mediaService.deleteMediaTrailer(this.mediaId()).subscribe((res) => {
      console.log(res);
      this.media.trailer_exists = false;
    });
  }
  static {
    this.\u0275fac = function MediaDetailsComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _MediaDetailsComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _MediaDetailsComponent, selectors: [["app-media-details"]], viewQuery: function MediaDetailsComponent_Query(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275viewQuery(_c02, 5);
      }
      if (rf & 2) {
        let _t;
        \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.deleteDialog = _t.first);
      }
    }, inputs: { mediaId: [1, "mediaId"] }, decls: 17, vars: 2, consts: [["mediaLoaded", ""], ["deleteDialog", ""], ["noTrailer", ""], ["showTVDBLogo", ""], [1, "media-details-container"], ["class", "center", 4, "ngIf", "ngIfElse"], [3, "click"], [1, "dialog-content", 3, "click"], ["tabindex", "2", 1, "danger", 3, "click"], ["tabindex", "1", 1, "secondary", 3, "click"], [1, "center"], ["class", "media-details-card", 4, "ngIf"], [3, "mediaId"], [1, "media-details-card"], [1, "media-fanart-overlay"], [1, "media-poster", 3, "title"], [3, "src", "alt"], [1, "media-details-col"], [1, "media-details-row"], ["class", "icon-link", "title", "Trailer Downloaded", 4, "ngIf", "ngIfElse"], [1, "text-lg", "title-text", "copy", 3, "click", "title"], [1, "text-md", 3, "title"], ["target", "_blank", "title", "IMDB Link", 3, "href", 4, "ngIf"], [4, "ngIf", "ngIfElse"], [1, "media-details-row", "extras"], [1, "labeled-text", 3, "title"], [1, "label"], [1, "text-sm", "copy", 3, "click"], [1, "labeled-text"], [1, "text-sm", "tooltip"], [1, "tooltiptext"], ["title", "Overview", 1, "labeled-text"], [1, "text-sm"], [1, "input-row"], [1, "labeled-input"], [1, "text-md", "sm-none"], [1, "text-md", "sm-show"], ["id", "youtube_trailer_id", "type", "text", "placeholder", "Youtube Video ID / URL", 3, "ngModelChange", "ngModel"], ["title", "Search Trailer", 1, "search-button", "icon-link"], ["title", "Searching for Trailer", 1, "loading-search", "icon-link"], ["id", "update_trailer_search_query", "tabindex", "24", 1, "primary", "icononly-button", "save-button", "success"], ["class", "text-sm info-text", 4, "ngIf"], ["class", "primary", "title", "Watch Trailer on Youtube", 3, "click", 4, "ngIf"], ["class", "primary", "title", "Download Trailer", 3, "disabled", "click", 4, "ngIf"], ["class", "danger", "title", "Delete Trailer", 3, "click", 4, "ngIf"], ["title", "Trailer Downloaded", 1, "icon-link"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "class", "downloaded-icon success", "aria-label", "Trailer Exists", 4, "ngIf"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Trailer Exists", 1, "downloaded-icon", "success"], ["d", "M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q65 0 123 19t107 53l-58 59q-38-24-81-37.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160q133 0 226.5-93.5T800-480q0-18-2-36t-6-35l65-65q11 32 17 66t6 70q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm-56-216L254-466l56-56 114 114 400-401 56 56-456 457Z"], ["class", "icon-link", "title", "Updating Monitor Status", 4, "ngIf"], ["class", "icon-link", 3, "title", "click", 4, "ngIf"], ["title", "Updating Monitor Status", 1, "icon-link"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", 1, "loading"], ["d", "M343-107q-120-42-194.5-146.5T74-490q0-29 4-57.5T91-604l-57 33-37-62 185-107 106 184-63 36-54-92q-13 30-18.5 60.5T147-490q0 113 65.5 200T381-171l-38 64Zm291-516v-73h107q-47-60-115.5-93.5T480-823q-66 0-123.5 24T255-734l-38-65q54-45 121-71t142-26q85 0 160.5 33T774-769v-67h73v213H634ZM598-1 413-107l107-184 62 37-54 94q123-17 204.5-110.5T814-489q0-19-2.5-37.5T805-563h74q4 18 6 36.5t2 36.5q0 142-87 251.5T578-96l56 33-36 62Z"], [1, "icon-link", 3, "click", "title"], [4, "ngIf"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "class", "monitored-icon", "aria-label", "Monitored", 4, "ngIf"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Monitored", 1, "monitored-icon"], ["d", "M713-600 600-713l56-57 57 57 141-142 57 57-198 198ZM200-120v-640q0-33 23.5-56.5T280-840h280q-20 30-30 57.5T520-720q0 72 45.5 127T680-524q23 3 40 3t40-3v404L480-240 200-120Z"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", "aria-label", "Not Monitored", 1, "not-monitored-icon"], ["d", "M200-120v-640q0-33 23.5-56.5T280-840h240v80H280v518l200-86 200 86v-278h80v400L480-240 200-120Zm80-640h240-240Zm400 160v-80h-80v-80h80v-80h80v80h80v80h-80v80h-80Z"], ["target", "_blank", "title", "IMDB Link", 3, "href"], ["src", "assets/IMDBlogo.png", "alt", "IMDB", 1, "xdb-icon"], ["target", "_blank", "title", "TMDB Link", 3, "href", 4, "ngIf"], ["target", "_blank", "title", "TMDB Link", 3, "href"], ["src", "assets/TMDBlogo.png", "alt", "TMDB", 1, "xdb-icon"], ["target", "_blank", "title", "TVDB Link", 3, "href", 4, "ngIf"], ["target", "_blank", "title", "TVDB Link", 3, "href"], ["src", "assets/TVDBlogo.png", "alt", "TVDB", 1, "xdb-icon"], ["title", "Search Trailer", 1, "search-button", "icon-link", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M801-108 537-372q-31 26-72.96 40-41.96 14-86.6 14-114.6 0-192.52-78Q107-474 107-586t78-190q78-78 190-78t190 78q78 78 78 190.15 0 43.85-13.5 84.35Q616-461 588-425l266 264-53 53ZM375.5-391q81.75 0 138.13-56.79Q570-504.58 570-586q0-81.42-56.29-138.21Q457.43-781 375.59-781q-82.67 0-139.13 56.79Q180-667.42 180-586q0 81.42 56.46 138.21Q292.92-391 375.5-391Z"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 0 200 200"], ["stroke-width", "14", "r", "15", "cx", "40", "cy", "65"], ["attributeName", "cy", "calcMode", "spline", "dur", "2", "values", "65;135;65;", "keySplines", ".5 0 .5 1;.5 0 .5 1", "repeatCount", "indefinite", "begin", "-.4"], ["stroke-width", "14", "r", "15", "cx", "100", "cy", "65"], ["attributeName", "cy", "calcMode", "spline", "dur", "2", "values", "65;135;65;", "keySplines", ".5 0 .5 1;.5 0 .5 1", "repeatCount", "indefinite", "begin", "-.2"], ["stroke-width", "14", "r", "15", "cx", "160", "cy", "65"], ["attributeName", "cy", "calcMode", "spline", "dur", "2", "values", "65;135;65;", "keySplines", ".5 0 .5 1;.5 0 .5 1", "repeatCount", "indefinite", "begin", "0"], ["class", "primary icononly-button save-button success", "id", "update_trailer_search_query", "tabindex", "24", 3, "click", 4, "ngIf"], ["id", "update_trailer_search_query", "tabindex", "24", 1, "primary", "icononly-button", "save-button", "success", 3, "click"], ["d", "M378-246 154-470l43-43 181 181 384-384 43 43-427 427Z"], [1, "text-sm", "info-text"], ["title", "Watch Trailer on Youtube", 1, "primary", 3, "click"], ["title", "Download Trailer", 1, "primary", 3, "click", "disabled"], ["class", "loading-icon", 4, "ngIf"], [1, "loading-icon"], ["title", "Delete Trailer", 1, "danger", 3, "click"]], template: function MediaDetailsComponent_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = \u0275\u0275getCurrentView();
        \u0275\u0275elementStart(0, "div", 4);
        \u0275\u0275template(1, MediaDetailsComponent_app_load_indicator_1_Template, 1, 0, "app-load-indicator", 5)(2, MediaDetailsComponent_ng_template_2_Template, 2, 2, "ng-template", null, 0, \u0275\u0275templateRefExtractor);
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(4, "dialog", 6, 1);
        \u0275\u0275listener("click", function MediaDetailsComponent_Template_dialog_click_4_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeDeleteDialog());
        });
        \u0275\u0275elementStart(6, "div", 7);
        \u0275\u0275listener("click", function MediaDetailsComponent_Template_div_click_6_listener($event) {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView($event.stopPropagation());
        });
        \u0275\u0275elementStart(7, "h2");
        \u0275\u0275text(8, "Delete Trailer");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(9, "p");
        \u0275\u0275text(10, "This will Delete the trailer file on disk for this Media");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(11, "p");
        \u0275\u0275text(12, "Are you sure?");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(13, "button", 8);
        \u0275\u0275listener("click", function MediaDetailsComponent_Template_button_click_13_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.onConfirmDelete());
        });
        \u0275\u0275text(14, "Delete");
        \u0275\u0275elementEnd();
        \u0275\u0275elementStart(15, "button", 9);
        \u0275\u0275listener("click", function MediaDetailsComponent_Template_button_click_15_listener() {
          \u0275\u0275restoreView(_r1);
          return \u0275\u0275resetView(ctx.closeDeleteDialog());
        });
        \u0275\u0275text(16, "Cancel");
        \u0275\u0275elementEnd()()();
      }
      if (rf & 2) {
        const mediaLoaded_r12 = \u0275\u0275reference(3);
        \u0275\u0275advance();
        \u0275\u0275property("ngIf", ctx.isLoading)("ngIfElse", mediaLoaded_r12);
      }
    }, dependencies: [NgIf, FormsModule, DefaultValueAccessor, NgControlStatus, NgModel, DurationConvertPipe, LoadIndicatorComponent, TitleCasePipe, FilesComponent], styles: ["\n\n.media-details-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  overflow-x: hidden;\n  overflow-y: auto;\n  margin: 1rem;\n  border: 1px solid var(--color-outline);\n  border-radius: 10px;\n}\n@media (width < 768px) {\n  .media-details-container[_ngcontent-%COMP%] {\n    margin: 0.5rem;\n  }\n}\n.text-center[_ngcontent-%COMP%] {\n  text-align: center;\n}\n.center[_ngcontent-%COMP%] {\n  margin: auto;\n}\n.media-details-card[_ngcontent-%COMP%] {\n  position: relative;\n  display: grid;\n  grid-template-columns: 1fr 3fr;\n  padding: 2rem;\n  gap: 2rem;\n}\n.media-fanart-overlay[_ngcontent-%COMP%] {\n  position: absolute;\n  top: 0;\n  right: 0;\n  bottom: 0;\n  left: 0;\n  z-index: 0;\n  height: 100%;\n  background-size: cover;\n  background-position: center;\n  opacity: 0.4;\n  border-radius: 10px;\n}\n.media-poster[_ngcontent-%COMP%] {\n  z-index: 2;\n  display: flex;\n  width: 100%;\n}\n.media-poster[_ngcontent-%COMP%]   img[_ngcontent-%COMP%] {\n  width: 100%;\n  max-width: 300px;\n  height: auto;\n  object-fit: contain;\n  margin-bottom: auto;\n}\n.media-details-col[_ngcontent-%COMP%] {\n  z-index: 2;\n  flex: 1;\n  display: flex;\n  flex-direction: column;\n}\n.media-details-row[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  margin: 0.3rem;\n  gap: 0.75rem;\n}\n.media-details-row[_ngcontent-%COMP%]   .title-text[_ngcontent-%COMP%] {\n  font-size: 2.5rem;\n  display: inline-block;\n  overflow: hidden;\n  max-width: 70%;\n}\n.icon-link[_ngcontent-%COMP%] {\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  text-decoration: none;\n  transition: all 0.4s;\n  cursor: pointer;\n}\n.icon-link[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  width: 40px;\n  fill: var(--color-primary);\n}\n.nav-icons[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  gap: 1rem;\n  margin-left: auto;\n  margin-right: 1rem;\n}\n.icon-link[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%]   .success[_ngcontent-%COMP%] {\n  fill: var(--color-success);\n}\n.xdb-icon[_ngcontent-%COMP%] {\n  width: 60px;\n  cursor: pointer;\n  border-radius: 4px;\n}\n.extras[_ngcontent-%COMP%] {\n  flex-wrap: wrap;\n}\n.labeled-text[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n}\n.labeled-text[_ngcontent-%COMP%]   .label[_ngcontent-%COMP%] {\n  font-size: 0.75rem;\n  opacity: 0.7;\n  margin-bottom: 0.1rem;\n}\n.labeled-input[_ngcontent-%COMP%] {\n  display: flex;\n  flex-wrap: nowrap !important;\n  align-items: stretch;\n  width: 100%;\n  border: 1px solid var(--color-outline);\n  border-radius: 6px;\n}\n.labeled-input[_ngcontent-%COMP%]   span[_ngcontent-%COMP%] {\n  display: block;\n  align-items: center;\n  padding: 0.75rem;\n  font-size: 1rem;\n  font-weight: 400;\n  color: var(--color-on-surface-variant);\n  text-align: center;\n  white-space: nowrap;\n  background-color: var(--color-surface-container-high);\n  border-right: 1px solid var(--color-outline);\n  border-top-left-radius: 6px;\n  border-bottom-left-radius: 6px;\n}\n.labeled-input[_ngcontent-%COMP%]   input[_ngcontent-%COMP%] {\n  flex: 1 1 auto;\n  width: 1%;\n  min-width: 100px;\n  display: block;\n  padding: 0.75rem;\n  font-size: 1rem;\n  font-weight: 400;\n  color: var(--color-on-surface);\n  border: none;\n  -webkit-appearance: none;\n  -moz-appearance: none;\n  appearance: none;\n  background-color: var(--color-surface-container);\n  border-top-right-radius: 6px;\n  border-bottom-right-radius: 6px;\n}\n.input-row[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: row;\n  gap: 0.5rem;\n}\n.loading-search[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%]   *[_ngcontent-%COMP%] {\n  fill: var(--color-primary);\n  stroke: var(--color-primary);\n}\n.save-button[_ngcontent-%COMP%] {\n  height: 40px;\n  width: 40px;\n}\n.info-text[_ngcontent-%COMP%] {\n  margin: 0.5rem;\n  padding: 0.5rem;\n  border-radius: 0.5rem;\n  background-color: var(--color-info);\n  color: var(--color-info-text);\n  text-align: center;\n}\n.loading-icon[_ngcontent-%COMP%] {\n  display: inline-flex;\n  justify-content: center;\n  align-items: center;\n}\n.loading-icon[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  width: 1rem;\n  height: 1rem;\n}\n.loading[_ngcontent-%COMP%] {\n  animation: _ngcontent-%COMP%_spin-animation 2s linear infinite;\n}\n@keyframes _ngcontent-%COMP%_spin-animation {\n  0% {\n    transform: rotate(0deg);\n  }\n  100% {\n    transform: rotate(360deg);\n  }\n}\n.dialog-content[_ngcontent-%COMP%] {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog[_ngcontent-%COMP%]::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content[_ngcontent-%COMP%]   button[_ngcontent-%COMP%] {\n  margin: 10px;\n}\n@media (max-width: 765px) {\n  .media-details-card[_ngcontent-%COMP%] {\n    display: flex;\n    flex-direction: column;\n    padding: 0;\n    padding-top: 2rem;\n    gap: 1rem;\n  }\n  .media-poster[_ngcontent-%COMP%]   img[_ngcontent-%COMP%] {\n    width: auto;\n    height: 30vh;\n    margin: 0 auto;\n  }\n  .media-details-col[_ngcontent-%COMP%] {\n    align-items: center;\n    margin: 1rem;\n    margin-top: 0;\n  }\n  .media-details-row[_ngcontent-%COMP%] {\n    display: flex;\n    flex-direction: row;\n    margin: 0.3rem;\n    gap: 0.75rem;\n  }\n  .media-details-row[_ngcontent-%COMP%]   .title-text[_ngcontent-%COMP%] {\n    max-width: 90%;\n  }\n}\n/*# sourceMappingURL=media-details.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(MediaDetailsComponent, [{
    type: Component,
    args: [{ selector: "app-media-details", imports: [NgIf, FormsModule, DurationConvertPipe, LoadIndicatorComponent, TitleCasePipe, FilesComponent], template: `<div class="media-details-container">
  <app-load-indicator *ngIf="isLoading; else mediaLoaded" class="center" />
  <ng-template #mediaLoaded>
    <div *ngIf="media" class="media-details-card">
      <div class="media-fanart-overlay" [style]="'background-image: url(' + media.fanart_path + ');'"></div>
      <div class="media-poster" [class.sm-none]="!media.poster_path" title="{{ media.title }} Poster">
        <img src="{{ media.poster_path || 'assets/poster-lg.png' }}" alt="{{ media.title }}" />
      </div>
      <div class="media-details-col">
        <div class="media-details-row">
          <div *ngIf="media.trailer_exists; else noTrailer" class="icon-link" title="Trailer Downloaded">
            <!-- Show Downloaded icon -->
            <svg
              *ngIf="media.trailer_exists"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 -960 960 960"
              class="downloaded-icon success"
              aria-label="Trailer Exists"
            >
              <path
                d="M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q65 0 123 19t107 53l-58 59q-38-24-81-37.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160q133 0 226.5-93.5T800-480q0-18-2-36t-6-35l65-65q11 32 17 66t6 70q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm-56-216L254-466l56-56 114 114 400-401 56 56-456 457Z"
              />
            </svg>
          </div>
          <ng-template #noTrailer>
            <div *ngIf="isLoadingMonitor" class="icon-link" title="Updating Monitor Status">
              <!-- Show loading icon on click -->
              <!-- Cycle icon - Google Fonts -->
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="loading">
                <path
                  d="M343-107q-120-42-194.5-146.5T74-490q0-29 4-57.5T91-604l-57 33-37-62 185-107 106 184-63 36-54-92q-13 30-18.5 60.5T147-490q0 113 65.5 200T381-171l-38 64Zm291-516v-73h107q-47-60-115.5-93.5T480-823q-66 0-123.5 24T255-734l-38-65q54-45 121-71t142-26q85 0 160.5 33T774-769v-67h73v213H634ZM598-1 413-107l107-184 62 37-54 94q123-17 204.5-110.5T814-489q0-19-2.5-37.5T805-563h74q4 18 6 36.5t2 36.5q0 142-87 251.5T578-96l56 33-36 62Z"
                />
              </svg>
            </div>
            <div
              *ngIf="!isLoadingMonitor"
              (click)="isLoadingMonitor = true; monitorSeries()"
              class="icon-link"
              [title]="media.monitor ? 'Monitored, click to change' : 'Not Monitored, click to change'"
            >
              <span *ngIf="media.monitor">
                <!-- Show Monitored icon -->
                <svg
                  *ngIf="media.monitor"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 -960 960 960"
                  class="monitored-icon"
                  aria-label="Monitored"
                >
                  <path
                    d="M713-600 600-713l56-57 57 57 141-142 57 57-198 198ZM200-120v-640q0-33 23.5-56.5T280-840h280q-20 30-30 57.5T520-720q0 72 45.5 127T680-524q23 3 40 3t40-3v404L480-240 200-120Z"
                  />
                </svg>
              </span>
              <span *ngIf="!media.monitor">
                <!-- Show Not Monitored icon -->
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="not-monitored-icon" aria-label="Not Monitored">
                  <path
                    d="M200-120v-640q0-33 23.5-56.5T280-840h240v80H280v518l200-86 200 86v-278h80v400L480-240 200-120Zm80-640h240-240Zm400 160v-80h-80v-80h80v-80h80v80h80v80h-80v80h-80Z"
                  />
                </svg>
              </span>
            </div>
            <!-- <ng-template #monitored>
              <div (click)="monitorSeries()" class="icon-link" title="Monitored, click to change">
                <span *ngIf="!isLoadingMonitor">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="not-monitored-icon" aria-label="Not Monitored">
                    <path d="M200-120v-640q0-33 23.5-56.5T280-840h240v80H280v518l200-86 200 86v-278h80v400L480-240 200-120Zm80-640h240-240Zm400 160v-80h-80v-80h80v-80h80v80h80v80h-80v80h-80Z"/>
                  </svg>
                </span>
                <span *ngIf="isLoadingMonitor">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="loading">
                    <path
                      d="M480.76-153.7q-132.19 0-228.01-95.33-95.82-95.34-95.82-227.06v-45.24l-77.36 77.37-40.68-40.91L191-637.22l152.35 152.35-40.92 40.91-77.36-77.37v44.76q0 104.61 75.3 179.56 75.3 74.94 180.39 74.94 29.48 0 55.96-5.23 26.48-5.24 49.71-15.72l48.5 48.26q-37.19 21.91-75.6 31.49-38.42 9.57-78.57 9.57Zm289.48-166.84L617.89-472.89l41.91-41.91 76.37 76.37v-40.77q0-104.37-75.42-179.43-75.42-75.07-180.27-75.07-29.72 0-56.2 5.74-26.48 5.74-49.71 14.22l-48.27-48.5q37.2-21.67 75.49-30.75 38.3-9.08 78.69-9.08 131.95 0 227.89 95.46 95.93 95.46 95.93 226.94v43.24l77.13-77.37 40.92 40.91-152.11 152.35Z" />
                  </svg>
                </span>
              </div>
            </ng-template>
            <ng-template #notMonitored>
              <div (click)="monitorSeries()" class="icon-link" title="Not Monitored, click to change">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="not-monitored-icon" aria-label="Not Monitored">
                  <path d="M200-120v-640q0-33 23.5-56.5T280-840h240v80H280v518l200-86 200 86v-278h80v400L480-240 200-120Zm80-640h240-240Zm400 160v-80h-80v-80h80v-80h80v80h80v80h-80v80h-80Z"/>
                </svg>
              </div>
            </ng-template> -->
          </ng-template>
          <span class="text-lg title-text copy" (click)="copyToClipboard(media.title)" [title]="media.title">
            {{ media.title }}
          </span>
          <!-- Add Previous and Next icons here -->
          <!-- <div class="nav-icons sm-none">
            <div class="icon-link" (click)="copyToClipboard('prev')">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
                <path d="m287-446.67 240 240L480-160 160-480l320-320 47 46.67-240 240h513v66.66H287Z"/>
              </svg>
            </div>
            <div class="icon-link" (click)="copyToClipboard('next')">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
                <path d="M673-446.67H160v-66.66h513l-240-240L480-800l320 320-320 320-47-46.67 240-240Z"/>
              </svg>
            </div>
          </div> -->
        </div>
        <div class="media-details-row">
          <span class="text-md" [title]="media.year">{{ media.year }}</span>
          <span class="text-md" [title]="media.runtime | durationConvert">{{ media.runtime | durationConvert }}</span>
        </div>
        <div class="media-details-row">
          <a *ngIf="media.imdb_id" href="https://www.imdb.com/title/{{ media.imdb_id }}/" target="_blank" title="IMDB Link">
            <img src="assets/IMDBlogo.png" alt="IMDB" class="xdb-icon" />
          </a>
          <ng-container *ngIf="media.is_movie; else showTVDBLogo">
            <a *ngIf="media.txdb_id" href="https://www.themoviedb.org/movie/{{ media.txdb_id }}" target="_blank" title="TMDB Link">
              <img src="assets/TMDBlogo.png" alt="TMDB" class="xdb-icon" />
            </a>
          </ng-container>
          <ng-template #showTVDBLogo>
            <a *ngIf="media.txdb_id" href="https://www.thetvdb.com/?tab=series&id={{ media.txdb_id }}" target="_blank" title="TVDB Link">
              <img src="assets/TVDBlogo.png" alt="TVDB" class="xdb-icon" />
            </a>
          </ng-template>
        </div>
        <div class="media-details-row extras">
          <span>
            <div class="labeled-text" [title]="media.folder_path">
              <span class="label">Path</span>
              <span class="text-sm copy" (click)="copyToClipboard(media.folder_path)">
                <code>{{ media.folder_path }}</code>
              </span>
            </div>
          </span>
          <span>
            <div class="labeled-text">
              <span class="label">Status</span>
              <span class="text-sm tooltip"
                >{{ media.status | titlecase }}
                <span class="tooltiptext">
                  <p>Monitored: {{ media.monitor }}</p>
                  <p>Downloaded: {{ media.trailer_exists }}</p>
                  <p>Added: {{ media.added_at.toLocaleString() }}</p>
                  <p>Updated: {{ media.updated_at.toLocaleString() }}</p>
                  <p>Downloaded: {{ media.downloaded_at.toLocaleString() || '' }}</p>
                </span>
              </span>
            </div>
          </span>
        </div>
        <div class="media-details-row">
          <div class="labeled-text" title="Overview">
            <span class="label">Overview</span>
            <span class="text-sm">{{ media.overview }}</span>
          </div>
        </div>
        <div class="media-details-row">
          <div class="labeled-text">
            <span class="label">Trailer</span>
            <div class="input-row">
              <div class="labeled-input">
                <span class="text-md sm-none">https://www.youtube.com/watch?v=</span>
                <span class="text-md sm-show">Youtube ID/URL:</span>
                <input id="youtube_trailer_id" type="text" [(ngModel)]="trailer_url" placeholder="Youtube Video ID / URL" />
              </div>
              @if (media.youtube_trailer_id == '' && trailer_url == '' && !isLoadingDownload) {
                <span class="search-button icon-link" title="Search Trailer" (click)="openProfileSelectDialog(true)">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
                    <path
                      d="M801-108 537-372q-31 26-72.96 40-41.96 14-86.6 14-114.6 0-192.52-78Q107-474 107-586t78-190q78-78 190-78t190 78q78 78 78 190.15 0 43.85-13.5 84.35Q616-461 588-425l266 264-53 53ZM375.5-391q81.75 0 138.13-56.79Q570-504.58 570-586q0-81.42-56.29-138.21Q457.43-781 375.59-781q-82.67 0-139.13 56.79Q180-667.42 180-586q0 81.42 56.46 138.21Q292.92-391 375.5-391Z"
                    />
                  </svg>
                </span>
              }
              @if (isLoadingDownload) {
                <!-- Show loading icon -->
                <span class="loading-search icon-link" title="Searching for Trailer">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
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
                </span>
              }
              @if (trailer_url != media.youtube_trailer_id && !isLoadingDownload) {
                <button
                  *ngIf="trailer_url != media.youtube_trailer_id"
                  class="primary icononly-button save-button success"
                  id="update_trailer_search_query"
                  tabindex="24"
                  (click)="saveYtId()"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
                    <path d="M378-246 154-470l43-43 181 181 384-384 43 43-427 427Z" />
                  </svg>
                </button>
              }
            </div>
            <p *ngIf="trailer_url != media.youtube_trailer_id" class="text-sm info-text">
              Click Download to download trailer from updated link!
            </p>
          </div>
        </div>
        <div class="media-details-row">
          <button *ngIf="media.youtube_trailer_id" (click)="openTrailer()" class="primary" title="Watch Trailer on Youtube">Watch</button>
          <button
            *ngIf="!media.trailer_exists || media.youtube_trailer_id != trailer_url"
            (click)="openProfileSelectDialog(false)"
            class="primary"
            title="Download Trailer"
            [disabled]="isLoadingDownload || media.status == 'downloading'"
          >
            <span>Download </span>
            <span *ngIf="isLoadingDownload || media.status == 'downloading'" class="loading-icon">
              <!-- Cycle icon - Google Fonts -->
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="loading">
                <path
                  d="M343-107q-120-42-194.5-146.5T74-490q0-29 4-57.5T91-604l-57 33-37-62 185-107 106 184-63 36-54-92q-13 30-18.5 60.5T147-490q0 113 65.5 200T381-171l-38 64Zm291-516v-73h107q-47-60-115.5-93.5T480-823q-66 0-123.5 24T255-734l-38-65q54-45 121-71t142-26q85 0 160.5 33T774-769v-67h73v213H634ZM598-1 413-107l107-184 62 37-54 94q123-17 204.5-110.5T814-489q0-19-2.5-37.5T805-563h74q4 18 6 36.5t2 36.5q0 142-87 251.5T578-96l56 33-36 62Z"
                />
              </svg>
            </span>
          </button>
          <!-- Change downloading / monitor button on click -->
          <button *ngIf="media.trailer_exists" (click)="showDeleteDialog()" class="danger" title="Delete Trailer">Delete</button>
        </div>
      </div>
    </div>
    <!-- Show Media Files -->
    <media-files [mediaId]="mediaId()"></media-files>
  </ng-template>
</div>

<dialog #deleteDialog (click)="closeDeleteDialog()">
  <div class="dialog-content" (click)="$event.stopPropagation()">
    <h2>Delete Trailer</h2>
    <p>This will Delete the trailer file on disk for this Media</p>
    <p>Are you sure?</p>
    <button class="danger" (click)="onConfirmDelete()" tabindex="2">Delete</button>
    <button class="secondary" (click)="closeDeleteDialog()" tabindex="1">Cancel</button>
  </div>
</dialog>
`, styles: ["/* src/app/media/media-details/media-details.component.scss */\n.media-details-container {\n  display: flex;\n  flex-direction: column;\n  overflow-x: hidden;\n  overflow-y: auto;\n  margin: 1rem;\n  border: 1px solid var(--color-outline);\n  border-radius: 10px;\n}\n@media (width < 768px) {\n  .media-details-container {\n    margin: 0.5rem;\n  }\n}\n.text-center {\n  text-align: center;\n}\n.center {\n  margin: auto;\n}\n.media-details-card {\n  position: relative;\n  display: grid;\n  grid-template-columns: 1fr 3fr;\n  padding: 2rem;\n  gap: 2rem;\n}\n.media-fanart-overlay {\n  position: absolute;\n  top: 0;\n  right: 0;\n  bottom: 0;\n  left: 0;\n  z-index: 0;\n  height: 100%;\n  background-size: cover;\n  background-position: center;\n  opacity: 0.4;\n  border-radius: 10px;\n}\n.media-poster {\n  z-index: 2;\n  display: flex;\n  width: 100%;\n}\n.media-poster img {\n  width: 100%;\n  max-width: 300px;\n  height: auto;\n  object-fit: contain;\n  margin-bottom: auto;\n}\n.media-details-col {\n  z-index: 2;\n  flex: 1;\n  display: flex;\n  flex-direction: column;\n}\n.media-details-row {\n  display: flex;\n  flex-direction: row;\n  margin: 0.3rem;\n  gap: 0.75rem;\n}\n.media-details-row .title-text {\n  font-size: 2.5rem;\n  display: inline-block;\n  overflow: hidden;\n  max-width: 70%;\n}\n.icon-link {\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  text-decoration: none;\n  transition: all 0.4s;\n  cursor: pointer;\n}\n.icon-link svg {\n  width: 40px;\n  fill: var(--color-primary);\n}\n.nav-icons {\n  display: flex;\n  flex-direction: row;\n  gap: 1rem;\n  margin-left: auto;\n  margin-right: 1rem;\n}\n.icon-link svg .success {\n  fill: var(--color-success);\n}\n.xdb-icon {\n  width: 60px;\n  cursor: pointer;\n  border-radius: 4px;\n}\n.extras {\n  flex-wrap: wrap;\n}\n.labeled-text {\n  display: flex;\n  flex-direction: column;\n}\n.labeled-text .label {\n  font-size: 0.75rem;\n  opacity: 0.7;\n  margin-bottom: 0.1rem;\n}\n.labeled-input {\n  display: flex;\n  flex-wrap: nowrap !important;\n  align-items: stretch;\n  width: 100%;\n  border: 1px solid var(--color-outline);\n  border-radius: 6px;\n}\n.labeled-input span {\n  display: block;\n  align-items: center;\n  padding: 0.75rem;\n  font-size: 1rem;\n  font-weight: 400;\n  color: var(--color-on-surface-variant);\n  text-align: center;\n  white-space: nowrap;\n  background-color: var(--color-surface-container-high);\n  border-right: 1px solid var(--color-outline);\n  border-top-left-radius: 6px;\n  border-bottom-left-radius: 6px;\n}\n.labeled-input input {\n  flex: 1 1 auto;\n  width: 1%;\n  min-width: 100px;\n  display: block;\n  padding: 0.75rem;\n  font-size: 1rem;\n  font-weight: 400;\n  color: var(--color-on-surface);\n  border: none;\n  -webkit-appearance: none;\n  -moz-appearance: none;\n  appearance: none;\n  background-color: var(--color-surface-container);\n  border-top-right-radius: 6px;\n  border-bottom-right-radius: 6px;\n}\n.input-row {\n  display: flex;\n  flex-direction: row;\n  gap: 0.5rem;\n}\n.loading-search svg * {\n  fill: var(--color-primary);\n  stroke: var(--color-primary);\n}\n.save-button {\n  height: 40px;\n  width: 40px;\n}\n.info-text {\n  margin: 0.5rem;\n  padding: 0.5rem;\n  border-radius: 0.5rem;\n  background-color: var(--color-info);\n  color: var(--color-info-text);\n  text-align: center;\n}\n.loading-icon {\n  display: inline-flex;\n  justify-content: center;\n  align-items: center;\n}\n.loading-icon svg {\n  width: 1rem;\n  height: 1rem;\n}\n.loading {\n  animation: spin-animation 2s linear infinite;\n}\n@keyframes spin-animation {\n  0% {\n    transform: rotate(0deg);\n  }\n  100% {\n    transform: rotate(360deg);\n  }\n}\n.dialog-content {\n  background-color: var(--color-on-error-container);\n  color: var(--color-on-error);\n  padding: 1rem;\n  text-align: center;\n}\ndialog::backdrop {\n  background-image:\n    linear-gradient(\n      0deg,\n      grey,\n      #690005);\n}\n.dialog-content button {\n  margin: 10px;\n}\n@media (max-width: 765px) {\n  .media-details-card {\n    display: flex;\n    flex-direction: column;\n    padding: 0;\n    padding-top: 2rem;\n    gap: 1rem;\n  }\n  .media-poster img {\n    width: auto;\n    height: 30vh;\n    margin: 0 auto;\n  }\n  .media-details-col {\n    align-items: center;\n    margin: 1rem;\n    margin-top: 0;\n  }\n  .media-details-row {\n    display: flex;\n    flex-direction: row;\n    margin: 0.3rem;\n    gap: 0.75rem;\n  }\n  .media-details-row .title-text {\n    max-width: 90%;\n  }\n}\n/*# sourceMappingURL=media-details.component.css.map */\n"] }]
  }], null, { deleteDialog: [{
    type: ViewChild,
    args: ["deleteDialog"]
  }] });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(MediaDetailsComponent, { className: "MediaDetailsComponent", filePath: "src/app/media/media-details/media-details.component.ts", lineNumber: 20 });
})();

// src/app/media/media-details/routes.ts
var routes_default = [{ path: "", loadComponent: () => MediaDetailsComponent }];
export {
  routes_default as default
};
//# sourceMappingURL=chunk-CTR4T5O6.js.map
