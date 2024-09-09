import { DOCUMENT } from '@angular/common';
import {
    Directive,
    ElementRef,
    EventEmitter,
    HostListener,
    Inject,
    Input,
    OnInit,
    Output
} from '@angular/core';

@Directive({
    selector: '[appScrollNearEnd]',
    standalone: true,
})
export class ScrollNearEndDirective implements OnInit {
    @Output() nearEnd: EventEmitter<void> = new EventEmitter<void>();

    /**
     * threshold in PX when to emit before page end scroll
     */
    @Input() threshold = 200;

    private window!: Window;

    constructor(private el: ElementRef, @Inject(DOCUMENT) private document: Document) {
        console.log('Scroll near end directive initialized');
    }

    ngOnInit(): void {
        // save window object for type safety
        this.window = window;
        console.log('Scroll near end directive initialized');
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

        const scrollToBottom =
            heightOfElement - innerHeight - currentScrolledY + spaceOfElementAndPage;

        console.log('windowScrollToBottom:', scrollToBottom);

        // console.log(
        //   currentScrolledY,
        //   innerHeight,
        //   heightOfWholePage,
        //   spaceOfElementAndPage
        // );

        if (scrollToBottom < this.threshold) {
            console.log(
                '%c [WinScrollNearEndDirective]: emit',
                'color: #bada55; font-size: 20px'
            );
            this.nearEnd.emit();
        }
    }

    // @HostListener('window:scroll', ['$event'])
    // onElementScroll(event: any): void {
    //     const element = this.el.nativeElement;

    //     // Height of the element
    //     const heightOfElement = element.scrollHeight;

    //     // Currently scrolled Y position within the element
    //     const currentScrolledY = element.scrollTop;

    //     // Height of the visible part of the element
    //     const innerHeight = element.clientHeight;

    //     // Calculate the distance to the bottom
    //     const scrollToBottom = heightOfElement - innerHeight - currentScrolledY;

    //     console.log('scrollToBottom:', scrollToBottom);

    //     if (scrollToBottom < this.threshold) {
    //         console.log(
    //             '%c [ScrollNearEndDirective]: emit',
    //             'color: #bada55; font-size: 20px'
    //         );
    //         this.nearEnd.emit();
    //     }
    // }
}
