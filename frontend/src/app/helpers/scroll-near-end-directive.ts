import {Directive, ElementRef, EventEmitter, HostListener, inject, Input, OnInit, Output} from '@angular/core';

@Directive({
  selector: '[appScrollNearEnd]',
  standalone: true,
})
export class ScrollNearEndDirective implements OnInit {
  private readonly el = inject(ElementRef);

  @Output() nearEnd: EventEmitter<void> = new EventEmitter<void>();

  /**
   * threshold in PX when to emit before page end scroll
   */
  @Input() threshold = 200;

  private window!: Window;

  ngOnInit() {
    // save window object for type safety
    this.window = window;
    // console.log('Scroll near end directive initialized');
  }

  @HostListener('window:scroll', ['$event'])
  windowScrollEvent(event: any) {
    // height of whole window page
    const heightOfWholePage = this.window.document.documentElement.scrollHeight;

    // how big in pixels the element is
    const heightOfElement = this.el.nativeElement.scrollHeight;

    // currently scrolled Y position
    const currentScrolledY = this.window.scrollY;

    // height of opened window - shrinks if console is opened
    const innerHeight = this.window.innerHeight;

    const spaceOfElementAndPage = heightOfWholePage - heightOfElement;

    const scrollToBottom = heightOfElement - innerHeight - currentScrolledY + spaceOfElementAndPage;

    // console.log('windowScrollToBottom:', scrollToBottom);

    // console.log(
    //   currentScrolledY,
    //   innerHeight,
    //   heightOfWholePage,
    //   spaceOfElementAndPage
    // );

    if (scrollToBottom < this.threshold) {
      // console.log(
      //     '%c [WinScrollNearEndDirective]: emit',
      //     'color: #bada55; font-size: 20px'
      // );
      this.nearEnd.emit();
    }
  }
}
